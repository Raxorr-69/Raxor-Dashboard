from fastapi import APIRouter, Depends, HTTPException, status

from api.dependencies import get_db_pool, require_guild_access
from core.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE, RANK_PERIODS
from services import statistics_service
from utils.validators import parse_snowflake


router = APIRouter(prefix="/guilds/{guild_id}/statistics", tags=["statistics"])


def _validate_period(period: str):
    if period not in RANK_PERIODS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid period: {period}. Expected one of {sorted(RANK_PERIODS)}.",
        )


@router.get("/overview")
async def read_overview(
    guild_id: str,
    session: dict = Depends(require_guild_access),
    pool=Depends(get_db_pool),
):
    return await statistics_service.get_overview(pool, parse_snowflake(guild_id))


@router.get("/activity")
async def read_activity(
    guild_id: str,
    period: str = "weekly",
    session: dict = Depends(require_guild_access),
    pool=Depends(get_db_pool),
):
    _validate_period(period)
    return await statistics_service.get_activity(pool, parse_snowflake(guild_id), period=period)


@router.get("/channels")
async def read_channel_stats(
    guild_id: str,
    period: str = "weekly",
    limit: int = DEFAULT_PAGE_SIZE,
    session: dict = Depends(require_guild_access),
    pool=Depends(get_db_pool),
):
    _validate_period(period)
    limit = max(1, min(limit, MAX_PAGE_SIZE))

    return await statistics_service.get_channel_stats(
        pool, parse_snowflake(guild_id), period=period, limit=limit
    )
