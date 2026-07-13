import zoneinfo
from datetime import UTC, datetime

from pydantic import BaseModel

from ahorratron.sync_api.models.annotations import datetimeUTC


class Model(BaseModel):
    dt: datetimeUTC


def test_naive_datetime_uses_default_timezone():
    model = Model(dt=datetime(2025, 1, 15, 12, 0, 0))

    assert model.dt == datetime(2025, 1, 15, 15, 0, 0, tzinfo=UTC)


def test_aware_datetime_is_normalized_to_utc():
    dt = datetime(2025, 1, 15, 12, 0, 0, tzinfo=zoneinfo.ZoneInfo("America/Santiago"))

    model = Model(dt=dt)

    assert model.dt == datetime(2025, 1, 15, 15, 0, 0, tzinfo=UTC)


def test_utc_datetime_is_unchanged():
    dt = datetime(2025, 1, 15, 12, 0, 0, tzinfo=UTC)

    model = Model(dt=dt)

    assert model.dt == dt


def test_json_serialization_uses_millis_and_z_suffix():
    model = Model(dt=datetime(2025, 1, 15, 12, 0, 0, 123456, tzinfo=UTC))

    assert model.model_dump_json() == '{"dt":"2025-01-15T12:00:00.123Z"}'


def test_model_dump_keeps_datetime_object():
    model = Model(dt=datetime(2025, 1, 15, 12, 0, 0, tzinfo=UTC))

    assert model.model_dump() == {"dt": datetime(2025, 1, 15, 12, 0, 0, tzinfo=UTC)}
