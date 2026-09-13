"""
Read/write access to the Raxor bot's Postgres tables.

This module intentionally duplicates (rather than imports) the bot's query
logic — the dashboard is a separate codebase that happens to share the same
database. Table/column names and validation rules are kept in sync by hand
with the bot's database/models.py and database/repositories.py.
"""

from core.constants import (
    LEADERBOARD_TYPES,
    MODERATION_ACTIONS,
    RESTRICTION_TYPES,
)


# =========================
# Guilds
# =========================


async def get_guild(pool, guild_id: int):
    """Get configuration for a specific server, or None if the bot has
    never seen this server (i.e. it isn't in the `guilds` table)."""

    query = "SELECT * FROM guilds WHERE guild_id = $1"
    return await pool.fetchrow(query, guild_id)


async def guild_exists(pool, guild_id: int) -> bool:
    """Check whether the bot has a configuration row for this server —
    used to confirm the bot is actually installed there."""

    query = "SELECT 1 FROM guilds WHERE guild_id = $1"
    result = await pool.fetchval(query, guild_id)
    return result is not None


async def get_known_guild_ids(pool) -> set[int]:
    """Get every guild id the bot has ever configured (i.e. every server
    the bot is currently or was previously installed in)."""

    query = "SELECT guild_id FROM guilds"
    rows = await pool.fetch(query)
    return {row["guild_id"] for row in rows}


GUILD_SETTINGS_ALLOWED = {
    "message_tracking_enabled",
    "voice_tracking_enabled",
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
    "leveling_enabled",
    "xp_min",
    "xp_max",
    "level_up_messages_enabled",
    "level_up_channel_id",
    "announcement_channel_id",
    "welcome_enabled", "welcome_channel_id", "welcome_message", "welcome_gif_url",
    "leave_enabled", "leave_channel_id", "leave_message", "leave_gif_url",
    "level_up_message", "level_up_gif_url",
    "verification_enabled", "verification_channel_id", "verification_role_id",
}

_ACTION_SETTINGS = {"spam_action", "emoji_spam_action", "link_action"}

_NUMERIC_SETTINGS = {
    "spam_message_limit",
    "spam_message_window",
    "emoji_spam_limit",
    "spam_timeout_seconds",
    "emoji_spam_timeout_seconds",
    "xp_min",
    "xp_max",
    "link_timeout_seconds",
}


async def update_guild_setting(pool, guild_id: int, setting: str, value, *, validate_cross_field: bool = True):
    """Update a single server setting.

    Mirrors the bot's own validation exactly so the dashboard can never
    write a value the bot wouldn't accept from a command.
    """

    if setting not in GUILD_SETTINGS_ALLOWED:
        raise ValueError(f"Invalid guild setting: {setting}")

    if setting in _ACTION_SETTINGS and value not in MODERATION_ACTIONS:
        raise ValueError(f"Invalid action: {value}")

    if setting in _NUMERIC_SETTINGS:
        if not isinstance(value, int) or isinstance(value, bool):
            raise ValueError(f"{setting} must be an integer.")
        if value < 1:
            raise ValueError(f"{setting} must be greater than zero.")

    if validate_cross_field and setting in ("xp_min", "xp_max"):
        current_guild = await get_guild(pool, guild_id)
        if current_guild is None:
            raise ValueError("Guild configuration does not exist.")

        if setting == "xp_min" and value > current_guild["xp_max"]:
            raise ValueError("xp_min cannot be greater than xp_max.")
        if setting == "xp_max" and value < current_guild["xp_min"]:
            raise ValueError("xp_max cannot be less than xp_min.")

    query = f"UPDATE guilds SET {setting} = $1 WHERE guild_id = $2"
    await pool.execute(query, value, guild_id)


# =========================
# Users
# =========================


async def get_user(pool, user_id: int, guild_id: int):
    query = "SELECT * FROM users WHERE user_id = $1 AND guild_id = $2"
    return await pool.fetchrow(query, user_id, guild_id)


_USER_SORT_COLUMNS = {
    "xp": "xp",
    "level": "level",
    "messages": "message_count",
    "voice": "voice_seconds",
    "warnings": "warnings",
}


async def list_users(
    pool,
    guild_id: int,
    *,
    sort: str = "xp",
    search: str | None = None,
    user_ids: list[int] | None = None,
    limit: int = 25,
    offset: int = 0,
):
    """Paginated user listing for the Users table, sortable by any of the
    tracked metrics.

    `search` filters by user id prefix — there's no username stored in
    this table (the bot never stores one; see database/models.py), so
    that's the only filter this function itself can do.

    `user_ids`, when given, restricts to exactly that set of ids instead
    — this is how username search actually works end to end: the route
    (see api/routes/users.py) resolves a non-numeric search term to a
    list of user ids via a live Discord member-search call, then passes
    those ids in here to fetch their stats. `user_ids` takes priority
    over `search` if both are somehow given.
    """

    column = _USER_SORT_COLUMNS.get(sort, "xp")

    params = [guild_id]
    where = "WHERE guild_id = $1"

    if user_ids is not None:
        params.append(user_ids)
        where += f" AND user_id = ANY(${len(params)})"
    elif search:
        params.append(f"{search}%")
        where += f" AND CAST(user_id AS TEXT) LIKE ${len(params)}"

    params.extend([limit, offset])

    query = f"""
    SELECT *
    FROM users
    {where}
    ORDER BY {column} DESC, user_id ASC
    LIMIT ${len(params) - 1} OFFSET ${len(params)}
    """

    return await pool.fetch(query, *params)


async def count_users(pool, guild_id: int, *, search: str | None = None, user_ids: list[int] | None = None) -> int:
    params = [guild_id]
    where = "WHERE guild_id = $1"

    if user_ids is not None:
        params.append(user_ids)
        where += f" AND user_id = ANY(${len(params)})"
    elif search:
        params.append(f"{search}%")
        where += f" AND CAST(user_id AS TEXT) LIKE ${len(params)}"

    query = f"SELECT COUNT(*) FROM users {where}"
    return await pool.fetchval(query, *params)


# =========================
# Warnings
# =========================


async def get_warning_history(pool, guild_id: int, user_id: int):
    query = """
    SELECT warning_id, user_id, moderator_id, reason, created_at
    FROM warning_history
    WHERE guild_id = $1 AND user_id = $2
    ORDER BY created_at DESC, warning_id DESC
    """
    return await pool.fetch(query, guild_id, user_id)


async def list_recent_warnings(pool, guild_id: int, *, limit: int = 50):
    """All recent warnings across the whole server, for the Moderation page."""

    query = """
    SELECT warning_id, user_id, moderator_id, reason, created_at
    FROM warning_history
    WHERE guild_id = $1
    ORDER BY created_at DESC, warning_id DESC
    LIMIT $2
    """
    return await pool.fetch(query, guild_id, limit)


async def remove_warning(pool, guild_id: int, warning_id: int) -> bool:
    query = """
    DELETE FROM warning_history
    WHERE guild_id = $1 AND warning_id = $2
    RETURNING user_id
    """
    user_id = await pool.fetchval(query, guild_id, warning_id)

    if user_id is None:
        return False

    await pool.execute(
        "UPDATE users SET warnings = GREATEST(warnings - 1, 0) "
        "WHERE user_id = $1 AND guild_id = $2",
        user_id,
        guild_id,
    )
    return True


async def clear_warning_history(pool, guild_id: int, user_id: int):
    await pool.execute(
        "DELETE FROM warning_history WHERE guild_id = $1 AND user_id = $2",
        guild_id,
        user_id,
    )
    await pool.execute(
        "UPDATE users SET warnings = 0 WHERE user_id = $1 AND guild_id = $2",
        user_id,
        guild_id,
    )


# =========================
# Channel Rules
# =========================


async def list_channel_rules(pool, guild_id: int):
    query = """
    SELECT guild_id, channel_id, image_only, clips_only
    FROM channel_rules
    WHERE guild_id = $1
      AND (image_only OR clips_only)
    ORDER BY channel_id
    """
    return await pool.fetch(query, guild_id)


async def update_channel_rule(pool, guild_id: int, channel_id: int, rule: str, enabled: bool):
    allowed_rules = {"image_only", "clips_only"}

    if rule not in allowed_rules:
        raise ValueError(f"Invalid channel rule: {rule}")

    await pool.execute(
        """
        INSERT INTO channel_rules (guild_id, channel_id)
        VALUES ($1, $2)
        ON CONFLICT (guild_id, channel_id) DO NOTHING
        """,
        guild_id,
        channel_id,
    )

    query = f"""
    UPDATE channel_rules
    SET {rule} = $1
    WHERE guild_id = $2 AND channel_id = $3
    """
    await pool.execute(query, enabled, guild_id, channel_id)


# =========================
# Statistics Excluded Channels
# =========================


async def get_statistics_excluded_channels(pool, guild_id: int):
    query = """
    SELECT channel_id FROM statistics_excluded_channels
    WHERE guild_id = $1 ORDER BY channel_id
    """
    return await pool.fetch(query, guild_id)


async def add_statistics_excluded_channel(pool, guild_id: int, channel_id: int):
    await pool.execute(
        """
        INSERT INTO statistics_excluded_channels (guild_id, channel_id)
        VALUES ($1, $2)
        ON CONFLICT (guild_id, channel_id) DO NOTHING
        """,
        guild_id,
        channel_id,
    )


async def remove_statistics_excluded_channel(pool, guild_id: int, channel_id: int):
    await pool.execute(
        "DELETE FROM statistics_excluded_channels WHERE guild_id = $1 AND channel_id = $2",
        guild_id,
        channel_id,
    )


# =========================
# Whitelist
# =========================


async def list_whitelist(pool, guild_id: int, restriction_type: str | None = None):
    if restriction_type is not None and restriction_type not in RESTRICTION_TYPES:
        raise ValueError(f"Invalid restriction type: {restriction_type}")

    if restriction_type is None:
        query = """
        SELECT guild_id, target_id, restriction_type
        FROM whitelists WHERE guild_id = $1
        ORDER BY restriction_type, target_id
        """
        return await pool.fetch(query, guild_id)

    query = """
    SELECT guild_id, target_id, restriction_type
    FROM whitelists WHERE guild_id = $1 AND restriction_type = $2
    ORDER BY target_id
    """
    return await pool.fetch(query, guild_id, restriction_type)


async def add_whitelist(pool, guild_id: int, target_id: int, restriction_type: str):
    if restriction_type not in RESTRICTION_TYPES:
        raise ValueError(f"Invalid restriction type: {restriction_type}")

    await pool.execute(
        """
        INSERT INTO whitelists (guild_id, target_id, restriction_type)
        VALUES ($1, $2, $3)
        ON CONFLICT (guild_id, target_id, restriction_type) DO NOTHING
        """,
        guild_id,
        target_id,
        restriction_type,
    )


async def remove_whitelist(pool, guild_id: int, target_id: int, restriction_type: str):
    if restriction_type not in RESTRICTION_TYPES:
        raise ValueError(f"Invalid restriction type: {restriction_type}")

    await pool.execute(
        """
        DELETE FROM whitelists
        WHERE guild_id = $1 AND target_id = $2 AND restriction_type = $3
        """,
        guild_id,
        target_id,
        restriction_type,
    )


# =========================
# AFK
# =========================


async def list_afk_users(pool, guild_id: int):
    query = """
    SELECT guild_id, user_id, reason, started_at
    FROM afk_users
    WHERE guild_id = $1
    ORDER BY started_at ASC
    """
    return await pool.fetch(query, guild_id)


async def remove_afk(pool, guild_id: int, user_id: int):
    await pool.execute(
        "DELETE FROM afk_users WHERE guild_id = $1 AND user_id = $2",
        guild_id,
        user_id,
    )


# =========================
# Invite Tracking
# =========================


async def get_inviter(pool, guild_id: int, user_id: int):
    query = "SELECT inviter_id FROM invite_tracking WHERE guild_id = $1 AND user_id = $2"
    return await pool.fetchval(query, guild_id, user_id)


async def get_invite_leaderboard(pool, guild_id: int, *, limit: int = 25):
    """Rank inviters by how many current members they invited."""

    query = """
    SELECT inviter_id, COUNT(*) AS invite_count
    FROM invite_tracking
    WHERE guild_id = $1 AND inviter_id IS NOT NULL
    GROUP BY inviter_id
    ORDER BY invite_count DESC, inviter_id ASC
    LIMIT $2
    """
    return await pool.fetch(query, guild_id, limit)


# =========================
# Level Rewards
# =========================


async def get_all_level_rewards(pool, guild_id: int):
    query = """
    SELECT level, role_id FROM level_rewards
    WHERE guild_id = $1 ORDER BY level ASC, role_id ASC
    """
    return await pool.fetch(query, guild_id)


async def add_level_reward(pool, guild_id: int, level: int, role_id: int):
    if level < 1:
        raise ValueError("Level must be greater than or equal to 1.")

    await pool.execute(
        """
        INSERT INTO level_rewards (guild_id, level, role_id)
        VALUES ($1, $2, $3)
        ON CONFLICT (guild_id, level, role_id) DO NOTHING
        """,
        guild_id,
        level,
        role_id,
    )


async def remove_level_reward(pool, guild_id: int, level: int, role_id: int):
    await pool.execute(
        "DELETE FROM level_rewards WHERE guild_id = $1 AND level = $2 AND role_id = $3",
        guild_id,
        level,
        role_id,
    )


# =========================
# Weekly Leaderboard Rewards
# =========================


async def get_leaderboard_rewards(pool, guild_id: int):
    """Get both configured leaderboard reward roles (messages + voice)."""

    query = """
    SELECT leaderboard_type, role_id FROM leaderboard_rewards
    WHERE guild_id = $1
    """
    rows = await pool.fetch(query, guild_id)
    return {row["leaderboard_type"]: row["role_id"] for row in rows}


async def set_leaderboard_reward_role(pool, guild_id: int, leaderboard_type: str, role_id: int):
    if leaderboard_type not in LEADERBOARD_TYPES:
        raise ValueError(f"Invalid leaderboard type: {leaderboard_type}")

    await pool.execute(
        """
        INSERT INTO leaderboard_rewards (guild_id, leaderboard_type, role_id)
        VALUES ($1, $2, $3)
        ON CONFLICT (guild_id, leaderboard_type)
        DO UPDATE SET role_id = EXCLUDED.role_id
        """,
        guild_id,
        leaderboard_type,
        role_id,
    )


async def remove_leaderboard_reward_role(pool, guild_id: int, leaderboard_type: str):
    if leaderboard_type not in LEADERBOARD_TYPES:
        raise ValueError(f"Invalid leaderboard type: {leaderboard_type}")

    await pool.execute(
        "DELETE FROM leaderboard_rewards WHERE guild_id = $1 AND leaderboard_type = $2",
        guild_id,
        leaderboard_type,
    )


# =========================
# Statistics — Messages
# =========================


async def get_all_message_stats(pool, guild_id: int, *, limit: int = 25):
    query = """
    SELECT user_id, message_count FROM users
    WHERE guild_id = $1 AND message_count > 0
    ORDER BY message_count DESC, user_id ASC
    LIMIT $2
    """
    return await pool.fetch(query, guild_id, limit)


async def get_daily_message_stats(pool, guild_id: int, start_date, end_date, *, limit: int = 25):
    query = """
    SELECT user_id, SUM(message_count) AS message_count
    FROM message_statistics
    WHERE guild_id = $1 AND statistic_date >= $2 AND statistic_date < $3
    GROUP BY user_id
    ORDER BY message_count DESC, user_id ASC
    LIMIT $4
    """
    return await pool.fetch(query, guild_id, start_date, end_date, limit)


async def get_message_activity(pool, guild_id: int, start_date, end_date):
    """Daily message totals across the whole server — for the activity chart."""

    query = """
    SELECT statistic_date, SUM(message_count) AS message_count
    FROM message_statistics
    WHERE guild_id = $1 AND statistic_date >= $2 AND statistic_date < $3
    GROUP BY statistic_date
    ORDER BY statistic_date ASC
    """
    return await pool.fetch(query, guild_id, start_date, end_date)


# =========================
# Statistics — Voice
# =========================


async def get_all_voice_stats(pool, guild_id: int, *, limit: int = 25):
    query = """
    SELECT user_id, voice_seconds FROM users
    WHERE guild_id = $1 AND voice_seconds > 0
    ORDER BY voice_seconds DESC, user_id ASC
    LIMIT $2
    """
    return await pool.fetch(query, guild_id, limit)


async def get_daily_voice_stats(pool, guild_id: int, start_date, end_date, *, limit: int = 25):
    query = """
    SELECT user_id, SUM(voice_seconds) AS voice_seconds
    FROM voice_statistics
    WHERE guild_id = $1 AND statistic_date >= $2 AND statistic_date < $3
    GROUP BY user_id
    ORDER BY voice_seconds DESC, user_id ASC
    LIMIT $4
    """
    return await pool.fetch(query, guild_id, start_date, end_date, limit)


async def get_voice_activity(pool, guild_id: int, start_date, end_date):
    """Daily voice-second totals across the whole server — for the activity chart."""

    query = """
    SELECT statistic_date, SUM(voice_seconds) AS voice_seconds
    FROM voice_statistics
    WHERE guild_id = $1 AND statistic_date >= $2 AND statistic_date < $3
    GROUP BY statistic_date
    ORDER BY statistic_date ASC
    """
    return await pool.fetch(query, guild_id, start_date, end_date)


# =========================
# Statistics — Channels
# =========================


async def get_channel_message_totals(pool, guild_id: int, start_date, end_date, *, limit: int = 25):
    query = """
    SELECT channel_id, SUM(message_count) AS message_count
    FROM channel_message_statistics
    WHERE guild_id = $1 AND statistic_date >= $2 AND statistic_date < $3
    GROUP BY channel_id
    ORDER BY message_count DESC, channel_id ASC
    LIMIT $4
    """
    return await pool.fetch(query, guild_id, start_date, end_date, limit)


async def get_channel_voice_totals(pool, guild_id: int, start_date, end_date, *, limit: int = 25):
    query = """
    SELECT channel_id, SUM(voice_seconds) AS voice_seconds
    FROM channel_voice_statistics
    WHERE guild_id = $1 AND statistic_date >= $2 AND statistic_date < $3
    GROUP BY channel_id
    ORDER BY voice_seconds DESC, channel_id ASC
    LIMIT $4
    """
    return await pool.fetch(query, guild_id, start_date, end_date, limit)


# =========================
# Message Recovery
# =========================


async def list_message_recovery_state(pool, guild_id: int):
    """Per-channel recovery status, including whether an on-demand
    rescan (queued via create_recovery_request below) is still pending —
    joined in from recovery_requests so the dashboard can show a
    "rescanning…" state without a second round trip."""

    query = """
    SELECT
        s.channel_id,
        s.last_scanned_at,
        r.requested_at AS rescan_requested_at
    FROM message_recovery_state s
    LEFT JOIN recovery_requests r
        ON r.guild_id = s.guild_id AND r.channel_id = s.channel_id
    WHERE s.guild_id = $1
    ORDER BY s.last_scanned_at DESC NULLS LAST
    """
    return await pool.fetch(query, guild_id)


async def create_recovery_request(pool, guild_id: int, channel_id: int, requested_by: int | None = None):
    """Queue an on-demand rescan for a channel — picked up by the bot's
    own recovery_request_poll_loop (bot/events.py), never executed by
    the dashboard itself. Safe to call again for a channel that already
    has a pending request; it just refreshes the timestamp."""

    query = """
    INSERT INTO recovery_requests (guild_id, channel_id, requested_by)
    VALUES ($1, $2, $3)
    ON CONFLICT (guild_id, channel_id)
    DO UPDATE SET
        requested_at = NOW(),
        requested_by = EXCLUDED.requested_by
    """
    await pool.execute(query, guild_id, channel_id, requested_by)
