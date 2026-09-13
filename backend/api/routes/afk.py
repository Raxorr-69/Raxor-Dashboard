from fastapi import APIRouter, Depends

from api.dependencies import get_db_pool, require_guild_access
from db import repositories
from utils.responses import rows_to_dicts
from utils.validators import parse_snowflake


router = APIRouter(prefix="/guilds/{guild_id}/afk", tags=["afk"])


@router.get("")
async def list_afk_users(
    guild_id: str,
    session: dict = Depends(require_guild_access),
    pool=Depends(get_db_pool),
):
    """Everyone currently marked AFK in this server."""

    rows = await repositories.list_afk_users(pool, parse_snowflake(guild_id))

    users = rows_to_dicts(rows)
    for user in users:
        user["user_id"] = str(user["user_id"])
        user["guild_id"] = str(user["guild_id"])
        user["started_at"] = user["started_at"].isoformat()

    return users


@router.delete("/{user_id}")
async def clear_afk(
    guild_id: str,
    user_id: str,
    session: dict = Depends(require_guild_access),
    pool=Depends(get_db_pool),
):
    """Manually clear a member's AFK status from the dashboard."""

    await repositories.remove_afk(pool, parse_snowflake(guild_id), parse_snowflake(user_id))
    return {"cleared": True}
