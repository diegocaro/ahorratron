from collections.abc import Sequence
from datetime import UTC, datetime


def drop_none[T](x: Sequence[T | None]) -> list[T]:
    return [i for i in x if i is not None]


def utcnow():
    """Return the current UTC time as a timezone-aware datetime object."""

    return datetime.now(UTC)
