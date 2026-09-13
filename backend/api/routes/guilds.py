from fastapi import APIRouter, Depends, HTTPException, status

from api.dependencies import (
    get_current_session,
    get_db_pool,
    refresh_session_guilds,
    require_guild_access,
)
from services.dashboard_service import get_overview
from services.discord import BotIntegrationNotConfigured, BotInternalAPIError, fetch_guild_channels, fetch_guild_roles
from services.guild_service import get_guild_detail
from utils.permissions import find_session_guild
from utils.validators import parse_snowflake


router = APIRouter(prefix="/guilds", tags=["guilds"])


@router.get("")
async def list_guilds(
    session: dict = Depends(get_current_session),
    pool=Depends(get_db_pool),
):
    """List every guild the logged-in user can manage — refreshed live
    from Discord on every call. This is the dashboard's server picker,
    so staleness here is the most visible possible place for it: it
    would either show a server the user no longer controls, or hide one
    they just got access to."""

    await refresh_session_guilds(session, pool)
    return session.get("guilds", [])


@router.get("/{guild_id}")
async def get_guild(
    guild_id: str,
    session: dict = Depends(require_guild_access),
    pool=Depends(get_db_pool),
):
    session_guild = find_session_guild(session.get("guilds", []), guild_id)

    guild = await get_guild_detail(pool, parse_snowflake(guild_id), session_guild)

    if guild is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The bot hasn't been set up in this server yet.",
        )

    return guild


@router.get("/{guild_id}/overview")
async def get_guild_overview(
    guild_id: str,
    session: dict = Depends(require_guild_access),
    pool=Depends(get_db_pool),
):
    session_guild = find_session_guild(session.get("guilds", []), guild_id)

    return await get_overview(pool, parse_snowflake(guild_id), session_guild)


@router.get("/{guild_id}/discord/channels")
async def get_guild_channels(
    guild_id: str,
    session: dict = Depends(require_guild_access),
):
    """Live channel list for this guild, fetched from Raxor's own
    running process (see services/discord.py — the dashboard never
    touches Discord's bot token for this). Backs the dashboard's
    channel selectors. Returns an empty list — not an error — if
    BOT_INTERNAL_API_URL/DASHBOARD_INTERNAL_KEY aren't configured, so
    selectors can fall back to plain manual ID entry."""

    try:
        return await fetch_guild_channels(parse_snowflake(guild_id))
    except BotIntegrationNotConfigured:
        return []
    except BotInternalAPIError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))


@router.get("/{guild_id}/discord/roles")
async def get_guild_roles(
    guild_id: str,
    session: dict = Depends(require_guild_access),
):
    """Live role list for this guild, fetched from Raxor's own running
    process. Backs the dashboard's role selectors (level rewards,
    leaderboard rewards). Same fallback as channels above."""

    try:
        return await fetch_guild_roles(parse_snowflake(guild_id))
    except BotIntegrationNotConfigured:
        return []
    except BotInternalAPIError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))
