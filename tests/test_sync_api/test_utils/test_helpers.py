import zoneinfo
from datetime import UTC, datetime

from ahorratron.sync_api.utils.helpers import to_utc


def test_default_timezone():
    dt = datetime(2025, 1, 15, 12, 0, 0)

    result = to_utc(dt)

    assert result == datetime(2025, 1, 15, 15, 0, 0, tzinfo=UTC)


def test_custom_timezone():
    dt = datetime(2025, 1, 15, 12, 0, 0)

    result = to_utc(dt, tz=zoneinfo.ZoneInfo("America/Santiago"))

    assert result.tzinfo == UTC


def test_utc_timezone():
    dt = datetime(2025, 1, 15, 12, 0, 0)

    result = to_utc(dt, tz=UTC)

    assert result == datetime(2025, 1, 15, 12, 0, 0, tzinfo=UTC)
