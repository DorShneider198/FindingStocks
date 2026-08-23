"""Fundamentals fetcher (yfinance).

Fetches a point-in-time snapshot of curated fundamental metrics for a single
ticker from yfinance's ``.info`` dict, returns a normalized
``FundamentalsSnapshot``, and preserves the full raw ``.info`` dict for separate
storage. Unlike prices (a time series), this is one snapshot per fetch.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Any

import yfinance as yf

from ingestion import _logging
from ingestion._resilience import TTLCache, with_retry

SOURCE = "yfinance"
_logger = _logging.get_logger(__name__)

# Successful fetches are cached for 15 minutes so repeated calls for the same
# ticker (e.g. dashboard reruns) don't re-hit the API.
_cache = TTLCache()


@dataclass(frozen=True)
class FundamentalsSnapshot:
    """A point-in-time snapshot of curated fundamental metrics.

    Every metric is optional: yfinance's ``.info`` coverage varies by ticker.
    """

    ticker: str
    as_of: date
    name: str | None
    sector: str | None
    industry: str | None
    market_cap: float | None
    trailing_pe: float | None
    forward_pe: float | None
    price_to_book: float | None
    dividend_yield: float | None
    profit_margin: float | None


@dataclass
class FundamentalsFetchResult:
    """Result of a fundamentals fetch: normalized snapshot plus the raw response."""

    source: str
    ticker: str
    fetched_at: datetime
    normalized: FundamentalsSnapshot
    raw: Any


def fetch_fundamentals(ticker: str) -> FundamentalsFetchResult:
    """Fetch a fundamentals snapshot for ``ticker``.

    Raises ``ValueError`` for an empty ticker or when yfinance returns no usable
    ``.info`` data.
    """
    ticker = ticker.strip().upper()
    if not ticker:
        raise ValueError("ticker must be a non-empty string")

    cached = _cache.get(ticker)
    if cached is not None:
        # fetched_at stays the original fetch time — honest about data age.
        _logging.info(_logger, "fetch.cache_hit", source=SOURCE, ticker=ticker)
        return cached

    _logging.info(_logger, "fetch.start", source=SOURCE, ticker=ticker)

    try:
        info = with_retry(lambda: yf.Ticker(ticker).info)
    except Exception as exc:
        _logging.error(_logger, "fetch.error", source=SOURCE, ticker=ticker, error=type(exc).__name__)
        raise
    fetched_at = datetime.now(timezone.utc)

    if not info:
        _logging.warning(_logger, "fetch.empty", source=SOURCE, ticker=ticker)
        raise ValueError(f"no fundamentals data returned for ticker {ticker!r}")

    _logging.info(_logger, "fetch.ok", source=SOURCE, ticker=ticker, fields=len(info))
    result = FundamentalsFetchResult(
        source=SOURCE,
        ticker=ticker,
        fetched_at=fetched_at,
        normalized=_normalize(ticker, fetched_at.date(), info),
        raw=info,
    )
    _cache.put(ticker, result)
    return result


def _normalize(ticker: str, as_of: date, info: dict) -> FundamentalsSnapshot:
    """Map yfinance ``.info`` keys to a curated ``FundamentalsSnapshot``."""
    return FundamentalsSnapshot(
        ticker=ticker,
        as_of=as_of,
        name=info.get("longName") or info.get("shortName"),
        sector=info.get("sector"),
        industry=info.get("industry"),
        market_cap=info.get("marketCap"),
        trailing_pe=info.get("trailingPE"),
        forward_pe=info.get("forwardPE"),
        price_to_book=info.get("priceToBook"),
        dividend_yield=info.get("dividendYield"),
        profit_margin=info.get("profitMargins"),
    )
