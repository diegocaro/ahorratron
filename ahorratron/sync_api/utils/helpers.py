import zoneinfo
from collections.abc import Sequence
from datetime import UTC, datetime

from ahorratron.sync_api.utils.constants import DEFAULT_TIMEZONE


def drop_none[T](x: Sequence[T | None]) -> list[T]:
    return [i for i in x if i is not None]


def utcnow():
    """Return the current UTC time as a timezone-aware datetime object."""

    return datetime.now(UTC)


def to_utc(dt: datetime, timezone: str = DEFAULT_TIMEZONE) -> datetime:
    """Interpret a naive datetime as the default local time and convert it to UTC."""

    tzinfo = zoneinfo.ZoneInfo(timezone)
    return dt.replace(tzinfo=tzinfo).astimezone(UTC)
