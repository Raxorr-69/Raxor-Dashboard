from services import statistics_service
from services.guild_service import get_guild_detail


async def get_overview(pool, guild_id: int, session_guild: dict) -> dict:
    """Everything the Overview page needs in one call: guild snapshot,
    30-day totals, and the recent activity trend."""

    guild = await get_guild_detail(pool, guild_id, session_guild)
    stats = await statistics_service.get_overview(pool, guild_id)
    activity = await statistics_service.get_activity(pool, guild_id, period="monthly")

    return {
        "guild": guild,
        "stats": stats,
        "activity": activity,
    }
