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
from ingestion.edgar import fetch_filings
from ingestion.filing_docs import fetch_filing_sections
from ingestion.fundamentals import fetch_fundamentals
from ingestion.news import fetch_news
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


def ingest_news(
    conn: sqlite3.Connection,
    ticker: str,
    start: date | None = None,
    end: date | None = None,
    http_get=None,
) -> IngestSummary:
    """Fetch company news for ``ticker`` and persist articles + the raw JSON list.

    ``http_get`` is an injectable transport (for tests/offline). The raw list is
    JSON-serialized here so ``storage`` stays source-agnostic.
    """
    _logging.info(_logger, "ingest.start", source="finnhub", ticker=ticker.strip().upper())
    try:
        result = fetch_news(ticker, start=start, end=end, http_get=http_get)
        rows_written = store.save_news_articles(conn, result.normalized)
        raw_id = store.save_raw(
            conn,
            source=result.source,
            ticker=result.ticker,
            fetched_at=result.fetched_at,
            payload=json.dumps(result.raw, default=str),
        )
    except Exception as exc:
        _logging.error(_logger, "ingest.error", source="finnhub", ticker=ticker.strip().upper(), error=type(exc).__name__)
        raise
    _logging.info(_logger, "ingest.ok", source=result.source, ticker=result.ticker, rows=rows_written, raw_id=raw_id)
    return IngestSummary(ticker=result.ticker, rows_written=rows_written, raw_id=raw_id)


def ingest_filings(
    conn: sqlite3.Connection,
    ticker: str,
    forms: tuple[str, ...] | None = None,
    limit: int = 20,
    get_json=None,
) -> IngestSummary:
    """Fetch SEC filing metadata for ``ticker`` and persist it + the raw JSON.

    ``get_json`` is an injectable transport (for tests/offline). The raw
    submissions dict is JSON-serialized here so ``storage`` stays
    source-agnostic.
    """
    _logging.info(_logger, "ingest.start", source="sec_edgar", ticker=ticker.strip().upper())
    try:
        result = fetch_filings(ticker, forms=forms, limit=limit, get_json=get_json)
        rows_written = store.save_filings(conn, result.normalized)
        raw_id = store.save_raw(
            conn,
            source=result.source,
            ticker=result.ticker,
            fetched_at=result.fetched_at,
            payload=json.dumps(result.raw, default=str),
        )
    except Exception as exc:
        _logging.error(_logger, "ingest.error", source="sec_edgar", ticker=ticker.strip().upper(), error=type(exc).__name__)
        raise
    _logging.info(_logger, "ingest.ok", source=result.source, ticker=result.ticker, rows=rows_written, raw_id=raw_id)
    return IngestSummary(ticker=result.ticker, rows_written=rows_written, raw_id=raw_id)


def ingest_filing_sections(
    conn: sqlite3.Connection,
    ticker: str,
    forms: tuple[str, ...] = ("10-K", "10-Q"),
    limit: int = 3,
    user_agent: str | None = None,
    get_text=None,
) -> IngestSummary:
    """Download + extract sections for ``ticker``'s stored filings.

    Works off the ``filings`` table (run ``ingest_filings`` first), taking the
    ``limit`` newest filings of the given ``forms``. Filings whose sections are
    already stored are skipped — EDGAR documents are immutable, so there is
    never a reason to re-download one. ``raw`` per filing is a provenance
    record (URL, bytes, sha256), not the multi-MB HTML; ``raw_id`` in the
    summary is the last one written (0 if everything was skipped).
    """
    ticker_clean = ticker.strip().upper()
    _logging.info(_logger, "ingest.start", source="sec_edgar_doc", ticker=ticker_clean)

    filings = store.load_filings(conn, ticker_clean, forms=forms, limit=limit)
    if not filings:
        _logging.warning(
            _logger, "ingest.empty", source="sec_edgar_doc", ticker=ticker_clean,
            reason="no_filings_stored",
        )
        return IngestSummary(ticker=ticker_clean, rows_written=0, raw_id=0)

    rows_written = 0
    raw_id = 0
    try:
        for filing in filings:
            if store.load_filing_sections(conn, ticker_clean, accession_number=filing.accession_number):
                continue  # immutable document, already extracted
            result = fetch_filing_sections(filing, user_agent=user_agent, get_text=get_text)
            rows_written += store.save_filing_sections(conn, result.normalized)
            raw_id = store.save_raw(
                conn,
                source=result.source,
                ticker=result.ticker,
                fetched_at=result.fetched_at,
                payload=json.dumps(result.raw),
            )
    except Exception as exc:
        _logging.error(_logger, "ingest.error", source="sec_edgar_doc", ticker=ticker_clean, error=type(exc).__name__)
        raise
    _logging.info(_logger, "ingest.ok", source="sec_edgar_doc", ticker=ticker_clean, rows=rows_written, raw_id=raw_id)
    return IngestSummary(ticker=ticker_clean, rows_written=rows_written, raw_id=raw_id)
