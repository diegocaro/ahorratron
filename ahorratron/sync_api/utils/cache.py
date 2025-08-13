from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Callable

from fastapi import BackgroundTasks


@dataclass
class _Entry:
    value: Any
    timestamp: datetime


class BackgroundRefreshCache:
    # TODO: add a max size limit
    def __init__(self, ttl_seconds: int = 300):
        self.ttl_seconds = ttl_seconds
        self._cache: dict[Any, _Entry] = {}

    def _now(self) -> datetime:
        return datetime.now()

    def _is_stale(self, entry: _Entry) -> bool:
        return (self._now() - entry.timestamp) > timedelta(seconds=self.ttl_seconds)

    def _set(self, key: Any, value: Any):
        entry = _Entry(value=value, timestamp=self._now())
        self._cache[key] = entry

    def get_or_fetch(
        self,
        key: Any,
        fetch_fn: Callable,
        background_tasks: BackgroundTasks,
        *args,
        **kwargs,
    ):
        """
        Return cached value if fresh.
        If stale, return old value but refresh in background.
        If missing, fetch immediately.
        """
        entry = self._cache.get(key)
        if entry is not None:
            if self._is_stale(entry):
                background_tasks.add_task(self._refresh, key, fetch_fn, *args, **kwargs)
            return self._cache[key].value
        return self._refresh(key, fetch_fn, *args, **kwargs)

    def _refresh(self, key: Any, fetch_fn: Callable, *args, **kwargs):
        value = fetch_fn(*args, **kwargs)
        self._set(key, value)
        return value


def cache_with_background(cache: BackgroundRefreshCache):
    def decorator(func: Callable):
        def wrapper(self, *args, **kwargs):
            if not hasattr(self, "background_tasks") or self.background_tasks is None:
                raise AttributeError(
                    "Object must have 'background_tasks' attribute for caching with background refresh."
                )
            # key = (func.__name__,) + args + tuple(sorted(kwargs.items()))
            key = args + tuple(sorted(kwargs.items()))
            # Check that all elements in key are hashable (immutable)
            for element in key:
                try:
                    hash(element)
                except TypeError:
                    raise TypeError(
                        f"Cache key argument '{element}' of type '{type(element).__name__}' is not hashable. All cache key arguments must be immutable and hashable."
                    )
            return cache.get_or_fetch(
                key=key,
                fetch_fn=lambda: func(self, *args, **kwargs),
                background_tasks=self.background_tasks,
            )

        return wrapper

    return decorator
