from datetime import datetime
from typing import Any

from pydantic import BaseModel, SerializerFunctionWrapHandler, model_serializer


def isoformat_millis(dt: datetime) -> str:
    """Pydantic's default datetime serializer emits microsecond precision (or none at
    all when it's exactly zero); this forces millisecond precision instead."""

    return dt.isoformat(timespec="milliseconds").replace("+00:00", "Z")


class APIBaseModel(BaseModel):
    """Base for Pluggy-compatible response models: serializes every datetime field
    to millisecond precision (e.g. `2026-07-13T02:41:28.714Z`)."""

    @model_serializer(mode="wrap")
    def _serialize_datetimes(self, handler: SerializerFunctionWrapHandler) -> dict[str, Any]:
        data = handler(self)
        for name, value in self:
            if isinstance(value, datetime):
                data[name] = isoformat_millis(value)
        return data
