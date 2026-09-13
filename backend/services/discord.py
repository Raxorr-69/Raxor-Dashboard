import httpx

from core.config import (
    BOT_INTERNAL_API_URL,
    DASHBOARD_INTERNAL_KEY,
    DISCORD_CLIENT_ID,
    DISCORD_CLIENT_SECRET,
    DISCORD_REDIRECT_URI,
)
from core.constants import (
    DISCORD_API_BASE_URL,
    DISCORD_OAUTH_TOKEN_URL,
    PERMISSION_ADMINISTRATOR,
    PERMISSION_MANAGE_GUILD,
)


class DiscordOAuthError(Exception):
    """Raised when the Discord OAuth2 exchange or API call fails."""


class BotInternalAPIError(Exception):
    """Raised when a call to Raxor's own internal dashboard API
    (web/internal.py in the bot's codebase) fails."""


class BotIntegrationNotConfigured(BotInternalAPIError):
    """Raised when a bot-integration feature is used but
    BOT_INTERNAL_API_URL / DASHBOARD_INTERNAL_KEY aren't set. Callers
    should treat this as "feature unavailable", not as a hard error."""


async def exchange_code_for_token(code: str) -> dict:
    """Exchange an OAuth2 authorization code for an access token."""

    data = {
        "client_id": DISCORD_CLIENT_ID,
        "client_secret": DISCORD_CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": DISCORD_REDIRECT_URI,
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            DISCORD_OAUTH_TOKEN_URL,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

    if response.status_code != 200:
        raise DiscordOAuthError(
            f"Discord token exchange failed: {response.status_code} {response.text}"
        )

    return response.json()


async def refresh_access_token(refresh_token: str) -> dict:
    """Exchange a refresh token for a new Discord access token, used to
    keep re-verifying a session's guild permissions live without forcing
    the user back through the consent screen every
    GUILD_CACHE_TTL_SECONDS (see api/dependencies.py)."""

    data = {
        "client_id": DISCORD_CLIENT_ID,
        "client_secret": DISCORD_CLIENT_SECRET,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            DISCORD_OAUTH_TOKEN_URL,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

    if response.status_code != 200:
        raise DiscordOAuthError(
            f"Discord token refresh failed: {response.status_code} {response.text}"
        )

    return response.json()


async def fetch_current_user(access_token: str) -> dict:
    """Fetch the logged-in Discord user's profile."""

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{DISCORD_API_BASE_URL}/users/@me",
            headers={"Authorization": f"Bearer {access_token}"},
        )

    if response.status_code != 200:
        raise DiscordOAuthError(
            f"Failed to fetch Discord user: {response.status_code} {response.text}"
        )

    return response.json()


async def fetch_current_user_guilds(access_token: str) -> list[dict]:
    """Fetch every guild the logged-in user is a member of, including
    their permission bitfield and owner status in each one."""

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{DISCORD_API_BASE_URL}/users/@me/guilds",
            params={"with_counts": "true"},
            headers={"Authorization": f"Bearer {access_token}"},
        )

    if response.status_code != 200:
        raise DiscordOAuthError(
            f"Failed to fetch Discord guilds: {response.status_code} {response.text}"
        )

    return response.json()


def guild_permissions_allow_management(guild: dict) -> bool:
    """Check whether a guild entry from /users/@me/guilds grants the user
    permission to manage the server (owner, or Administrator / Manage
    Server permission) — this is the same bar the bot itself uses to
    decide who can run admin commands."""

    if guild.get("owner"):
        return True

    permissions = int(guild.get("permissions", 0))

    return bool(
        permissions & PERMISSION_ADMINISTRATOR
        or permissions & PERMISSION_MANAGE_GUILD
    )


# =========================
# Bot-integration live data
# =========================
#
# Everything below calls Raxor's own bot process directly over HTTP — its
# existing health-check web server plus tightly allow-listed integration
# routes (see the bot's web/internal.py) — instead of calling Discord's API
# with the bot's Discord token. Mutating calls are limited to explicit Save
# operations and rollback of resources created by the same Save.
#
# The dashboard never holds DISCORD_TOKEN. It only holds
# DASHBOARD_INTERNAL_KEY, a separate secret that these three read-only
# operations accept and nothing else does — so even if the dashboard is
# fully compromised, the worst it leaks is "list channels/roles/members
# of guilds Raxor is in", not a bot token capable of sending messages,
# banning members, or anything else Raxor itself can do.


def _require_bot_integration() -> str:
    if not BOT_INTERNAL_API_URL or not DASHBOARD_INTERNAL_KEY:
        raise BotIntegrationNotConfigured(
            "BOT_INTERNAL_API_URL / DASHBOARD_INTERNAL_KEY are not set — "
            "set them (and the matching DASHBOARD_INTERNAL_KEY in "
            "Raxor/.env) to enable live channel/role selectors and "
            "username search."
        )
    return BOT_INTERNAL_API_URL


async def _bot_internal_get(path: str, *, params: dict | None = None) -> httpx.Response:
    base_url = _require_bot_integration()

    async with httpx.AsyncClient() as client:
        return await client.get(
            f"{base_url}{path}",
            params=params,
            headers={"Authorization": f"Bearer {DASHBOARD_INTERNAL_KEY}"},
            timeout=10.0,
        )


async def fetch_guild_channels(guild_id: int) -> list[dict]:
    """List a guild's text-capable channels, as Raxor itself sees them.
    Used to back the dashboard's channel selectors with real channels
    instead of a raw ID field."""

    response = await _bot_internal_get(f"/internal/guilds/{guild_id}/channels")

    if response.status_code != 200:
        raise BotInternalAPIError(
            f"Failed to fetch channels for guild {guild_id}: "
            f"{response.status_code} {response.text}"
        )

    return response.json()


async def ensure_guild_channel(guild_id: int, name: str) -> dict:
    """Ensure a managed text channel exists in Raxor's guild and return it.

    This is intentionally the only mutating bot-integration operation:
    it is called from an explicit dashboard Save action when a required
    feature has no selected channel. The bot, not the dashboard, owns the
    Discord token and performs the actual channel creation.
    """
    base_url = _require_bot_integration()

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{base_url}/internal/guilds/{guild_id}/channels/ensure",
            json={"name": name},
            headers={"Authorization": f"Bearer {DASHBOARD_INTERNAL_KEY}"},
            timeout=15.0,
        )

    if response.status_code != 200:
        raise BotInternalAPIError(
            f"Failed to ensure channel for guild {guild_id}: "
            f"{response.status_code} {response.text}"
        )

    return response.json()


async def ensure_guild_role(guild_id: int, name: str) -> dict:
    """Ensure a managed Discord role exists through Raxor."""
    base_url = _require_bot_integration()
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{base_url}/internal/guilds/{guild_id}/roles/ensure",
            json={"name": name},
            headers={"Authorization": f"Bearer {DASHBOARD_INTERNAL_KEY}"},
            timeout=15.0,
        )
    if response.status_code != 200:
        raise BotInternalAPIError(
            f"Failed to ensure role for guild {guild_id}: {response.status_code} {response.text}"
        )
    return response.json()




async def delete_guild_channel(guild_id: int, channel_id: str, rollback_token: str) -> dict:
    """Delete a channel that this dashboard Save just created during rollback."""
    base_url = _require_bot_integration()
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{base_url}/internal/guilds/{guild_id}/channels/delete",
            json={"channel_id": str(channel_id)},
            headers={"Authorization": f"Bearer {DASHBOARD_INTERNAL_KEY}", "X-Rollback-Token": rollback_token},
            timeout=15.0,
        )
    if response.status_code != 200:
        raise BotInternalAPIError(
            f"Failed to rollback channel {channel_id}: {response.status_code} {response.text}"
        )
    return response.json()


async def delete_guild_role(guild_id: int, role_id: str, rollback_token: str) -> dict:
    """Delete a role that this dashboard Save just created during rollback."""
    base_url = _require_bot_integration()
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{base_url}/internal/guilds/{guild_id}/roles/delete",
            json={"role_id": str(role_id)},
            headers={"Authorization": f"Bearer {DASHBOARD_INTERNAL_KEY}", "X-Rollback-Token": rollback_token},
            timeout=15.0,
        )
    if response.status_code != 200:
        raise BotInternalAPIError(
            f"Failed to rollback role {role_id}: {response.status_code} {response.text}"
        )
    return response.json()


async def configure_verification(guild_id: int, channel_id: str, role_id: str) -> dict:
    """Configure the verification channel and persistent Verify button."""
    base_url = _require_bot_integration()
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{base_url}/internal/guilds/{guild_id}/verification/configure",
            json={"channel_id": channel_id, "role_id": role_id},
            headers={"Authorization": f"Bearer {DASHBOARD_INTERNAL_KEY}"},
            timeout=20.0,
        )
    if response.status_code != 200:
        raise BotInternalAPIError(
            f"Failed to configure verification for guild {guild_id}: {response.status_code} {response.text}"
        )
    return response.json()


async def fetch_guild_roles(guild_id: int) -> list[dict]:
    """List a guild's roles (excluding @everyone), as Raxor itself sees
    them. Used to back the dashboard's role selectors (level rewards,
    weekly leaderboard rewards) with real roles instead of a raw ID
    field."""

    response = await _bot_internal_get(f"/internal/guilds/{guild_id}/roles")

    if response.status_code != 200:
        raise BotInternalAPIError(
            f"Failed to fetch roles for guild {guild_id}: "
            f"{response.status_code} {response.text}"
        )

    return response.json()


async def search_guild_members(guild_id: int, query: str, limit: int = 10) -> list[dict]:
    """Search a guild's members by username/nickname prefix, the same
    way Discord's own member list search works. Used so the Users page
    can search by name — the dashboard's own database only ever stores
    a user_id, never a username (see the bot's database/models.py), so
    without this a "search" box could only ever match raw IDs."""

    response = await _bot_internal_get(
        f"/internal/guilds/{guild_id}/members/search",
        params={"query": query, "limit": max(1, min(limit, 100))},
    )

    if response.status_code != 200:
        raise BotInternalAPIError(
            f"Failed to search members of guild {guild_id}: "
            f"{response.status_code} {response.text}"
        )

    return response.json()
