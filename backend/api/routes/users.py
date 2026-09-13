from fastapi import APIRouter, Depends, HTTPException, status

from api.dependencies import get_db_pool, require_guild_access
from core.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from db import repositories
from services.discord import BotIntegrationNotConfigured, BotInternalAPIError, search_guild_members
from utils.responses import paginated
from utils.validators import parse_snowflake


router = APIRouter(prefix="/guilds/{guild_id}/users", tags=["users"])


def _serialize_user(row: dict) -> dict:
    out = dict(row)
    out["user_id"] = str(out["user_id"])
    out["guild_id"] = str(out["guild_id"])
    return out


@router.get("")
async def list_users(
    guild_id: str,
    sort: str = "xp",
    search: str | None = None,
    limit: int = DEFAULT_PAGE_SIZE,
    offset: int = 0,
    session: dict = Depends(require_guild_access),
    pool=Depends(get_db_pool),
):
    """Paginated, sortable user table for the Users page.

    A numeric `search` term is matched against user id prefixes
    directly in the DB (fast, always available). A non-numeric term is
    treated as a username/nickname search: it's resolved to a set of
    user ids via a live call to Raxor's own member-search (see
    services/discord.py — requires BOT_INTERNAL_API_URL/
    DASHBOARD_INTERNAL_KEY), then that id set is used to filter the
    DB's stats table. If bot integration isn't configured, non-numeric
    search returns no results rather than silently matching everyone.
    """

    gid = parse_snowflake(guild_id)
    limit = max(1, min(limit, MAX_PAGE_SIZE))
    offset = max(0, offset)

    user_ids = None
    id_search = search

    if search and not search.strip().isdigit():
        id_search = None
        try:
            matches = await search_guild_members(gid, search.strip(), limit=limit)
            user_ids = [int(match["id"]) for match in matches]
        except BotIntegrationNotConfigured:
            user_ids = []
        except BotInternalAPIError:
            user_ids = []

        if not user_ids:
            return paginated([], total=0, limit=limit, offset=offset)

    rows = await repositories.list_users(
        pool, gid, sort=sort, search=id_search, user_ids=user_ids, limit=limit, offset=offset
    )
    total = await repositories.count_users(pool, gid, search=id_search, user_ids=user_ids)

    items = [_serialize_user(row) for row in rows]

    return paginated(items, total=total, limit=limit, offset=offset)


@router.get("/{user_id}")
async def get_user_profile(
    guild_id: str,
    user_id: str,
    session: dict = Depends(require_guild_access),
    pool=Depends(get_db_pool),
):
    row = await repositories.get_user(pool, parse_snowflake(user_id), parse_snowflake(guild_id))

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="This user has no activity recorded in this server.",
        )

    return _serialize_user(row)
