import datetime

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from core.security import decode_session_jwt
from db import repositories
from db import sessions as session_repo
from services.discord import DiscordOAuthError, fetch_current_user_guilds, refresh_access_token
from services.guild_service import resolve_manageable_guilds
from utils.permissions import user_can_manage_guild
from utils.validators import parse_snowflake


bearer_scheme = HTTPBearer(auto_error=False)

GUILD_CACHE_TTL_SECONDS = 60


async def get_db_pool(request: Request):
    """Get the shared asyncpg pool (created once at startup in main.py)."""

    return request.app.state.pool


async def get_current_session(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    pool=Depends(get_db_pool),
) -> dict:
    """Decode the session JWT, then load the live session it references
    from Postgres (see db/sessions.py).

    Raises 401 if the header is missing, the token is invalid/expired,
    or the session row is gone/expired — e.g. the user logged out
    elsewhere, or an admin cleared sessions. Either way the fix is the
    same: log in again.
    """

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated.",
        )

    try:
        payload = decode_session_jwt(credentials.credentials)
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session.",
        )

    session = await session_repo.get_session(pool, payload.get("sid", ""))
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Your session has expired. Please log in again.",
        )

    return session


async def refresh_session_guilds(session: dict, pool) -> None:
    """Re-fetch the user's manageable-guild snapshot from Discord right
    now, persist it, and update the in-memory `session` dict passed in
    so the rest of the current request sees the fresh value too.

    Falls back silently to the existing snapshot if Discord can't be
    reached or the refresh token is dead, rather than locking the user
    out over a transient network error — the next call tries again.
    """

    access_token = session.get("access_token")
    if not access_token:
        return

    refresh_token = session.get("refresh_token")

    try:
        discord_guilds = await fetch_current_user_guilds(access_token)
    except DiscordOAuthError:
        if not refresh_token:
            return
        try:
            refreshed = await refresh_access_token(refresh_token)
            access_token = refreshed["access_token"]
            refresh_token = refreshed.get("refresh_token", refresh_token)
            discord_guilds = await fetch_current_user_guilds(access_token)
        except DiscordOAuthError:
            return

    manageable_guilds = await resolve_manageable_guilds(pool, discord_guilds)

    session["guilds"] = manageable_guilds
    session["guilds_cached_at"] = datetime.datetime.now(datetime.timezone.utc)
    session["access_token"] = access_token
    session["refresh_token"] = refresh_token

    await session_repo.update_session_guilds(
        pool, session["session_id"], manageable_guilds, access_token, refresh_token
    )


async def ensure_fresh_session_guilds(session: dict, pool) -> None:
    """Refresh the session's guild snapshot only if it's older than
    GUILD_CACHE_TTL_SECONDS, so routine requests don't each cost a round
    trip to Discord and a database write."""

    cached_at = session.get("guilds_cached_at")
    if cached_at is not None:
        age = (datetime.datetime.now(datetime.timezone.utc) - cached_at).total_seconds()
        if age < GUILD_CACHE_TTL_SECONDS:
            return

    await refresh_session_guilds(session, pool)


async def require_guild_access(
    guild_id: str,
    session: dict = Depends(get_current_session),
    pool=Depends(get_db_pool),
) -> dict:
    """Ensure the logged-in user can *currently* manage this guild.

    Used as a dependency on every `/guilds/{guild_id}/...` route. FastAPI
    matches the `guild_id` parameter here to the route's path parameter.

    Two things are checked live rather than trusted from a stale
    snapshot:
      1. The bot is still actually installed here — read straight from
         the bot's own `guilds` table, so this is never wrong.
      2. The user still has Manage Server / Administrator / ownership —
         re-fetched from Discord whenever the cached snapshot is older
         than GUILD_CACHE_TTL_SECONDS, so a revoked role or an
         ownership change shows up within about a minute instead of
         staying valid for the rest of the session.
    """

    if not await repositories.guild_exists(pool, parse_snowflake(guild_id)):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The bot isn't in this server (anymore).",
        )

    await ensure_fresh_session_guilds(session, pool)

    if not user_can_manage_guild(session.get("guilds", []), guild_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this server.",
        )

    return session
