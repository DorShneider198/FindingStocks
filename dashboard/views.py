"""Data layer for the dashboard (no streamlit import — fully testable offline).

``load_ticker_view`` reads whatever is stored for a ticker; it never fetches.
``ingest_ticker`` runs the wired ingest functions for one ticker, isolating
failures per source so one broken source (e.g. missing Reddit credentials)
never blocks the others. The Streamlit app in ``app.py`` is a thin UI over
these two functions.
"""

from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass
from datetime import date, timedelta

from ingestion.fundamentals import FundamentalsSnapshot
from ingestion.pipeline import ingest_fundamentals, ingest_prices, ingest_reddit
from ingestion.prices import PriceBar
from ingestion.reddit import RedditMention
from storage import store

_PRICE_LOOKBACK_DAYS = 365
_MAX_MENTIONS = 50

REDDIT_NOT_CONFIGURED = (
    "skipped: Reddit not configured (set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET)"
)


@dataclass
class TickerView:
    """Everything stored for one ticker, shaped for display."""

    ticker: str
    fundamentals: FundamentalsSnapshot | None
    price_bars: list[PriceBar]        # last year, oldest first (chart-ready)
    mentions: list[RedditMention]     # newest first, capped

    @property
    def is_empty(self) -> bool:
        return self.fundamentals is None and not self.price_bars and not self.mentions


def reddit_configured() -> bool:
    """True when Reddit credentials are present in the environment."""
    return bool(os.environ.get("REDDIT_CLIENT_ID") and os.environ.get("REDDIT_CLIENT_SECRET"))


def load_ticker_view(conn: sqlite3.Connection, ticker: str) -> TickerView:
    """Read the stored data for ``ticker``. Never hits the network."""
    ticker = ticker.strip().upper()
    start = date.today() - timedelta(days=_PRICE_LOOKBACK_DAYS)

    mentions = store.load_reddit_mentions(conn, ticker)  # oldest first
    mentions.reverse()

    return TickerView(
        ticker=ticker,
        fundamentals=store.load_fundamentals(conn, ticker),
        price_bars=store.load_price_bars(conn, ticker, start=start),
        mentions=mentions[:_MAX_MENTIONS],
    )


def ingest_ticker(conn: sqlite3.Connection, ticker: str) -> dict[str, str]:
    """Ingest all wired sources for ``ticker``; report per-source outcomes.

    Returns ``{"prices": ..., "fundamentals": ..., "reddit": ...}`` where each
    value is ``"ok: N rows"``, ``"error: <type>"``, or a skipped message.
    Reddit is skipped up front when credentials are unset — a plain message,
    never an exception.
    """
    results: dict[str, str] = {}

    for name, ingest in (("prices", ingest_prices), ("fundamentals", ingest_fundamentals)):
        try:
            summary = ingest(conn, ticker)
            results[name] = f"ok: {summary.rows_written} rows"
        except Exception as exc:
            results[name] = f"error: {type(exc).__name__}"

    if not reddit_configured():
        results["reddit"] = REDDIT_NOT_CONFIGURED
    else:
        try:
            summary = ingest_reddit(conn, ticker)
            results["reddit"] = f"ok: {summary.rows_written} rows"
        except Exception as exc:
            results["reddit"] = f"error: {type(exc).__name__}"

    return results
