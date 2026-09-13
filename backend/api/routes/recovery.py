from fastapi import APIRouter, Depends, status

from api.dependencies import get_db_pool, require_guild_access
from db import repositories
from utils.responses import rows_to_dicts
from utils.validators import parse_snowflake


router = APIRouter(prefix="/guilds/{guild_id}/recovery", tags=["recovery"])


@router.get("")
async def list_recovery_state(
    guild_id: str,
    session: dict = Depends(require_guild_access),
    pool=Depends(get_db_pool),
):
    """Per-channel message-recovery status: when the bot last finished
    scanning each channel for messages it may have missed while offline,
    and whether an on-demand rescan is currently queued for it."""

    rows = await repositories.list_message_recovery_state(pool, parse_snowflake(guild_id))

    states = rows_to_dicts(rows)
    for state in states:
        state["channel_id"] = str(state["channel_id"])
        state["last_scanned_at"] = (
            state["last_scanned_at"].isoformat()
            if state["last_scanned_at"] is not None
            else None
        )
        state["rescan_pending"] = state.pop("rescan_requested_at", None) is not None

    return states


@router.post("/{channel_id}/rescan", status_code=status.HTTP_202_ACCEPTED)
async def request_rescan(
    guild_id: str,
    channel_id: str,
    session: dict = Depends(require_guild_access),
    pool=Depends(get_db_pool),
):
    """Queue an on-demand rescan of a channel's message history.

    This only writes a request row — the dashboard has no way to
    execute a scan itself, since that means walking Discord message
    history with the bot's own gateway session. Raxor's own
    `recovery_request_poll_loop` (bot/events.py) picks the request up
    within ~20 seconds, runs it, and clears the row; poll
    `GET /guilds/{guild_id}/recovery` afterwards (the `rescan_pending`
    flag and `last_scanned_at` timestamp) to see it complete.
    """

    await repositories.create_recovery_request(
        pool,
        parse_snowflake(guild_id),
        parse_snowflake(channel_id),
        requested_by=int(session["discord_user_id"]),
    )

    return {"detail": "Rescan queued.", "channel_id": channel_id}
