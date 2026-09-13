from fastapi import APIRouter, Depends, HTTPException, status

from api.dependencies import get_db_pool, require_guild_access
from core.constants import LEADERBOARD_TYPES
from db import repositories
from services.discord import BotIntegrationNotConfigured, BotInternalAPIError, ensure_guild_role
from schemas.leveling import LeaderboardRewardIn, LevelRewardIn
from utils.responses import rows_to_dicts
from utils.validators import parse_snowflake


router = APIRouter(prefix="/guilds/{guild_id}", tags=["leveling"])


# =========================
# Level Rewards
# =========================


@router.get("/level-rewards")
async def list_level_rewards(
    guild_id: str,
    session: dict = Depends(require_guild_access),
    pool=Depends(get_db_pool),
):
    rows = await repositories.get_all_level_rewards(pool, parse_snowflake(guild_id))
    rewards = rows_to_dicts(rows)
    for reward in rewards:
        reward["role_id"] = str(reward["role_id"])
    return rewards


@router.post("/level-rewards")
async def add_level_reward(
    guild_id: str,
    body: LevelRewardIn,
    session: dict = Depends(require_guild_access),
    pool=Depends(get_db_pool),
):
    try:
        role_id = body.role_id.strip() if isinstance(body.role_id, str) else ""
        if not role_id or role_id == "__auto__":
            role = await ensure_guild_role(parse_snowflake(guild_id), f"Level {body.level}")
            role_id = role["id"]
        await repositories.add_level_reward(
            pool,
            parse_snowflake(guild_id),
            body.level,
            parse_snowflake(role_id),
        )
    except (ValueError, BotIntegrationNotConfigured, BotInternalAPIError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    return {"added": True}


@router.delete("/level-rewards/{level}/{role_id}")
async def remove_level_reward(
    guild_id: str,
    level: int,
    role_id: str,
    session: dict = Depends(require_guild_access),
    pool=Depends(get_db_pool),
):
    await repositories.remove_level_reward(
        pool,
        parse_snowflake(guild_id),
        level,
        parse_snowflake(role_id),
    )
    return {"removed": True}


# =========================
# Weekly Leaderboard Rewards
# =========================


@router.get("/leaderboard-rewards")
async def get_leaderboard_rewards(
    guild_id: str,
    session: dict = Depends(require_guild_access),
    pool=Depends(get_db_pool),
):
    rewards = await repositories.get_leaderboard_rewards(pool, parse_snowflake(guild_id))
    return {
        leaderboard_type: str(role_id)
        for leaderboard_type, role_id in rewards.items()
    }


@router.put("/leaderboard-rewards")
async def set_leaderboard_reward(
    guild_id: str,
    body: LeaderboardRewardIn,
    session: dict = Depends(require_guild_access),
    pool=Depends(get_db_pool),
):
    try:
        if body.leaderboard_type not in LEADERBOARD_TYPES:
            raise ValueError(f"Invalid leaderboard type: {body.leaderboard_type}")

        role_id = body.role_id.strip() if isinstance(body.role_id, str) else ""
        if not role_id or role_id == "__auto__":
            role_name = (
                "weekly-top-messages"
                if body.leaderboard_type == "messages"
                else "weekly-top-voice"
            )
            role = await ensure_guild_role(parse_snowflake(guild_id), role_name)
            role_id = role["id"]
        await repositories.set_leaderboard_reward_role(
            pool,
            parse_snowflake(guild_id),
            body.leaderboard_type,
            parse_snowflake(role_id),
        )
    except (ValueError, BotIntegrationNotConfigured, BotInternalAPIError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    return {"set": True}


@router.delete("/leaderboard-rewards/{leaderboard_type}")
async def remove_leaderboard_reward(
    guild_id: str,
    leaderboard_type: str,
    session: dict = Depends(require_guild_access),
    pool=Depends(get_db_pool),
):
    try:
        await repositories.remove_leaderboard_reward_role(
            pool, parse_snowflake(guild_id), leaderboard_type
        )
    except (ValueError, BotIntegrationNotConfigured, BotInternalAPIError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    return {"removed": True}
