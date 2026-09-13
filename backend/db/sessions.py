import json
from cryptography.fernet import Fernet, InvalidToken
from core.config import SESSION_ENCRYPTION_FERNET_KEY


def _cipher() -> Fernet:
    if not SESSION_ENCRYPTION_FERNET_KEY:
        raise RuntimeError("SESSION_ENCRYPTION_KEY is not configured.")
    return Fernet(SESSION_ENCRYPTION_FERNET_KEY)


def _encrypt(value: str | None) -> str | None:
    return _cipher().encrypt(value.encode("utf-8")).decode("ascii") if value else None


def _decrypt(value: str | None) -> str | None:
    if not value:
        return None
    try:
        return _cipher().decrypt(value.encode("ascii")).decode("utf-8")
    except (InvalidToken, ValueError, UnicodeError):
        # Legacy plaintext rows are migrated on startup; fail closed if a
        # value is neither valid ciphertext nor recoverable plaintext.
        if value.startswith("gAAAA"):
            raise RuntimeError("Unable to decrypt stored Discord OAuth token.")
        return value

# =========================
# Dashboard Sessions
# =========================
#
# This is the ONE table the dashboard creates and owns for itself — the
# bot's schema (see Raxor/database/models.py) is otherwise untouched;
# db/repositories.py only ever reads/writes tables the bot created. A
# login session doesn't belong in the bot's schema at all (the bot has
# no concept of "a dashboard user is logged in"), so it lives here
# instead, in a table the dashboard itself creates at startup (see
# ensure_schema, called from main.py's lifespan).
#
# Storing sessions in Postgres instead of an in-memory dict means a
# backend restart or a redeploy doesn't silently log everyone out, and
# multiple API workers/processes all see the same sessions instead of
# each having their own — the two concrete problems an in-memory store
# has.

DASHBOARD_SESSIONS_TABLE = """
CREATE TABLE IF NOT EXISTS dashboard_sessions (
    session_id TEXT PRIMARY KEY,

    discord_user_id TEXT NOT NULL,
    username TEXT NOT NULL,
    avatar TEXT,
    is_developer BOOLEAN NOT NULL DEFAULT FALSE,

    access_token TEXT NOT NULL,
    refresh_token TEXT,

    guilds JSONB NOT NULL DEFAULT '[]'::jsonb,
    guilds_cached_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL
);
"""

DASHBOARD_SESSIONS_EXPIRY_INDEX = """
CREATE INDEX IF NOT EXISTS idx_dashboard_sessions_expires_at
ON dashboard_sessions (expires_at);
"""


async def ensure_schema(pool) -> None:
    """Create the dashboard's own session table if it doesn't exist yet,
    and sweep out anything already expired. Safe to call on every
    startup — CREATE TABLE IF NOT EXISTS is a no-op once the table
    exists."""

    await pool.execute(DASHBOARD_SESSIONS_TABLE)
    await pool.execute(DASHBOARD_SESSIONS_EXPIRY_INDEX)
    # Encrypt any legacy plaintext tokens in-place. New writes are always
    # encrypted; this makes the migration safe across existing deployments.
    rows = await pool.fetch("SELECT session_id, access_token, refresh_token FROM dashboard_sessions")
    for row in rows:
        access = row["access_token"]
        refresh = row["refresh_token"]
        if access and not str(access).startswith("gAAAA"):
            await pool.execute(
                "UPDATE dashboard_sessions SET access_token=$2, refresh_token=$3 WHERE session_id=$1",
                row["session_id"], _encrypt(str(access)), _encrypt(str(refresh)) if refresh else None
            )
    await pool.execute("DELETE FROM dashboard_sessions WHERE expires_at <= NOW()")


def _deserialize(row) -> dict:
    session = dict(row)
    guilds = session.get("guilds")
    session["guilds"] = json.loads(guilds) if isinstance(guilds, str) else (guilds or [])
    session["access_token"] = _decrypt(session.get("access_token"))
    session["refresh_token"] = _decrypt(session.get("refresh_token"))
    return session


async def insert_session(
    pool,
    *,
    session_id: str,
    discord_user_id: str,
    username: str,
    avatar: str | None,
    is_developer: bool,
    access_token: str,
    refresh_token: str | None,
    guilds: list[dict],
    expires_at,
) -> None:
    query = """
    INSERT INTO dashboard_sessions (
        session_id, discord_user_id, username, avatar, is_developer,
        access_token, refresh_token, guilds, guilds_cached_at, expires_at
    )
    VALUES ($1, $2, $3, $4, $5, $6, $7, $8::jsonb, NOW(), $9)
    """
    await pool.execute(
        query,
        session_id,
        discord_user_id,
        username,
        avatar,
        is_developer,
        _encrypt(access_token),
        _encrypt(refresh_token),
        json.dumps(guilds),
        expires_at,
    )


async def get_session(pool, session_id: str) -> dict | None:
    """Look up a live, non-expired session."""

    if not session_id:
        return None

    query = "SELECT * FROM dashboard_sessions WHERE session_id = $1 AND expires_at > NOW()"
    row = await pool.fetchrow(query, session_id)
    return _deserialize(row) if row is not None else None


async def update_session_guilds(
    pool,
    session_id: str,
    guilds: list[dict],
    access_token: str,
    refresh_token: str | None,
) -> None:
    """Persist a freshly re-fetched guild permission snapshot (and the
    access/refresh token pair used to get it, in case Discord issued a
    new one on refresh) — see api/dependencies.py's
    ensure_fresh_session_guilds."""

    query = """
    UPDATE dashboard_sessions
    SET guilds = $2::jsonb, guilds_cached_at = NOW(), access_token = $3, refresh_token = $4
    WHERE session_id = $1
    """
    await pool.execute(query, session_id, json.dumps(guilds), _encrypt(access_token), _encrypt(refresh_token))


async def delete_session(pool, session_id: str) -> None:
    """Invalidate a session immediately, e.g. on logout."""

    await pool.execute("DELETE FROM dashboard_sessions WHERE session_id = $1", session_id)
