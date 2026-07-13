from datetime import datetime
from typing import Annotated

from pydantic import AfterValidator, PlainSerializer

from ahorratron.sync_api.utils.helpers import to_utc


def isoformat_millis(dt: datetime) -> str:
    """Pydantic's default datetime serializer emits microsecond precision (or none at
    all when it's exactly zero); this forces millisecond precision instead."""

    return dt.isoformat(timespec="milliseconds").replace("+00:00", "Z")


UTCDatetime = Annotated[
    datetime,
    AfterValidator(to_utc),
    PlainSerializer(isoformat_millis, return_type=str, when_used="json"),
]
"""Datetime for Pluggy-compatible response models.

On validation, naive values are interpreted in the configured timezone and aware
values are normalized, so the field is always UTC-aware no matter which connector
produced it. On JSON serialization it emits millisecond precision with a Z suffix
(e.g. `2026-07-13T02:41:28.714Z`); `model_dump()` keeps datetime objects.
"""
