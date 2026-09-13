from fastapi import APIRouter, Depends

from api.dependencies import get_db_pool, require_guild_access
from core.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from db import repositories
from services.statistics_service import get_invite_leaderboard
from utils.validators import parse_snowflake


router = APIRouter(prefix="/guilds/{guild_id}/invites", tags=["invites"])


@router.get("/leaderboard")
async def read_invite_leaderboard(
    guild_id: str,
    limit: int = DEFAULT_PAGE_SIZE,
    session: dict = Depends(require_guild_access),
    pool=Depends(get_db_pool),
):
    limit = max(1, min(limit, MAX_PAGE_SIZE))

    return await get_invite_leaderboard(pool, parse_snowflake(guild_id), limit=limit)


@router.get("/{user_id}")
async def read_member_inviter(
    guild_id: str,
    user_id: str,
    session: dict = Depends(require_guild_access),
    pool=Depends(get_db_pool),
):
    """Who invited a specific member — Unknown/None if they joined
    before invite tracking was set up, or via an untracked path
    (e.g. a vanity URL)."""

    inviter_id = await repositories.get_inviter(
        pool, parse_snowflake(guild_id), parse_snowflake(user_id)
    )

    return {
        "user_id": user_id,
        "inviter_id": str(inviter_id) if inviter_id is not None else None,
    }
