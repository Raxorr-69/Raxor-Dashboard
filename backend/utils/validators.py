import datetime


class InvalidSnowflakeError(ValueError):
    """Raised when a Discord id (snowflake) string isn't actually numeric."""


def parse_snowflake(value: str) -> int:
    """Parse a Discord id from a URL/body string into an int.

    Discord ids are 64-bit and JavaScript can't represent them precisely
    as numbers, so the frontend always sends/receives them as strings —
    this is where they become ints for the database layer.
    """

    if not value.isdigit():
        raise InvalidSnowflakeError(f"'{value}' is not a valid Discord id.")

    return int(value)


def get_week_start_date(reference: datetime.date | None = None) -> datetime.date:
    """The Monday on or before `reference` (defaults to today)."""

    reference = reference or datetime.date.today()
    return reference - datetime.timedelta(days=reference.weekday())


def get_month_start_date(reference: datetime.date | None = None) -> datetime.date:
    reference = reference or datetime.date.today()
    return reference.replace(day=1)


def resolve_period_range(period: str) -> tuple[datetime.date, datetime.date]:
    """Resolve a period keyword ("weekly" | "monthly" | "all") into a
    [start_date, end_date) range for statistics queries."""

    today = datetime.date.today()
    tomorrow = today + datetime.timedelta(days=1)

    if period == "weekly":
        return get_week_start_date(today), tomorrow

    if period == "monthly":
        return get_month_start_date(today), tomorrow

    if period == "all":
        # A wide-open range; callers with an "all" period should prefer
        # the all-time repository functions instead of this range.
        return datetime.date(2000, 1, 1), tomorrow

    raise ValueError(f"Invalid period: {period}")


def daterange_days(start_date: datetime.date, end_date: datetime.date) -> int:
    return max((end_date - start_date).days, 0)
