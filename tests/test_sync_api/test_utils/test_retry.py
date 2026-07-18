import httpx
import pytest

from ahorratron.sync_api.core.exceptions import (
    InternalServerError,
    LoginError,
    SessionExpired,
)
from ahorratron.sync_api.utils import retry
from ahorratron.sync_api.utils.retry import retry_on_error


@pytest.fixture
def sleep_calls(monkeypatch):
    calls: list[float] = []
    monkeypatch.setattr(retry.time, "sleep", calls.append)
    return calls


def make_flaky(failures: list[Exception], result: str = "ok"):
    """Return a decoratable function that raises each exception in order,
    then returns `result`. Also tracks the number of calls."""
    calls = {"count": 0}

    def func():
        calls["count"] += 1
        if failures:
            raise failures.pop(0)
        return result

    return func, calls


def test_success_on_first_attempt(sleep_calls):
    func, calls = make_flaky([])

    assert retry_on_error()(func)() == "ok"
    assert calls["count"] == 1
    assert sleep_calls == []


def test_passes_args_and_kwargs():
    @retry_on_error()
    def add(a, b, *, c=0):
        return a + b + c

    assert add(1, 2, c=3) == 6


def test_preserves_function_metadata():
    @retry_on_error()
    def my_func():
        """docstring"""

    assert my_func.__name__ == "my_func"
    assert my_func.__doc__ == "docstring"


def test_retries_internal_server_error(sleep_calls):
    func, calls = make_flaky([InternalServerError("500")])

    assert retry_on_error()(func)() == "ok"
    assert calls["count"] == 2


def test_retries_timeout(sleep_calls):
    func, calls = make_flaky([httpx.ReadTimeout("timed out")])

    assert retry_on_error()(func)() == "ok"
    assert calls["count"] == 2


def test_raises_after_attempts_exhausted(sleep_calls):
    func, calls = make_flaky([InternalServerError(str(i)) for i in range(3)])

    with pytest.raises(InternalServerError):
        retry_on_error(attempts=3)(func)()
    assert calls["count"] == 3


def test_no_sleep_after_last_attempt(sleep_calls):
    func, _ = make_flaky([InternalServerError(str(i)) for i in range(3)])

    with pytest.raises(InternalServerError):
        retry_on_error(attempts=3)(func)()
    assert len(sleep_calls) == 2


def test_linear_backoff(sleep_calls):
    func, _ = make_flaky([InternalServerError(str(i)) for i in range(3)])

    with pytest.raises(InternalServerError):
        retry_on_error(attempts=3, backoff_seconds=0.5)(func)()
    assert sleep_calls == [0.5, 1.0]


def test_session_expired_retried_once(sleep_calls):
    func, calls = make_flaky([SessionExpired()])

    assert retry_on_error()(func)() == "ok"
    assert calls["count"] == 2


def test_session_expired_does_not_sleep(sleep_calls):
    func, _ = make_flaky([SessionExpired()])

    retry_on_error()(func)()
    assert sleep_calls == []


def test_second_session_expired_raises(sleep_calls):
    func, calls = make_flaky([SessionExpired(), SessionExpired()])

    with pytest.raises(SessionExpired):
        retry_on_error(attempts=5)(func)()
    assert calls["count"] == 2


def test_session_expired_on_last_attempt_raises(sleep_calls):
    func, calls = make_flaky(
        [InternalServerError("500"), InternalServerError("500"), SessionExpired()]
    )

    with pytest.raises(SessionExpired):
        retry_on_error(attempts=3)(func)()
    assert calls["count"] == 3


def test_session_expired_then_server_errors_still_retried(sleep_calls):
    func, calls = make_flaky([SessionExpired(), InternalServerError("500")])

    assert retry_on_error(attempts=3)(func)() == "ok"
    assert calls["count"] == 3


def test_login_error_not_retried(sleep_calls):
    func, calls = make_flaky([LoginError("bad credentials")])

    with pytest.raises(LoginError):
        retry_on_error()(func)()
    assert calls["count"] == 1


def test_unrelated_exception_not_retried(sleep_calls):
    func, calls = make_flaky([ValueError("boom")])

    with pytest.raises(ValueError):
        retry_on_error()(func)()
    assert calls["count"] == 1
