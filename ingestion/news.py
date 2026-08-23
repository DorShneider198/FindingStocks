"""Company news fetcher (Finnhub — free tier, API key required).

Fetches company news for a ticker from Finnhub's ``/company-news`` endpoint,
normalizes each article into a ``NewsArticle`` record, and preserves the raw
JSON list for separate storage. Uses stdlib ``urllib`` so there's no new dep.

The API key comes from the environment (``FINNHUB_API_KEY``) and is sent only
as the ``token`` query parameter — never hardcoded, never logged. The HTTP
getter is injectable so tests run offline with no network and no key.
"""

from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any, Callable

from ingestion import _logging

SOURCE = "finnhub"
_COMPANY_NEWS_URL = "https://finnhub.io/api/v1/company-news"
_DEFAULT_WINDOW_DAYS = 30

GetJson = Callable[[str], Any]

_logger = _logging.get_logger(__name__)


@dataclass(frozen=True)
class NewsArticle:
    """One normalized news article about a ticker."""

    ticker: str
    article_id: int
    published_at: datetime
    headline: str
    summary: str
    source_name: str
    url: str


@dataclass
class NewsFetchResult:
    """Result of a news fetch: normalized articles plus the raw JSON list."""

    source: str
    ticker: str
    fetched_at: datetime
    normalized: list[NewsArticle]
    raw: Any


def fetch_news(
    ticker: str,
    start: date | None = None,
    end: date | None = None,
    http_get: GetJson | None = None,
) -> NewsFetchResult:
    """Fetch company news for ``ticker`` between ``start`` and ``end`` (inclusive).

    Defaults to the last 30 days. ``http_get`` is an injectable transport
    (url -> parsed JSON) for tests. Raises ``ValueError`` for an empty ticker
    and ``RuntimeError`` if ``FINNHUB_API_KEY`` is unset when a live fetch is
    attempted.
    """
    ticker = ticker.strip().upper()
    if not ticker:
        raise ValueError("ticker must be a non-empty string")

    end = end or datetime.now(timezone.utc).date()
    start = start or end - timedelta(days=_DEFAULT_WINDOW_DAYS)

    _logging.info(_logger, "fetch.start", source=SOURCE, ticker=ticker)

    try:
        url = _build_url(ticker, start, end, token=_api_key() if http_get is None else None)
        raw = (http_get or _http_get_json)(url)
    except (ValueError, RuntimeError):
        raise
    except Exception as exc:
        _logging.error(_logger, "fetch.error", source=SOURCE, ticker=ticker, error=type(exc).__name__)
        raise
    fetched_at = datetime.now(timezone.utc)

    normalized = [_normalize(ticker, item) for item in raw or []]
    if not normalized:
        _logging.warning(_logger, "fetch.empty", source=SOURCE, ticker=ticker)
    else:
        _logging.info(_logger, "fetch.ok", source=SOURCE, ticker=ticker, rows=len(normalized))

    return NewsFetchResult(
        source=SOURCE,
        ticker=ticker,
        fetched_at=fetched_at,
        normalized=normalized,
        raw=raw,
    )


def _build_url(ticker: str, start: date, end: date, token: str | None) -> str:
    """Build the company-news URL; ``token`` is omitted when a test transport is used."""
    params = {"symbol": ticker, "from": start.isoformat(), "to": end.isoformat()}
    if token:
        params["token"] = token
    return f"{_COMPANY_NEWS_URL}?{urllib.parse.urlencode(params)}"


def _normalize(ticker: str, item: dict) -> NewsArticle:
    """Map one Finnhub article dict to a normalized ``NewsArticle``."""
    return NewsArticle(
        ticker=ticker,
        article_id=int(item["id"]),
        published_at=datetime.fromtimestamp(item["datetime"], tz=timezone.utc),
        headline=item.get("headline", ""),
        summary=item.get("summary", ""),
        source_name=item.get("source", ""),
        url=item.get("url", ""),
    )


def _http_get_json(url: str) -> Any:
    """Default HTTP getter: GET ``url`` and parse the JSON body."""
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _api_key() -> str:
    """Read the Finnhub API key from the environment; fail with setup help if unset."""
    key = os.environ.get("FINNHUB_API_KEY")
    if not key:
        raise RuntimeError(
            "Finnhub API key missing: set FINNHUB_API_KEY in the environment. "
            "Get a free key at https://finnhub.io/dashboard (never hardcode it)."
        )
    return key
