"""Ingestion orchestration: fetch a source and persist it in one call.

Keeps the fetch->store wiring in one place and owns any source-specific
serialization (e.g. turning a pandas DataFrame into JSON), so the storage layer
stays source-agnostic. Future fetchers add ``ingest_reddit``, ``ingest_news``,
etc. alongside ``ingest_prices``.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import date

from ingestion import _logging
from ingestion.fundamentals import fetch_fundamentals
from ingestion.prices import fetch_prices
from ingestion.reddit import fetch_reddit_mentions
from storage import store

_logger = _logging.get_logger(__name__)


@dataclass
class IngestSummary:
    """Outcome of ingesting one source for one ticker."""

    ticker: str
    rows_written: int
    raw_id: int


def ingest_prices(
    conn: sqlite3.Connection,
    ticker: str,
    start: date | None = None,
    end: date | None = None,
) -> IngestSummary:
    """Fetch prices for ``ticker`` and persist normalized bars + the raw response.

    The raw DataFrame is serialized here (``to_json``) so ``storage`` never needs
    to know about pandas.
    """
    _logging.info(_logger, "ingest.start", source="yfinance", ticker=ticker.strip().upper())
    try:
        result = fetch_prices(ticker, start, end)
        rows_written = store.save_price_bars(conn, result.normalized)
        raw_id = store.save_raw(
            conn,
            source=result.source,
            ticker=result.ticker,
            fetched_at=result.fetched_at,
            payload=result.raw.to_json(orient="split"),
        )
    except Exception as exc:
        _logging.error(_logger, "ingest.error", source="yfinance", ticker=ticker.strip().upper(), error=type(exc).__name__)
        raise
    _logging.info(_logger, "ingest.ok", source=result.source, ticker=result.ticker, rows=rows_written, raw_id=raw_id)
    return IngestSummary(ticker=result.ticker, rows_written=rows_written, raw_id=raw_id)


def ingest_fundamentals(conn: sqlite3.Connection, ticker: str) -> IngestSummary:
    """Fetch a fundamentals snapshot for ``ticker`` and persist it + the raw response.

    The raw ``.info`` dict is JSON-serialized here (``default=str`` guards any
    stray non-serializable values) so ``storage`` stays source-agnostic.
    """
    _logging.info(_logger, "ingest.start", source="yfinance", ticker=ticker.strip().upper())
    try:
        result = fetch_fundamentals(ticker)
        rows_written = store.save_fundamentals(conn, result.normalized)
        raw_id = store.save_raw(
            conn,
            source=result.source,
            ticker=result.ticker,
            fetched_at=result.fetched_at,
            payload=json.dumps(result.raw, default=str),
        )
    except Exception as exc:
        _logging.error(_logger, "ingest.error", source="yfinance", ticker=ticker.strip().upper(), error=type(exc).__name__)
        raise
    _logging.info(_logger, "ingest.ok", source=result.source, ticker=result.ticker, rows=rows_written, raw_id=raw_id)
    return IngestSummary(ticker=result.ticker, rows_written=rows_written, raw_id=raw_id)


def ingest_reddit(
    conn: sqlite3.Connection,
    ticker: str,
    subreddits: tuple[str, ...] | None = None,
    limit: int = 50,
    time_filter: str = "month",
    reddit=None,
) -> IngestSummary:
    """Fetch Reddit mentions for ``ticker`` and persist them + the raw post list.

    ``reddit`` is an injectable PRAW client (for tests/offline). The raw list of
    post dicts is JSON-serialized here so ``storage`` stays source-agnostic.
    """
    _logging.info(_logger, "ingest.start", source="reddit", ticker=ticker.strip().upper())
    try:
        result = fetch_reddit_mentions(
            ticker, subreddits=subreddits, limit=limit, time_filter=time_filter, reddit=reddit
        )
        rows_written = store.save_reddit_mentions(conn, result.normalized)
        raw_id = store.save_raw(
            conn,
            source=result.source,
            ticker=result.ticker,
            fetched_at=result.fetched_at,
            payload=json.dumps(result.raw, default=str),
        )
    except Exception as exc:
        _logging.error(_logger, "ingest.error", source="reddit", ticker=ticker.strip().upper(), error=type(exc).__name__)
        raise
    _logging.info(_logger, "ingest.ok", source=result.source, ticker=result.ticker, rows=rows_written, raw_id=raw_id)
    return IngestSummary(ticker=result.ticker, rows_written=rows_written, raw_id=raw_id)
