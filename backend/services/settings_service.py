from core.config import ENVIRONMENT
from services.discord import (BotIntegrationNotConfigured, BotInternalAPIError, ensure_guild_channel, ensure_guild_role, configure_verification)
from db import repositories
from utils.validators import parse_snowflake


_ID_FIELDS = {"level_up_channel_id", "announcement_channel_id", "verification_channel_id", "verification_role_id", "welcome_channel_id", "leave_channel_id"}


def _serialize_guild_row(row: dict) -> dict:
    """Convert a `guilds` row into JSON-safe output.

    Discord snowflakes exceed JavaScript's safe integer range, so every
    id field is stringified. Everything else (counters, toggles, actions)
    passes through unchanged.
    """

    out = dict(row)
    out["guild_id"] = str(out["guild_id"])

    for field in _ID_FIELDS:
        if out.get(field) is not None:
            out[field] = str(out[field])

    return out


async def get_guild_settings(pool, guild_id: int) -> dict | None:
    row = await repositories.get_guild(pool, guild_id)
    return _serialize_guild_row(row) if row else None


async def update_guild_settings(pool, guild_id: int, updates: dict) -> dict:
    """Validate and apply a settings snapshot atomically.

    Discord resources needed by the snapshot are created before the DB
    transaction and removed again if the DB write fails. This prevents a
    partially-applied dashboard Save from leaving mixed configuration.
    """
    updates = dict(updates)

    # Validate all values before touching Discord or PostgreSQL.
    for field in ("welcome_gif_url", "leave_gif_url", "level_up_gif_url"):
        if field in updates and updates[field]:
            value = str(updates[field]).strip()
            if not value.startswith(("https://", "http://")):
                raise ValueError(f"{field} must be an http(s) URL.")
            if ENVIRONMENT == "production" and not value.startswith("https://"):
                raise ValueError(f"{field} must use HTTPS in production.")
            updates[field] = value[:1000]

    # Validate through the same repository rules without writing yet.
    # The repository performs cross-field XP validation against the current row.
    current = await repositories.get_guild(pool, guild_id)
    if current is None:
        raise ValueError("Guild configuration does not exist.")
    for field, value in updates.items():
        if field not in repositories.GUILD_SETTINGS_ALLOWED:
            raise ValueError(f"Invalid guild setting: {field}")
        if field in repositories._ACTION_SETTINGS and value not in repositories.MODERATION_ACTIONS:
            raise ValueError(f"Invalid action: {value}")
        if field in repositories._NUMERIC_SETTINGS:
            if not isinstance(value, int) or isinstance(value, bool) or value < 1:
                raise ValueError(f"{field} must be a positive integer.")
    effective = dict(current)
    effective.update(updates)
    if effective["xp_min"] > effective["xp_max"]:
        raise ValueError("xp_min cannot be greater than xp_max.")

    created_channels = []
    created_roles = []
    verification_configured_this_pass = False
    try:
        channel_defaults = {}
        if effective.get("level_up_messages_enabled") and (not effective.get("level_up_channel_id") or updates.get("level_up_channel_id") == "__auto__"):
            channel_defaults["level_up_channel_id"] = "level-up"
        if effective.get("welcome_enabled") and (not effective.get("welcome_channel_id") or updates.get("welcome_channel_id") == "__auto__"):
            channel_defaults["welcome_channel_id"] = "welcome"
        if effective.get("leave_enabled") and (not effective.get("leave_channel_id") or updates.get("leave_channel_id") == "__auto__"):
            channel_defaults["leave_channel_id"] = "leave"
        if effective.get("verification_enabled") and (not effective.get("verification_channel_id") or updates.get("verification_channel_id") == "__auto__"):
            channel_defaults["verification_channel_id"] = "verification"
        if updates.get("announcement_channel_id") == "__auto__" or ("announcement_channel_id" in updates and not updates.get("announcement_channel_id")):
            channel_defaults["announcement_channel_id"] = "announcements"

        for field, name in channel_defaults.items():
            channel = await ensure_guild_channel(guild_id, name)
            if channel.get("created"):
                created_channels.append((channel["id"], channel.get("rollback_token")))
            updates[field] = channel["id"]
            effective[field] = channel["id"]

        if effective.get("verification_enabled"):
            role_changed = "verification_role_id" in updates
            if not effective.get("verification_role_id") or updates.get("verification_role_id") == "__auto__":
                role = await ensure_guild_role(guild_id, "Verified")
                if role.get("created"):
                    created_roles.append((role["id"], role.get("rollback_token")))
                updates["verification_role_id"] = role["id"]
                effective["verification_role_id"] = role["id"]
                role_changed = True

            if not effective.get("verification_channel_id"):
                raise ValueError("Verification channel could not be configured.")

            channel_changed = (
                "verification_channel_id" in updates
                or "verification_channel_id" in channel_defaults
            )
            verification_just_enabled = updates.get("verification_enabled") is True

            # Only touch Discord's verification setup (re-post the verify
            # message, reset the channel's permissions) when something
            # about it actually changed this save — otherwise every save
            # of an unrelated setting (e.g. toggling spam protection)
            # would redo it for no reason.
            if verification_just_enabled or channel_changed or role_changed:
                await configure_verification(
                    guild_id,
                    effective["verification_channel_id"],
                    effective["verification_role_id"],
                )
                verification_configured_this_pass = True

        # Apply the entire DB snapshot in one transaction.
        async with pool.acquire() as conn:
            async with conn.transaction():
                for field, value in updates.items():
                    if field in _ID_FIELDS and value is not None:
                        value = parse_snowflake(value)
                    await repositories.update_guild_setting(conn, guild_id, field, value, validate_cross_field=False)

        return await get_guild_settings(pool, guild_id)
    except Exception as exc:
        # Best-effort rollback of Discord resources created solely by this Save.
        # The bot endpoint only deletes IDs explicitly supplied by this service.
        from services.discord import delete_guild_channel, delete_guild_role
        for channel_id, rollback_token in reversed(created_channels):
            try:
                if rollback_token:
                    await delete_guild_channel(guild_id, channel_id, rollback_token)
            except Exception:
                pass
        for role_id, rollback_token in reversed(created_roles):
            try:
                if rollback_token:
                    await delete_guild_role(guild_id, role_id, rollback_token)
            except Exception:
                pass

        # configure_verification() has no rollback of its own (it edits
        # channel permissions and posts/edits a persistent message rather
        # than creating a deletable resource), so if it succeeded but the
        # DB write below it failed, Discord is left correctly configured
        # while the database still shows the old state. That resolves
        # itself on the next successful save (ensure_guild_* are
        # idempotent by name), but give a clear message instead of a
        # generic one in the meantime.
        if verification_configured_this_pass and not isinstance(exc, ValueError):
            raise RuntimeError(
                "Verification was updated in Discord, but saving these "
                "settings failed. Please try saving again."
            ) from exc

        raise

