from fastapi import APIRouter, Depends, HTTPException, status

from api.dependencies import get_db_pool, require_guild_access
from core.constants import RESTRICTION_TYPES
from services.discord import BotIntegrationNotConfigured, BotInternalAPIError, ensure_guild_channel
from db import repositories
from schemas.moderation import WhitelistEntryIn
from utils.responses import rows_to_dicts
from utils.validators import parse_snowflake


router = APIRouter(prefix="/guilds/{guild_id}", tags=["moderation"])


# =========================
# Warnings
# =========================


@router.get("/warnings")
async def list_warnings(
    guild_id: str,
    user_id: str | None = None,
    session: dict = Depends(require_guild_access),
    pool=Depends(get_db_pool),
):
    gid = parse_snowflake(guild_id)

    if user_id:
        rows = await repositories.get_warning_history(pool, gid, parse_snowflake(user_id))
    else:
        rows = await repositories.list_recent_warnings(pool, gid)

    warnings = rows_to_dicts(rows)
    for warning in warnings:
        warning["user_id"] = str(warning["user_id"])
        warning["moderator_id"] = str(warning["moderator_id"])
        warning["created_at"] = warning["created_at"].isoformat()

    return warnings


@router.delete("/warnings/{warning_id}")
async def delete_warning(
    guild_id: str,
    warning_id: int,
    session: dict = Depends(require_guild_access),
    pool=Depends(get_db_pool),
):
    removed = await repositories.remove_warning(pool, parse_snowflake(guild_id), warning_id)

    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No warning found with id {warning_id}.",
        )

    return {"removed": True}


@router.delete("/users/{user_id}/warnings")
async def clear_warnings(
    guild_id: str,
    user_id: str,
    session: dict = Depends(require_guild_access),
    pool=Depends(get_db_pool),
):
    await repositories.clear_warning_history(
        pool, parse_snowflake(guild_id), parse_snowflake(user_id)
    )
    return {"cleared": True}


# =========================
# Channel Rules
# =========================


@router.get("/channel-rules")
async def list_channel_rules(
    guild_id: str,
    session: dict = Depends(require_guild_access),
    pool=Depends(get_db_pool),
):
    rows = await repositories.list_channel_rules(pool, parse_snowflake(guild_id))
    rules = rows_to_dicts(rows)
    for rule in rules:
        rule["guild_id"] = str(rule["guild_id"])
        rule["channel_id"] = str(rule["channel_id"])
    return rules


@router.put("/channel-rules/{channel_id}")
async def set_channel_rule(
    guild_id: str,
    channel_id: str,
    rule: str,
    enabled: bool,
    session: dict = Depends(require_guild_access),
    pool=Depends(get_db_pool),
):
    try:
        if channel_id == "__auto__":
            channel_name = "restricted"
            channel = await ensure_guild_channel(parse_snowflake(guild_id), channel_name)
            channel_id = channel["id"]
        await repositories.update_channel_rule(
            pool,
            parse_snowflake(guild_id),
            parse_snowflake(channel_id),
            rule,
            enabled,
        )
    except (ValueError, BotIntegrationNotConfigured, BotInternalAPIError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    return {"channel_id": channel_id, "rule": rule, "enabled": enabled}


# =========================
# Restriction Whitelist
# =========================


@router.get("/whitelist")
async def list_whitelist(
    guild_id: str,
    restriction_type: str | None = None,
    session: dict = Depends(require_guild_access),
    pool=Depends(get_db_pool),
):
    try:
        rows = await repositories.list_whitelist(
            pool, parse_snowflake(guild_id), restriction_type
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    entries = rows_to_dicts(rows)
    for entry in entries:
        entry["target_id"] = str(entry["target_id"])
    return entries


@router.post("/whitelist")
async def add_whitelist_entry(
    guild_id: str,
    body: WhitelistEntryIn,
    session: dict = Depends(require_guild_access),
    pool=Depends(get_db_pool),
):
    if body.restriction_type not in RESTRICTION_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid restriction type: {body.restriction_type}",
        )

    await repositories.add_whitelist(
        pool,
        parse_snowflake(guild_id),
        parse_snowflake(body.target_id),
        body.restriction_type,
    )
    return {"added": True}


@router.delete("/whitelist/{target_id}")
async def remove_whitelist_entry(
    guild_id: str,
    target_id: str,
    restriction_type: str,
    session: dict = Depends(require_guild_access),
    pool=Depends(get_db_pool),
):
    try:
        await repositories.remove_whitelist(
            pool,
            parse_snowflake(guild_id),
            parse_snowflake(target_id),
            restriction_type,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    return {"removed": True}
