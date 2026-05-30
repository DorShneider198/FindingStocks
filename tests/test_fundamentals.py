"""One test proving the fundamentals fetcher maps .info to a snapshot and keeps raw.

yfinance is mocked, so the test is deterministic and runs offline (no network).
"""

from datetime import datetime

from ingestion import fundamentals
from ingestion.fundamentals import FundamentalsFetchResult, FundamentalsSnapshot


class _FakeTicker:
    """Stand-in for yfinance.Ticker exposing a fixed ``.info`` dict."""

    def __init__(self, symbol):
        self.symbol = symbol

    @property
    def info(self):
        return {
            "longName": "Apple Inc.",
            "sector": "Technology",
            "industry": "Consumer Electronics",
            "marketCap": 3_000_000_000_000,
            "trailingPE": 30.5,
            "forwardPE": 28.0,
            "priceToBook": 45.2,
            "dividendYield": 0.005,
            # profitMargins intentionally omitted -> should map to None
        }


def test_fetch_fundamentals_maps_snapshot_and_keeps_raw(monkeypatch):
    monkeypatch.setattr(fundamentals.yf, "Ticker", _FakeTicker)

    result = fundamentals.fetch_fundamentals("aapl")  # lower-case on purpose

    # Envelope
    assert isinstance(result, FundamentalsFetchResult)
    assert result.source == "yfinance"
    assert result.ticker == "AAPL"  # normalized to upper-case
    assert isinstance(result.fetched_at, datetime)

    # Normalized snapshot
    snap = result.normalized
    assert isinstance(snap, FundamentalsSnapshot)
    assert snap.ticker == "AAPL"
    assert snap.as_of == result.fetched_at.date()
    assert snap.name == "Apple Inc."
    assert snap.sector == "Technology"
    assert snap.industry == "Consumer Electronics"
    assert snap.market_cap == 3_000_000_000_000
    assert snap.trailing_pe == 30.5
    assert snap.forward_pe == 28.0
    assert snap.price_to_book == 45.2
    assert snap.dividend_yield == 0.005
    assert snap.profit_margin is None  # missing field maps to None

    # Raw response preserved (the full .info dict)
    assert isinstance(result.raw, dict)
    assert result.raw["longName"] == "Apple Inc."
