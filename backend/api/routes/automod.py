from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from api.dependencies import get_db_pool, require_guild_access
from services.settings_service import get_guild_settings, update_guild_settings
from utils.validators import parse_snowflake


router = APIRouter(prefix="/guilds/{guild_id}/automod", tags=["automod"])


_AUTOMOD_FIELDS = (
    "spam_enabled",
    "link_protection_enabled",
    "spam_message_limit",
    "spam_message_window",
    "emoji_spam_limit",
    "spam_action",
    "spam_timeout_seconds",
    "emoji_spam_action",
    "emoji_spam_timeout_seconds",
    "link_action",
    "link_timeout_seconds",
)


class AutoModUpdate(BaseModel):
    spam_enabled: bool | None = None
    link_protection_enabled: bool | None = None

    spam_message_limit: int | None = Field(default=None, ge=1)
    spam_message_window: int | None = Field(default=None, ge=1)
    emoji_spam_limit: int | None = Field(default=None, ge=1)

    spam_action: str | None = None
    spam_timeout_seconds: int | None = Field(default=None, ge=1)

    emoji_spam_action: str | None = None
    emoji_spam_timeout_seconds: int | None = Field(default=None, ge=1)

    link_action: str | None = None
    link_timeout_seconds: int | None = Field(default=None, ge=1)


@router.get("")
async def read_automod_settings(
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

    return {field: settings[field] for field in _AUTOMOD_FIELDS}


@router.patch("")
async def patch_automod_settings(
    guild_id: str,
    body: AutoModUpdate,
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
        settings = await update_guild_settings(pool, parse_snowflake(guild_id), updates)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    return {field: settings[field] for field in _AUTOMOD_FIELDS}
