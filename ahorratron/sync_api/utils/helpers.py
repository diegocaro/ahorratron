from typing import Sequence, TypeVar

T = TypeVar("T")


def drop_none(x: Sequence[T | None]) -> list[T]:
    return [i for i in x if i is not None]
