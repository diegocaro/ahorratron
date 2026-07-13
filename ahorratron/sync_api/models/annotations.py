from datetime import datetime
from typing import Annotated

from pydantic import AfterValidator, PlainSerializer

from ahorratron.sync_api.utils.helpers import isoformat_millis, to_utc

"""Datetime for Pluggy-compatible response models.

On validation, naive values are interpreted in the configured timezone and aware
values are normalized, so the field is always UTC-aware no matter which connector
produced it. On JSON serialization it emits millisecond precision with a Z suffix
(e.g. `2026-07-13T02:41:28.714Z`); `model_dump()` keeps datetime objects.
"""
datetimeUTC = Annotated[
    datetime,
    AfterValidator(to_utc),
    PlainSerializer(isoformat_millis, return_type=str, when_used="json"),
]
