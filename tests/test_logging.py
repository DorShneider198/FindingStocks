"""One test proving the structured logging convention end-to-end.

Drives the prices fetcher (with yfinance faked) and inspects records via
pytest's ``caplog``: a success emits ``fetch.start`` + ``fetch.ok`` with the
right ``source``/``ticker`` fields; a transient failure emits a ``fetch.error``
ERROR carrying the exception type. No network, deterministic.
"""

import logging

import pandas as pd
import pytest

from ingestion import prices


class _FakeTicker:
    def __init__(self, frame):
        self._frame = frame

    def history(self, **kwargs):
        return self._frame


class _BoomTicker:
    def history(self, **kwargs):
        raise RuntimeError("network down")


def _frame():
    idx = pd.to_datetime(["2024-01-02", "2024-01-03"])
    return pd.DataFrame(
        {
            "Open": [100.0, 102.0],
            "High": [105.0, 106.0],
            "Low": [99.0, 101.0],
            "Close": [104.0, 103.0],
            "Adj Close": [103.5, 102.5],
            "Volume": [1_000_000, 1_200_000],
        },
        index=idx,
    )


def test_fetch_logs_start_and_ok(monkeypatch, caplog):
    monkeypatch.setattr(prices.yf, "Ticker", lambda t: _FakeTicker(_frame()))

    with caplog.at_level(logging.INFO, logger="ingestion.prices"):
        prices.fetch_prices("AAPL")

    messages = [r.getMessage() for r in caplog.records]
    assert any(
        m.startswith("fetch.start") and "source=yfinance" in m and "ticker=AAPL" in m
        for m in messages
    )
    assert any(m.startswith("fetch.ok") and "ticker=AAPL" in m and "rows=2" in m for m in messages)


def test_fetch_logs_error_with_exception_type(monkeypatch, caplog):
    monkeypatch.setattr(prices.yf, "Ticker", lambda t: _BoomTicker())

    with caplog.at_level(logging.ERROR, logger="ingestion.prices"):
        with pytest.raises(RuntimeError):
            prices.fetch_prices("AAPL")

    errors = [r for r in caplog.records if r.levelno == logging.ERROR]
    assert any(
        r.getMessage().startswith("fetch.error") and "error=RuntimeError" in r.getMessage()
        for r in errors
    )
