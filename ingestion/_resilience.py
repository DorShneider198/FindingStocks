"""Retry with exponential backoff + a short-lived in-process cache (stdlib only).

Shared by the yfinance fetchers: ``with_retry`` survives transient failures
(rate limits, network hiccups), and ``TTLCache`` keeps repeated calls for the
same ticker from re-hitting the API within a short window. Both are small and
injectable (``sleep`` / ``clock``) so tests run instantly with no real waiting.
"""

from __future__ import annotations

import random
import time
from typing import Any, Callable, TypeVar

from ingestion import _logging

T = TypeVar("T")

_logger = _logging.get_logger(__name__)


def with_retry(
    fn: Callable[[], T],
    *,
    attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    sleep: Callable[[float], None] = time.sleep,
) -> T:
    """Call ``fn()``; on exception, retry with exponential backoff plus jitter.

    Delays double each attempt (1s, 2s, 4s, ... capped at ``max_delay``), with
    up to 10% random jitter so parallel callers don't retry in lockstep. Each
    failure logs a ``retry.attempt`` event; the final failure re-raises.
    """
    if attempts < 1:
        raise ValueError("attempts must be >= 1")

    for attempt in range(1, attempts + 1):
        try:
            return fn()
        except Exception as exc:
            if attempt == attempts:
                raise
            delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
            delay *= 1 + random.random() * 0.1
            _logging.warning(
                _logger, "retry.attempt", attempt=attempt, error=type(exc).__name__
            )
            sleep(delay)
    raise AssertionError("unreachable")  # for the type checker


class TTLCache:
    """In-process cache with per-entry expiry and a size cap.

    ``get`` returns ``None`` for a missing or expired key. ``put`` evicts the
    oldest entry once ``maxsize`` is exceeded. Not thread-safe — fine for the
    single-threaded fetchers and the Streamlit dashboard.
    """

    def __init__(
        self,
        ttl_seconds: float = 900.0,
        maxsize: int = 128,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._ttl = ttl_seconds
        self._maxsize = maxsize
        self._clock = clock
        self._entries: dict[Any, tuple[float, Any]] = {}

    def get(self, key: Any) -> Any | None:
        entry = self._entries.get(key)
        if entry is None:
            return None
        stored_at, value = entry
        if self._clock() - stored_at >= self._ttl:
            del self._entries[key]
            return None
        return value

    def put(self, key: Any, value: Any) -> None:
        self._entries.pop(key, None)  # re-inserting refreshes insertion order
        self._entries[key] = (self._clock(), value)
        while len(self._entries) > self._maxsize:
            del self._entries[next(iter(self._entries))]

    def clear(self) -> None:
        self._entries.clear()
