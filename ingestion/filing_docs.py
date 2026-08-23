"""SEC filing document fetcher: download a filing and extract key sections.

Downloads the primary document behind a ``Filing`` (see ``edgar.py``) and
extracts the sections that matter for research, as plain text:

  * ``business``      — 10-K Item 1
  * ``risk_factors``  — 10-K Item 1A / 10-Q Part II Item 1A
  * ``mdna``          — 10-K Item 7  / 10-Q Part I Item 2

Extraction is **heuristic**: the HTML is stripped to text (stdlib
``HTMLParser``), then ``Item N`` headings are located by regex and the span up
to the next item/part heading is taken. The table of contents also contains
"Item 1A" etc., so for each wanted item the candidate with the largest
following body wins. Every section records extraction metadata — word count,
the heading text that matched, and a confidence flag (``high``/``low``/
``missing``) — so a bad grab is visible in the DB instead of silently
poisoning downstream summarization. A wanted section that isn't found still
produces a row, flagged ``missing``.

Raw handling deviates from the always-store-raw rule by design (user-approved):
EDGAR documents are immutable and permanently re-fetchable, and their HTML runs
5–30 MB each, so ``raw`` is a small provenance record (URL, byte size, SHA-256)
rather than the document itself.

Fair access: SEC allows 10 req/s with a declared User-Agent. The default
transport throttles to at most one document every 0.5 s and, on SEC's 403
rate-limit response, backs off 10 s before retrying. An injected ``get_text``
bypasses the network (and the throttle) entirely, so tests run offline.
"""

from __future__ import annotations

import hashlib
import os
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from typing import Any, Callable

from ingestion import _logging
from ingestion._resilience import with_retry
from ingestion.edgar import Filing

SOURCE = "sec_edgar_doc"
_DEFAULT_USER_AGENT = "findingstocks dor.shneider@gmail.com"
_MIN_INTERVAL_SECONDS = 0.5
_RATE_LIMIT_BACKOFF_SECONDS = 10.0
_MIN_WORDS_HIGH_CONFIDENCE = 500

# Which items make up each canonical section, per (amendment-normalized) form.
# 20-F (foreign private issuers) is item-structured like a 10-K, numbered
# differently: Item 3 "Key Information" holds risk factors (section D), Item 4
# is the business, Item 5 "Operating and Financial Review" is the MD&A
# equivalent. 40-F is NOT here on purpose: it's a wrapper whose content lives
# in exhibits (AIF, MD&A) — support is a separate step; until then it skips
# with a visible log rather than a wrong extraction.
_SECTION_ITEMS = {
    "10-K": {"business": "1", "risk_factors": "1A", "mdna": "7"},
    "10-Q": {"risk_factors": "1A", "mdna": "2"},
    "20-F": {"risk_factors": "3", "business": "4", "mdna": "5"},
}


def _base_form(form: str) -> str:
    """Normalize a form name for section-map lookup: 10-K/A -> 10-K."""
    return form.upper().removesuffix("/A")


def has_section_map(form: str) -> bool:
    """True when we know how to extract sections from this form type."""
    return _base_form(form) in _SECTION_ITEMS

GetText = Callable[[str, str], str]

_logger = _logging.get_logger(__name__)


@dataclass(frozen=True)
class FilingSection:
    """One extracted section of a filing, with extraction metadata."""

    accession_number: str
    ticker: str
    form: str
    section: str            # "business" | "risk_factors" | "mdna"
    text: str               # plain text; "" when confidence == "missing"
    word_count: int
    matched_heading: str | None  # the heading text the extractor locked onto
    confidence: str         # "high" | "low" | "missing"
    extracted_at: datetime


@dataclass
class FilingSectionsResult:
    """Result of a document fetch: extracted sections plus a provenance record."""

    source: str
    ticker: str
    fetched_at: datetime
    normalized: list[FilingSection]
    raw: Any  # {"filing_url", "bytes", "sha256"} — not the HTML (see module doc)


def fetch_filing_sections(
    filing: Filing,
    user_agent: str | None = None,
    get_text: GetText | None = None,
) -> FilingSectionsResult:
    """Download ``filing``'s primary document and extract its key sections.

    Raises ``ValueError`` for form types we don't know how to section
    (only 10-K and 10-Q are supported). ``get_text`` is injectable for tests.
    """
    items = _SECTION_ITEMS.get(_base_form(filing.form))
    if items is None:
        raise ValueError(
            f"no section map for form {filing.form!r} "
            f"(supported: {', '.join(sorted(_SECTION_ITEMS))} and their /A amendments)"
        )

    user_agent = user_agent or os.environ.get("SEC_EDGAR_USER_AGENT") or _DEFAULT_USER_AGENT

    _logging.info(
        _logger, "fetch.start", source=SOURCE, ticker=filing.ticker,
        accession=filing.accession_number,
    )
    try:
        html = (get_text or _http_get_text)(filing.filing_url, user_agent)
    except Exception as exc:
        _logging.error(
            _logger, "fetch.error", source=SOURCE, ticker=filing.ticker,
            accession=filing.accession_number, error=type(exc).__name__,
        )
        raise
    fetched_at = datetime.now(timezone.utc)

    text = _html_to_text(html)
    sections = [
        _extract_section(filing, section, item_id, text, fetched_at)
        for section, item_id in items.items()
    ]

    missing = [s.section for s in sections if s.confidence == "missing"]
    if missing:
        _logging.warning(
            _logger, "fetch.partial", source=SOURCE, ticker=filing.ticker,
            accession=filing.accession_number, missing=",".join(missing),
        )
    else:
        _logging.info(
            _logger, "fetch.ok", source=SOURCE, ticker=filing.ticker,
            accession=filing.accession_number, rows=len(sections),
        )

    provenance = {
        "filing_url": filing.filing_url,
        "bytes": len(html.encode("utf-8", errors="replace")),
        "sha256": hashlib.sha256(html.encode("utf-8", errors="replace")).hexdigest(),
    }
    return FilingSectionsResult(
        source=SOURCE,
        ticker=filing.ticker,
        fetched_at=fetched_at,
        normalized=sections,
        raw=provenance,
    )


# --- HTML -> text -----------------------------------------------------------

class _TextExtractor(HTMLParser):
    """Strip HTML to plain text: drop script/style, newline at block edges."""

    _SKIP = {"script", "style"}
    _BLOCK = {"p", "div", "br", "tr", "table", "li", "h1", "h2", "h3", "h4", "h5", "h6"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._skip_depth = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in self._SKIP:
            self._skip_depth += 1
        elif tag in self._BLOCK:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in self._SKIP:
            self._skip_depth = max(0, self._skip_depth - 1)
        elif tag in self._BLOCK:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self._skip_depth:
            self.parts.append(data)


def _html_to_text(html: str) -> str:
    """Reduce filing HTML to whitespace-normalized plain text."""
    parser = _TextExtractor()
    parser.feed(html)
    text = "".join(parser.parts).replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    return re.sub(r"\s*\n\s*", "\n", text).strip()


# --- section extraction -----------------------------------------------------

def _item_pattern(item_id: str) -> re.Pattern:
    """Match ``Item <id>`` at a line start, as a standalone token.

    Line-anchored (block boundaries became newlines in ``_html_to_text``)
    because filings are full of mid-sentence cross-references like "see Item
    1A of this Form 10-K" — real headings are their own block; references
    aren't. The token lookahead keeps Item 1 from matching Item 1A/10.
    """
    return re.compile(rf"^item\s+{re.escape(item_id)}(?![\w])\.?", re.IGNORECASE | re.MULTILINE)

# Any item/part heading at a line start — the end boundary of a section span.
_ANY_HEADING = re.compile(
    r"^(?:item\s+\d{1,2}[a-c]?(?![\w])|part\s+[ivx]+(?![\w]))",
    re.IGNORECASE | re.MULTILINE,
)


def _extract_section(
    filing: Filing,
    section: str,
    item_id: str,
    text: str,
    extracted_at: datetime,
) -> FilingSection:
    """Take the best ``Item <item_id>`` span from ``text``; flag the outcome.

    Every occurrence of the heading (TOC entries included) is a candidate; the
    one with the most text before the next item/part heading wins, which is
    what reliably separates the real section from its TOC line.
    """
    best_body = ""
    best_heading: str | None = None
    for match in _item_pattern(item_id).finditer(text):
        nxt = _ANY_HEADING.search(text, match.end())
        body = text[match.end(): nxt.start() if nxt else len(text)].strip()
        if len(body) > len(best_body):
            best_body = body
            # Collapse whitespace: headings can wrap mid-phrase ("Item\n3.").
            best_heading = " ".join(text[match.start(): match.end() + 40].split())[:60]

    words = len(best_body.split()) if best_body else 0
    if not best_body:
        confidence = "missing"
    elif words >= _MIN_WORDS_HIGH_CONFIDENCE:
        confidence = "high"
    else:
        confidence = "low"

    return FilingSection(
        accession_number=filing.accession_number,
        ticker=filing.ticker,
        form=filing.form.upper(),
        section=section,
        text=best_body,
        word_count=words,
        matched_heading=best_heading,
        confidence=confidence,
        extracted_at=extracted_at,
    )


# --- default transport (throttled, retrying, SEC-aware) ---------------------

_last_request_at = [0.0]


def _throttle(sleep: Callable[[float], None] = time.sleep) -> None:
    """Enforce >= _MIN_INTERVAL_SECONDS between document downloads."""
    wait = _MIN_INTERVAL_SECONDS - (time.monotonic() - _last_request_at[0])
    if wait > 0:
        sleep(wait)
    _last_request_at[0] = time.monotonic()


def _http_get_text(url: str, user_agent: str) -> str:
    """Throttled, retrying GET. SEC's 403 rate-limit reply gets a long backoff."""

    def once() -> str:
        _throttle()
        req = urllib.request.Request(url, headers={"User-Agent": user_agent})
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as exc:
            if exc.code == 403:  # SEC throttling us: wait well past the window
                time.sleep(_RATE_LIMIT_BACKOFF_SECONDS)
            raise

    return with_retry(once)
