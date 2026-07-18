import functools
import logging
import time
from collections.abc import Callable

import httpx

from ahorratron.sync_api.core.exceptions import InternalServerError, SessionExpired

logger = logging.getLogger(__name__)


def retry_on_error[**P, R](
    attempts: int = 3, backoff_seconds: float = 1.0
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Retry on SessionExpired, InternalServerError or timeouts.

    SessionExpired is retried at most once (a second 302 after a fresh login
    means something is structurally wrong); LoginError is not caught, so a
    failed re-login aborts. Only safe on read-only calls.
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            relogin_done = False
            for attempt in range(1, attempts + 1):
                is_exhausted = attempt == attempts
                wait = backoff_seconds * attempt
                try:
                    return func(*args, **kwargs)
                except SessionExpired:
                    if relogin_done or is_exhausted:
                        raise
                    relogin_done = True
                    logger.info(
                        "Session expired, retrying %s with a fresh login",
                        func.__name__,
                    )
                except (InternalServerError, httpx.TimeoutException) as e:
                    if is_exhausted:
                        raise
                    logger.warning(
                        "%s failed (%s), retrying in %.1fs (attempt %d/%d)",
                        func.__name__,
                        e,
                        wait,
                        attempt + 1,
                        attempts,
                    )
                    time.sleep(wait)
            raise AssertionError("unreachable: last attempt returns or raises")

        return wrapper

    return decorator
