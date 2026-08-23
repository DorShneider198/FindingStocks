"""One test proving retry backs off then succeeds, and the TTL cache serves hits.

Sleep and clock are injected, so the test runs instantly with no real waiting.
"""

import pytest

from ingestion._resilience import TTLCache, with_retry


def test_with_retry_backs_off_and_ttl_cache_serves_and_expires():
    # --- with_retry: two failures, then success, with doubling jittered delays.
    calls = {"n": 0}
    delays: list[float] = []

    def flaky():
        calls["n"] += 1
        if calls["n"] < 3:
            raise ConnectionError("transient")
        return "payload"

    assert with_retry(flaky, attempts=3, base_delay=1.0, sleep=delays.append) == "payload"
    assert calls["n"] == 3
    assert len(delays) == 2  # no sleep after the final success
    assert 1.0 <= delays[0] <= 1.1  # base delay + up to 10% jitter
    assert 2.0 <= delays[1] <= 2.2  # doubled

    # Exhausted attempts re-raise the last error.
    def always_fails():
        raise ConnectionError("still down")

    with pytest.raises(ConnectionError):
        with_retry(always_fails, attempts=2, sleep=delays.append)

    # --- TTLCache: hit within ttl, miss after expiry, oldest evicted at maxsize.
    now = {"t": 0.0}
    cache = TTLCache(ttl_seconds=10.0, maxsize=2, clock=lambda: now["t"])

    cache.put("AAPL", "cached-result")
    assert cache.get("AAPL") == "cached-result"

    now["t"] = 10.0  # ttl reached -> expired
    assert cache.get("AAPL") is None

    cache.put("A", 1)
    cache.put("B", 2)
    cache.put("C", 3)  # over maxsize -> "A" (oldest) evicted
    assert cache.get("A") is None
    assert cache.get("B") == 2
    assert cache.get("C") == 3
