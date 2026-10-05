import pytest

from app.worker.retry import retry_with_backoff


def test_succeeds_on_first_attempt(monkeypatch):
    monkeypatch.setattr("app.worker.retry.time.sleep", lambda _: None)
    calls = []

    def func():
        calls.append(1)
        return "ok"

    result = retry_with_backoff(func, max_attempts=3, exceptions=(ValueError,))
    assert result == "ok"
    assert len(calls) == 1


def test_retries_then_succeeds(monkeypatch):
    monkeypatch.setattr("app.worker.retry.time.sleep", lambda _: None)
    attempts = {"count": 0}

    def func():
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise ValueError("midlertidig feil")
        return "ok"

    result = retry_with_backoff(func, max_attempts=3, exceptions=(ValueError,))
    assert result == "ok"
    assert attempts["count"] == 3


def test_gives_up_after_max_attempts(monkeypatch):
    monkeypatch.setattr("app.worker.retry.time.sleep", lambda _: None)

    def func():
        raise ValueError("vedvarende feil")

    result = retry_with_backoff(func, max_attempts=3, exceptions=(ValueError,))
    assert result is None


def test_does_not_catch_unlisted_exceptions(monkeypatch):
    monkeypatch.setattr("app.worker.retry.time.sleep", lambda _: None)

    def func():
        raise TypeError("uventet feil")

    with pytest.raises(TypeError):
        retry_with_backoff(func, max_attempts=3, exceptions=(ValueError,))