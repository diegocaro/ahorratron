import zoneinfo
from collections.abc import Sequence
from datetime import UTC, datetime

from ahorratron.sync_api.config import TZ


def drop_none[T](x: Sequence[T | None]) -> list[T]:
    return [i for i in x if i is not None]


def utcnow():
    """Return the current UTC time as a timezone-aware datetime object."""

    return datetime.now(UTC)


def to_utc(dt: datetime, timezone: str = TZ) -> datetime:
    """Interpret a naive datetime as a timezone-aware datetime and convert it to UTC."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=zoneinfo.ZoneInfo(timezone))

    return dt.astimezone(UTC)
