import random
import time
from collections.abc import Sequence
from datetime import UTC, datetime, tzinfo

from ahorratron.sync_api.config import DEFAULT_TIMEZONE


def drop_none[T](x: Sequence[T | None]) -> list[T]:
    return [i for i in x if i is not None]


def disambiguate_ids(ids: Sequence[str]) -> list[str]:
    """Agrega un contador a los ids repetidos para hacerlos únicos.

    Cuando el banco no entrega un identificador, el id se arma con los campos
    del movimiento. Dos compras idénticas (mismo comercio, día y monto) quedan
    con el mismo id, así que se numeran las repeticiones en el orden de la
    lista: la primera conserva el id original y las siguientes reciben el
    sufijo `#2`, `#3`, etc.

    Se devuelve la lista en el mismo orden que entró.
    """
    counts = {i: 0 for i in ids}
    unique = []
    for i in ids:
        counts[i] += 1
        n = counts[i]
        unique.append(i if n == 1 else f"{i}#{n}")
    return unique


def utcnow():
    """Return the current UTC time as a timezone-aware datetime object."""

    return datetime.now(UTC)


def to_utc(dt: datetime, tz: tzinfo = DEFAULT_TIMEZONE) -> datetime:
    """Interpret a naive datetime as being in `tz` and convert it to UTC."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=tz)

    return dt.astimezone(UTC)


def isoformat_millis(dt: datetime) -> str:
    """
    Create an ISO 8601 string with millisecond precision
    and a Z suffix for UTC datetimes.
    """

    return dt.isoformat(timespec="milliseconds").replace("+00:00", "Z")


def random_wait(min_seconds: float = 1, max_seconds: float = 3) -> None:
    time.sleep(random.uniform(min_seconds, max_seconds))
