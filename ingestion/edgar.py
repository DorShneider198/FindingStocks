"""SEC EDGAR filings fetcher (free — no API key, no account).

Maps a ticker to its CIK via SEC's public ``company_tickers.json``, fetches the
company's submissions JSON, and normalizes recent filings into ``Filing``
records. SEC's fair-access policy requires a User-Agent identifying the caller
(with contact info) — that's the only requirement. The raw submissions JSON is
preserved for separate storage. Uses stdlib ``urllib`` so there's no new dep.
"""

from __future__ import annotations

import json
import os
import urllib.request
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Any, Callable

from ingestion import _logging

SOURCE = "sec_edgar"
_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik:010d}.json"
_ARCHIVES_URL = "https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/{document}"
_DEFAULT_USER_AGENT = "findingstocks dor.shneider@gmail.com"

GetJson = Callable[[str, str], Any]

_logger = _logging.get_logger(__name__)


@dataclass(frozen=True)
class Filing:
    """One normalized SEC filing."""

    ticker: str
    cik: int
    form: str
    filing_date: date
    accession_number: str
    primary_document: str
    primary_doc_description: str | None
    report_date: date | None
    filing_url: str


@dataclass
class FilingsFetchResult:
    """Result of a filings fetch: normalized filings plus the raw submissions JSON."""

    source: str
    ticker: str
    fetched_at: datetime
    normalized: list[Filing]
    raw: Any


def fetch_filings(
    ticker: str,
    forms: tuple[str, ...] | None = None,
    limit: int = 20,
    user_agent: str | None = None,
    get_json: GetJson | None = None,
) -> FilingsFetchResult:
    """Fetch recent SEC filings for ``ticker``.

    ``forms`` optionally restricts to specific form types (e.g.
    ``("10-K", "10-Q", "8-K")``); ``limit`` caps how many are returned (most
    recent first). ``get_json`` is injectable for tests. Raises ``ValueError``
    for an empty ticker or one with no CIK in SEC's map.
    """
    ticker = ticker.strip().upper()
    if not ticker:
        raise ValueError("ticker must be a non-empty string")

    user_agent = user_agent or os.environ.get("SEC_EDGAR_USER_AGENT") or _DEFAULT_USER_AGENT
    get_json = get_json or _http_get_json

    _logging.info(_logger, "fetch.start", source=SOURCE, ticker=ticker)

    try:
        tickers_payload = get_json(_TICKERS_URL, user_agent)
        cik = _resolve_cik(ticker, tickers_payload)
        if cik is None:
            _logging.warning(_logger, "fetch.empty", source=SOURCE, ticker=ticker, reason="no_cik")
            raise ValueError(f"no CIK found for ticker {ticker!r} in SEC ticker map")
        raw = get_json(_SUBMISSIONS_URL.format(cik=cik), user_agent)
    except ValueError:
        raise
    except Exception as exc:
        _logging.error(_logger, "fetch.error", source=SOURCE, ticker=ticker, error=type(exc).__name__)
        raise
    fetched_at = datetime.now(timezone.utc)

    filings = _normalize(ticker, cik, raw, forms, limit)
    if not filings:
        _logging.warning(_logger, "fetch.empty", source=SOURCE, ticker=ticker, reason="no_filings")
    else:
        _logging.info(_logger, "fetch.ok", source=SOURCE, ticker=ticker, rows=len(filings))
    return FilingsFetchResult(
        source=SOURCE,
        ticker=ticker,
        fetched_at=fetched_at,
        normalized=filings,
        raw=raw,
    )


def _http_get_json(url: str, user_agent: str) -> Any:
    """Default HTTP getter: GET ``url`` with the SEC-required User-Agent."""
    req = urllib.request.Request(
        url, headers={"User-Agent": user_agent, "Accept": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _resolve_cik(ticker: str, tickers_payload: dict) -> int | None:
    """Find the integer CIK for ``ticker`` in SEC's company_tickers.json payload."""
    for entry in tickers_payload.values():
        if str(entry.get("ticker", "")).upper() == ticker:
            return int(entry["cik_str"])
    return None


def _normalize(
    ticker: str,
    cik: int,
    submissions: dict,
    forms: tuple[str, ...] | None,
    limit: int,
) -> list[Filing]:
    """Turn SEC submissions JSON into normalized ``Filing`` records (most recent first)."""
    recent = submissions.get("filings", {}).get("recent", {})
    accession_numbers = recent.get("accessionNumber", [])
    forms_list = recent.get("form", [])
    filing_dates = recent.get("filingDate", [])
    report_dates = recent.get("reportDate", [])
    primary_docs = recent.get("primaryDocument", [])
    primary_descs = recent.get("primaryDocDescription", [])

    wanted = {f.upper() for f in forms} if forms else None
    filings: list[Filing] = []
    for i in range(len(accession_numbers)):
        form = forms_list[i]
        if wanted is not None and form.upper() not in wanted:
            continue

        accession = accession_numbers[i]
        document = primary_docs[i] if i < len(primary_docs) else ""
        report_raw = report_dates[i] if i < len(report_dates) else ""
        desc = primary_descs[i] if i < len(primary_descs) else ""

        filings.append(
            Filing(
                ticker=ticker,
                cik=cik,
                form=form,
                filing_date=date.fromisoformat(filing_dates[i]),
                accession_number=accession,
                primary_document=document,
                primary_doc_description=desc or None,
                report_date=date.fromisoformat(report_raw) if report_raw else None,
                filing_url=_ARCHIVES_URL.format(
                    cik=cik, accession=accession.replace("-", ""), document=document
                ),
            )
        )
        if len(filings) >= limit:
            break
    return filings
