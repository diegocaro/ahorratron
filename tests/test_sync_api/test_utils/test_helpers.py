import zoneinfo
from datetime import UTC, datetime

from ahorratron.sync_api.utils.helpers import disambiguate_ids, to_utc


def test_default_timezone():
    dt = datetime(2025, 1, 15, 12, 0, 0)  # noqa: DTZ001 -- naive input is what to_utc interprets

    result = to_utc(dt)

    assert result == datetime(2025, 1, 15, 15, 0, 0, tzinfo=UTC)


def test_custom_timezone():
    dt = datetime(2025, 1, 15, 12, 0, 0)  # noqa: DTZ001 -- naive input is what to_utc interprets

    result = to_utc(dt, tz=zoneinfo.ZoneInfo("America/Santiago"))

    assert result.tzinfo == UTC


def test_utc_timezone():
    dt = datetime(2025, 1, 15, 12, 0, 0)  # noqa: DTZ001 -- naive input is what to_utc interprets

    result = to_utc(dt, tz=UTC)

    assert result == datetime(2025, 1, 15, 12, 0, 0, tzinfo=UTC)


def test_disambiguate_ids_keeps_unique_ids_untouched():
    assert disambiguate_ids(["a", "b", "c"]) == ["a", "b", "c"]


def test_disambiguate_ids_numbers_repetitions_in_order():
    assert disambiguate_ids(["a", "b", "a", "a", "b"]) == [
        "a",
        "b",
        "a#2",
        "a#3",
        "b#2",
    ]


def test_disambiguate_ids_empty():
    assert disambiguate_ids([]) == []
