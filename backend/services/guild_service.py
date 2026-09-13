from db import repositories
from services.discord import guild_permissions_allow_management


DISCORD_CDN = "https://cdn.discordapp.com"


def _icon_url(guild: dict) -> str | None:
    icon = guild.get("icon")
    if not icon:
        return None
    return f"{DISCORD_CDN}/icons/{guild['id']}/{icon}.png"


async def resolve_manageable_guilds(pool, discord_guilds: list[dict]) -> list[dict]:
    """From the user's full Discord guild list, keep only the servers
    they're allowed to manage (owner, Administrator, or Manage Server),
    and flag whether the bot is actually installed there."""

    known_ids = await repositories.get_known_guild_ids(pool)

    manageable = []

    for guild in discord_guilds:
        if not guild_permissions_allow_management(guild):
            continue

        guild_id = int(guild["id"])

        manageable.append(
            {
                "id": str(guild_id),
                "name": guild["name"],
                "icon_url": _icon_url(guild),
                "member_count": guild.get("approximate_member_count"),
                "is_bot_present": guild_id in known_ids,
            }
        )

    return manageable


async def get_guild_detail(pool, guild_id: int, session_guild: dict) -> dict | None:
    """Merge the cached session snapshot (name/icon/member count) with a
    live settings snapshot from the database."""

    row = await repositories.get_guild(pool, guild_id)

    if row is None:
        return None

    return {
        "id": session_guild["id"],
        "name": session_guild["name"],
        "icon_url": session_guild["icon_url"],
        "member_count": session_guild.get("member_count"),
        "is_bot_present": True,
        "message_tracking_enabled": row["message_tracking_enabled"],
        "voice_tracking_enabled": row["voice_tracking_enabled"],
        "leveling_enabled": row["leveling_enabled"],
        "spam_enabled": row["spam_enabled"],
        "link_protection_enabled": row["link_protection_enabled"],
    }
