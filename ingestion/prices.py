"""Prices fetcher (yfinance).

Fetches historical daily OHLCV price data for a single ticker, returns a
normalized list of ``PriceBar`` records, and preserves the raw yfinance
response so it can be stored separately (per the project's "always keep the raw
response" rule). The storage module — built later — decides on-disk format.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any

import yfinance as yf

SOURCE = "yfinance"
_DEFAULT_LOOKBACK_DAYS = 365


@dataclass(frozen=True)
class PriceBar:
    """One trading day of normalized price data."""

    ticker: str
    date: date
    open: float
    high: float
    low: float
    close: float
    adj_close: float
    volume: int


@dataclass
class PriceFetchResult:
    """Result of a price fetch: normalized records plus the raw response."""

    source: str
    ticker: str
    fetched_at: datetime
    normalized: list[PriceBar]
    raw: Any


def fetch_prices(
    ticker: str,
    start: date | None = None,
    end: date | None = None,
) -> PriceFetchResult:
    """Fetch daily OHLCV prices for ``ticker`` between ``start`` and ``end``.

    Defaults to roughly the last year if the range is omitted. Raises
    ``ValueError`` for an empty ticker or when no data is returned.
    """
    ticker = ticker.strip().upper()
    if not ticker:
        raise ValueError("ticker must be a non-empty string")

    if end is None:
        end = date.today()
    if start is None:
        start = end - timedelta(days=_DEFAULT_LOOKBACK_DAYS)

    # auto_adjust=False keeps both the raw Close and a separate Adj Close.
    raw = yf.Ticker(ticker).history(start=start, end=end, auto_adjust=False)
    fetched_at = datetime.now(timezone.utc)

    if raw is None or raw.empty:
        raise ValueError(f"no price data returned for ticker {ticker!r}")

    return PriceFetchResult(
        source=SOURCE,
        ticker=ticker,
        fetched_at=fetched_at,
        normalized=_normalize(ticker, raw),
        raw=raw,
    )


def _normalize(ticker: str, frame: Any) -> list[PriceBar]:
    """Turn a yfinance history DataFrame into a list of ``PriceBar`` records."""
    has_adj = "Adj Close" in frame.columns
    bars: list[PriceBar] = []
    for ts, row in frame.iterrows():
        close = float(row["Close"])
        bars.append(
            PriceBar(
                ticker=ticker,
                date=ts.date() if hasattr(ts, "date") else ts,
                open=float(row["Open"]),
                high=float(row["High"]),
                low=float(row["Low"]),
                close=close,
                adj_close=float(row["Adj Close"]) if has_adj else close,
                volume=int(row["Volume"]),
            )
        )
    return bars
