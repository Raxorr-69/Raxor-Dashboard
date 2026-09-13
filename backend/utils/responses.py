from typing import Any


def paginated(items: list[Any], *, total: int, limit: int, offset: int) -> dict:
    """Standard pagination envelope used by every list endpoint."""

    return {
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": offset + len(items) < total,
    }


def row_to_dict(row) -> dict | None:
    """Convert an asyncpg Record (or None) to a plain dict."""

    return dict(row) if row is not None else None


def rows_to_dicts(rows) -> list[dict]:
    return [dict(row) for row in rows]
