from collections.abc import Sequence


def drop_none[T](x: Sequence[T | None]) -> list[T]:
    return [i for i in x if i is not None]
