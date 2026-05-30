"""One test proving the prices fetcher normalizes data and keeps the raw response.

yfinance is mocked, so the test is deterministic and runs offline (no network).
"""

from datetime import date, datetime

import pandas as pd

from ingestion import prices
from ingestion.prices import PriceBar, PriceFetchResult


class _FakeTicker:
    """Stand-in for yfinance.Ticker with a fixed two-day history."""

    def __init__(self, symbol):
        self.symbol = symbol

    def history(self, start=None, end=None, auto_adjust=False):
        index = pd.to_datetime(["2024-01-02", "2024-01-03"])
        return pd.DataFrame(
            {
                "Open": [100.0, 102.0],
                "High": [105.0, 106.0],
                "Low": [99.0, 101.0],
                "Close": [104.0, 103.0],
                "Adj Close": [103.5, 102.5],
                "Volume": [1_000_000, 1_200_000],
            },
            index=index,
        )


def test_fetch_prices_normalizes_and_keeps_raw(monkeypatch):
    monkeypatch.setattr(prices.yf, "Ticker", _FakeTicker)

    result = prices.fetch_prices("aapl")  # lower-case on purpose

    # Envelope
    assert isinstance(result, PriceFetchResult)
    assert result.source == "yfinance"
    assert result.ticker == "AAPL"  # normalized to upper-case
    assert isinstance(result.fetched_at, datetime)

    # Normalized records
    assert len(result.normalized) == 2
    first = result.normalized[0]
    assert isinstance(first, PriceBar)
    assert first.ticker == "AAPL"
    assert first.date == date(2024, 1, 2)
    assert (first.open, first.high, first.low, first.close) == (100.0, 105.0, 99.0, 104.0)
    assert first.adj_close == 103.5
    assert first.volume == 1_000_000

    # Raw response preserved untouched
    assert isinstance(result.raw, pd.DataFrame)
    assert list(result.raw.columns) == ["Open", "High", "Low", "Close", "Adj Close", "Volume"]
    assert len(result.raw) == 2
