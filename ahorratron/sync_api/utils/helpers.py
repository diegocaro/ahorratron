from collections.abc import Sequence
from datetime import UTC, datetime, tzinfo

from ahorratron.sync_api.config import DEFAULT_TIMEZONE


def drop_none[T](x: Sequence[T | None]) -> list[T]:
    return [i for i in x if i is not None]


def utcnow():
    """Return the current UTC time as a timezone-aware datetime object."""

    return datetime.now(UTC)


def to_utc(dt: datetime, tz: tzinfo = DEFAULT_TIMEZONE) -> datetime:
    """Interpret a naive datetime as being in `tz` and convert it to UTC."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=tz)

    return dt.astimezone(UTC)
