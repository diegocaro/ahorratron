import json
from datetime import UTC, datetime

from pydantic import BaseModel

from ahorratron.sync_api.utils.helpers import to_utc


def test_result_default_timezone():
    dt = datetime(2025, 1, 15, 12, 0, 0)

    result = to_utc(dt)

    assert result == datetime(2025, 1, 15, 15, 0, 0, tzinfo=UTC)


def test_result_is_utc_aware():
    dt = datetime(2025, 1, 15, 12, 0, 0)

    result = to_utc(dt, timezone="America/Santiago")

    assert result.tzinfo == UTC


def test_custom_timezone():
    dt = datetime(2025, 1, 15, 12, 0, 0)

    result = to_utc(dt, timezone="UTC")

    assert result == datetime(2025, 1, 15, 12, 0, 0, tzinfo=UTC)


def test_pydantic_model_accepts_utc_datetime():
    class TestPydanticDatetime(BaseModel):
        field: datetime

    dt = datetime(2025, 1, 15, 12, 0, 0, tzinfo=UTC)

    data = TestPydanticDatetime(field=dt)

    json_data = data.model_dump_json()

    parsed = json.loads(json_data)

    assert parsed["field"] == "2025-01-15T12:00:00Z"
