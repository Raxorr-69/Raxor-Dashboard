import asyncpg

from core.config import DATABASE_URL


# =========================
# Connection Pool
# =========================
#
# This pool points at the same Postgres database the Raxor bot uses. The
# dashboard reads and writes rows in the bot's existing tables — it never
# creates or alters schema. If the bot hasn't run yet (so the tables don't
# exist), start the bot at least once before the dashboard.


async def create_database_pool() -> asyncpg.Pool:
    """Create the shared asyncpg connection pool."""

    return await asyncpg.create_pool(
        dsn=DATABASE_URL,
        min_size=1,
        max_size=10,
    )


async def close_database_pool(pool: asyncpg.Pool) -> None:
    """Close the connection pool."""

    await pool.close()
