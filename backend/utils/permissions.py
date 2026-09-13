def user_can_manage_guild(session_guilds: list[dict], guild_id: str) -> bool:
    """Check whether the logged-in user's session includes this guild."""

    return any(guild["id"] == guild_id for guild in session_guilds)


def find_session_guild(session_guilds: list[dict], guild_id: str) -> dict | None:
    """Get the cached guild snapshot (name/icon/member_count) from the
    session, if the user has access to it."""

    for guild in session_guilds:
        if guild["id"] == guild_id:
            return guild
    return None
