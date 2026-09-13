from fastapi import APIRouter, Depends, HTTPException, status

from api.dependencies import get_db_pool, require_guild_access
from schemas.settings import GuildSettingsOut, GuildSettingsUpdate
from services.discord import BotIntegrationNotConfigured, BotInternalAPIError
from services.settings_service import get_guild_settings, update_guild_settings
from utils.validators import parse_snowflake


router = APIRouter(prefix="/guilds/{guild_id}/settings", tags=["settings"])


@router.get("", response_model=GuildSettingsOut)
async def read_settings(
    guild_id: str,
    session: dict = Depends(require_guild_access),
    pool=Depends(get_db_pool),
):
    settings = await get_guild_settings(pool, parse_snowflake(guild_id))

    if settings is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The bot hasn't been set up in this server yet.",
        )

    return settings


@router.patch("", response_model=GuildSettingsOut)
async def patch_settings(
    guild_id: str,
    body: GuildSettingsUpdate,
    session: dict = Depends(require_guild_access),
    pool=Depends(get_db_pool),
):
    updates = body.model_dump(exclude_unset=True)

    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No settings were provided to update.",
        )

    try:
        return await update_guild_settings(pool, parse_snowflake(guild_id), updates)
    except (ValueError, BotIntegrationNotConfigured, BotInternalAPIError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
