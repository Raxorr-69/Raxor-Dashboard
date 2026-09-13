import datetime

from db import repositories
from utils.validators import daterange_days, resolve_period_range


def _rank(rows: list, value_key: str) -> list[dict]:
    return [
        {"rank": index + 1, "user_id": str(row["user_id"]), "value": row[value_key]}
        for index, row in enumerate(rows)
    ]


async def get_leaderboard(
    pool,
    guild_id: int,
    *,
    category: str,
    period: str,
    limit: int = 25,
) -> list[dict]:
    """Ranked leaderboard for a category ("messages" | "voice") over a
    period ("weekly" | "monthly" | "all")."""

    if category not in ("messages", "voice"):
        raise ValueError(f"Invalid leaderboard category: {category}")

    if period == "all":
        if category == "messages":
            rows = await repositories.get_all_message_stats(pool, guild_id, limit=limit)
            return _rank(rows, "message_count")

        rows = await repositories.get_all_voice_stats(pool, guild_id, limit=limit)
        return _rank(rows, "voice_seconds")

    start_date, end_date = resolve_period_range(period)

    if category == "messages":
        rows = await repositories.get_daily_message_stats(
            pool, guild_id, start_date, end_date, limit=limit
        )
        return _rank(rows, "message_count")

    rows = await repositories.get_daily_voice_stats(
        pool, guild_id, start_date, end_date, limit=limit
    )
    return _rank(rows, "voice_seconds")


async def get_activity(pool, guild_id: int, *, period: str) -> dict:
    """Day-by-day server-wide totals for the activity chart."""

    if period == "all":
        # Cap "all" activity charts to the last 90 days so the query and
        # the chart both stay fast/readable; the leaderboard still
        # supports true all-time totals separately.
        end_date = datetime.date.today() + datetime.timedelta(days=1)
        start_date = end_date - datetime.timedelta(days=90)
    else:
        start_date, end_date = resolve_period_range(period)

    message_rows = await repositories.get_message_activity(pool, guild_id, start_date, end_date)
    voice_rows = await repositories.get_voice_activity(pool, guild_id, start_date, end_date)

    return {
        "messages": [
            {"date": row["statistic_date"].isoformat(), "value": row["message_count"]}
            for row in message_rows
        ],
        "voice": [
            {"date": row["statistic_date"].isoformat(), "value": row["voice_seconds"]}
            for row in voice_rows
        ],
    }


async def get_overview(pool, guild_id: int) -> dict:
    """Summary numbers for the Overview page: rolling 30-day totals."""

    start_date, end_date = resolve_period_range("monthly")
    # Use a fixed 30-day window rather than "since the 1st of the month"
    # so the overview doesn't reset to near-zero on the 1st.
    import datetime

    end_date = datetime.date.today() + datetime.timedelta(days=1)
    start_date = end_date - datetime.timedelta(days=30)

    message_rows = await repositories.get_message_activity(pool, guild_id, start_date, end_date)
    voice_rows = await repositories.get_voice_activity(pool, guild_id, start_date, end_date)
    tracked_users = await repositories.count_users(pool, guild_id)

    return {
        "total_messages": sum(row["message_count"] for row in message_rows),
        "total_voice_seconds": sum(row["voice_seconds"] for row in voice_rows),
        "tracked_users": tracked_users,
        "period_days": daterange_days(start_date, end_date),
    }


async def get_channel_stats(pool, guild_id: int, *, period: str, limit: int = 25) -> dict:
    if period == "all":
        # Channel stats are only tracked daily, so "all" falls back to a
        # generous 365-day window rather than an unbounded scan.
        end_date = datetime.date.today() + datetime.timedelta(days=1)
        start_date = end_date - datetime.timedelta(days=365)
    else:
        start_date, end_date = resolve_period_range(period)

    message_rows = await repositories.get_channel_message_totals(
        pool, guild_id, start_date, end_date, limit=limit
    )
    voice_rows = await repositories.get_channel_voice_totals(
        pool, guild_id, start_date, end_date, limit=limit
    )

    return {
        "messages": [
            {"channel_id": str(row["channel_id"]), "value": row["message_count"]}
            for row in message_rows
        ],
        "voice": [
            {"channel_id": str(row["channel_id"]), "value": row["voice_seconds"]}
            for row in voice_rows
        ],
    }


async def get_invite_leaderboard(pool, guild_id: int, *, limit: int = 25) -> list[dict]:
    rows = await repositories.get_invite_leaderboard(pool, guild_id, limit=limit)

    return [
        {
            "rank": index + 1,
            "inviter_id": str(row["inviter_id"]),
            "invite_count": row["invite_count"],
        }
        for index, row in enumerate(rows)
    ]
