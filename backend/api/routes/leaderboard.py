from fastapi import APIRouter, Depends, HTTPException, status

from api.dependencies import get_db_pool, require_guild_access
from core.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE, RANK_PERIODS
from services.statistics_service import get_leaderboard
from utils.validators import parse_snowflake


router = APIRouter(prefix="/guilds/{guild_id}/leaderboard", tags=["leaderboard"])


@router.get("")
async def read_leaderboard(
    guild_id: str,
    category: str = "messages",
    period: str = "weekly",
    limit: int = DEFAULT_PAGE_SIZE,
    session: dict = Depends(require_guild_access),
    pool=Depends(get_db_pool),
):
    if period not in RANK_PERIODS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid period: {period}. Expected one of {sorted(RANK_PERIODS)}.",
        )

    limit = max(1, min(limit, MAX_PAGE_SIZE))

    try:
        return await get_leaderboard(
            pool,
            parse_snowflake(guild_id),
            category=category,
            period=period,
            limit=limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
