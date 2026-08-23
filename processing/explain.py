"""LLM research briefs: ticker in, grounded plain-English explanations out.

Generates three short briefs — what the company does, the mainstream bull
thesis, the mainstream bear thesis — using the Anthropic API, **strictly from
stored documents**: extracted filing sections, news headlines/summaries, and
the yfinance business profile (mined from the raw archive). The model is
instructed to use no outside knowledge, cite a source id ``[S#]`` for every
claim, ignore boilerplate risk language (currency, cyber, key personnel —
near-identical across all companies) in favor of company-specific material,
and to say the sources are insufficient rather than invent a thesis.

Grounding is enforced in code too: a brief citing an unknown source id, or
carrying no citations at all without declaring insufficiency, raises
``GroundingError`` and is never stored.

Briefs are cached in the ``briefs`` table keyed by ``(ticker, source_hash)``
where the hash covers the exact source texts — same stored data, same hash,
zero API calls. New filings or news change the hash and trigger a fresh
generation.

The API key comes from ``ANTHROPIC_API_KEY`` (environment, falling back to a
``.env`` file at the project root — gitignored, never committed). The client
is injectable so the test runs offline.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from ingestion import _logging
from storage import store

DEFAULT_MODEL = "claude-opus-5"
_NEWS_WINDOW_DAYS = 30
_MAX_NEWS_ITEMS = 40
_SECTION_WORD_CAPS = {"risk_factors": 15_000, "business": 8_000, "mdna": 8_000}
_INSUFFICIENT_PREFIX = "The stored sources"

_CITATION_RE = re.compile(r"\[S(\d+)\]")
_PROJECT_ROOT = Path(__file__).resolve().parent.parent

_logger = _logging.get_logger(__name__)

_SYSTEM_PROMPT = """\
You write short research briefs for a private investor, working ONLY from the
numbered sources provided in the user message. Hard rules:

1. Use NO knowledge beyond the provided sources. If you know something about
   this company that the sources don't say, it does not exist for this task.
2. Cite a source for every claim by putting its id in brackets, e.g. [S3],
   immediately after the claim. Cite only ids that appear in the sources.
3. "What it does" must be intuitive plain English; define any technical term
   you have to use, in one clause, the first time it appears.
4. For the bull and bear cases: give the MAINSTREAM thesis a well-read
   investor would recognize, built only from what the sources support.
5. Risk-factor sections are mostly generic boilerplate that appears in every
   company's filings — currency risk, interest rates, cybersecurity, reliance
   on key personnel, litigation, general economic conditions. DISREGARD that
   boilerplate. Build the bear case only from risks specific to THIS
   company's business, products, customers, or financial position. Apply the
   same standard to the bull case: company-specific strengths, not generic
   optimism.
6. If the sources are too thin to support a section honestly, write a single
   sentence starting exactly "The stored sources" explaining what is missing,
   instead of inventing content.
7. Keep each section under 150 words.
"""

_OUTPUT_SCHEMA = {
    "type": "json_schema",
    "schema": {
        "type": "object",
        "properties": {
            "what_it_does": {"type": "string"},
            "bull_case": {"type": "string"},
            "bear_case": {"type": "string"},
        },
        "required": ["what_it_does", "bull_case", "bear_case"],
        "additionalProperties": False,
    },
}


class GroundingError(RuntimeError):
    """The model's output failed citation validation; the brief was discarded."""


@dataclass(frozen=True)
class BriefSource:
    """One source document behind a brief, for citation rendering."""

    id: str          # "S1", "S2", ...
    kind: str        # "profile" | "filing:business" | "filing:risk_factors"
                     # | "filing:mdna" | "news"
    label: str       # human-readable, e.g. "10-K 0000320193-25-000079 · Risk Factors"
    url: str | None


@dataclass(frozen=True)
class Brief:
    """Three grounded explanations plus the sources they cite."""

    ticker: str
    what_it_does: str    # text with inline [S#] markers
    bull_case: str
    bear_case: str
    sources: list[BriefSource]
    source_hash: str
    generated_at: datetime
    model: str


def generate_brief(
    conn: sqlite3.Connection,
    ticker: str,
    client: Any | None = None,
    model: str | None = None,
) -> Brief:
    """Produce (or fetch from cache) the research brief for ``ticker``.

    Raises ``ValueError`` when nothing usable is stored for the ticker, and
    ``GroundingError`` when the model's output fails citation validation.
    ``client`` is an injectable Anthropic client for tests.
    """
    ticker = ticker.strip().upper()
    if not ticker:
        raise ValueError("ticker must be a non-empty string")
    model = model or os.environ.get("EXPLAIN_MODEL") or DEFAULT_MODEL

    sources, texts = _collect_sources(conn, ticker)
    if not sources:
        raise ValueError(
            f"nothing stored for {ticker!r} to ground a brief on — "
            "ingest filings/news/fundamentals first"
        )
    source_hash = _hash_sources(sources, texts)

    cached = store.load_brief(conn, ticker, source_hash)
    if cached is not None:
        _logging.info(_logger, "brief.cache_hit", ticker=ticker)
        return _from_row(cached)

    _logging.info(_logger, "brief.generate", ticker=ticker, sources=len(sources), model=model)
    client = client or _make_client()
    response = client.beta.messages.create(
        model=model,
        max_tokens=16000,
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        system=_SYSTEM_PROMPT,
        output_config={"format": _OUTPUT_SCHEMA},
        messages=[{"role": "user", "content": _build_user_prompt(ticker, sources, texts)}],
    )
    if response.stop_reason == "refusal":
        raise RuntimeError(f"model declined to generate a brief for {ticker}")

    payload = json.loads(next(b.text for b in response.content if b.type == "text"))
    _validate_citations(ticker, payload, {s.id for s in sources})

    brief = Brief(
        ticker=ticker,
        what_it_does=payload["what_it_does"],
        bull_case=payload["bull_case"],
        bear_case=payload["bear_case"],
        sources=sources,
        source_hash=source_hash,
        generated_at=datetime.now(timezone.utc),
        model=model,
    )
    store.save_brief(
        conn, ticker, source_hash, brief.generated_at, model,
        brief.what_it_does, brief.bull_case, brief.bear_case,
        json.dumps([s.__dict__ for s in sources]),
    )
    _logging.info(_logger, "brief.ok", ticker=ticker)
    return brief


# --- source collection ------------------------------------------------------

def _collect_sources(conn: sqlite3.Connection, ticker: str) -> tuple[list[BriefSource], list[str]]:
    """Assemble the grounded source set from the DB, deterministically ordered.

    Order: profile, filing sections (business, risk_factors, mdna — latest
    filing each), then news (newest first). Deterministic order keeps the
    source hash stable for identical data.
    """
    sources: list[BriefSource] = []
    texts: list[str] = []

    def add(kind: str, label: str, url: str | None, text: str) -> None:
        sources.append(BriefSource(id=f"S{len(sources) + 1}", kind=kind, label=label, url=url))
        texts.append(text)

    profile = _profile_summary(conn, ticker)
    if profile:
        add("profile", "Company profile (yfinance)", None, profile)

    filing_urls = {
        f.accession_number: f.filing_url for f in store.load_filings(conn, ticker)
    }
    seen_sections: set[str] = set()
    for s in store.load_filing_sections(conn, ticker):  # newest filing first
        if s.section in seen_sections or s.confidence == "missing":
            continue
        seen_sections.add(s.section)
        cap = _SECTION_WORD_CAPS.get(s.section, 8_000)
        words = s.text.split()
        text = " ".join(words[:cap]) + (" [truncated]" if len(words) > cap else "")
        add(
            f"filing:{s.section}",
            f"{s.form} {s.accession_number} · {s.section}",
            filing_urls.get(s.accession_number),
            text,
        )

    since = datetime.now(timezone.utc) - timedelta(days=_NEWS_WINDOW_DAYS)
    articles = store.load_news_articles(conn, ticker, start=since)  # oldest first
    for a in reversed(articles[-_MAX_NEWS_ITEMS:]):  # newest first
        body = a.headline if not a.summary else f"{a.headline} — {a.summary}"
        add(
            "news",
            f"News: {a.source_name} {a.published_at.date().isoformat()}",
            a.url or None,
            body,
        )

    return sources, texts


def _profile_summary(conn: sqlite3.Connection, ticker: str) -> str | None:
    """Mine yfinance's longBusinessSummary out of the raw archive."""
    for payload in store.load_raw_payloads(conn, "yfinance", ticker):
        try:
            data = json.loads(payload)
        except (ValueError, TypeError):
            continue
        if isinstance(data, dict) and data.get("longBusinessSummary"):
            return str(data["longBusinessSummary"])
    return None


def _hash_sources(sources: list[BriefSource], texts: list[str]) -> str:
    """Stable hash of the exact source set + contents."""
    digest = hashlib.sha256()
    for source, text in zip(sources, texts):
        digest.update(source.kind.encode())
        digest.update(source.label.encode())
        digest.update(hashlib.sha256(text.encode()).digest())
    return digest.hexdigest()


# --- prompt + validation ----------------------------------------------------

def _build_user_prompt(ticker: str, sources: list[BriefSource], texts: list[str]) -> str:
    blocks = [
        f"[{source.id}] ({source.kind}) {source.label}\n{text}"
        for source, text in zip(sources, texts)
    ]
    return (
        f"Ticker: {ticker}\n\nSOURCES:\n\n" + "\n\n---\n\n".join(blocks)
        + "\n\nWrite the three sections now, following every rule."
    )


def _validate_citations(ticker: str, payload: dict, valid_ids: set[str]) -> None:
    """Reject output citing unknown sources or making uncited claims."""
    for field in ("what_it_does", "bull_case", "bear_case"):
        text = payload[field]
        cited = {f"S{n}" for n in _CITATION_RE.findall(text)}
        unknown = cited - valid_ids
        if unknown:
            _logging.error(_logger, "brief.bad_citation", ticker=ticker,
                           field=field, unknown=",".join(sorted(unknown)), exc_info=False)
            raise GroundingError(
                f"{field} cites unknown source(s) {sorted(unknown)} — brief discarded"
            )
        if not cited and not text.startswith(_INSUFFICIENT_PREFIX):
            _logging.error(_logger, "brief.uncited", ticker=ticker, field=field, exc_info=False)
            raise GroundingError(
                f"{field} has no citations and doesn't declare sources insufficient"
            )


# --- client plumbing --------------------------------------------------------

def _from_row(row: dict) -> Brief:
    return Brief(
        ticker=row["ticker"],
        what_it_does=row["what_it_does"],
        bull_case=row["bull_case"],
        bear_case=row["bear_case"],
        sources=[BriefSource(**s) for s in json.loads(row["sources_json"])],
        source_hash=row["source_hash"],
        generated_at=datetime.fromisoformat(row["generated_at"]),
        model=row["model"],
    )


def _make_client() -> Any:
    """Build an Anthropic client; key from env or the project-root .env file."""
    key = os.environ.get("ANTHROPIC_API_KEY") or _read_env_file("ANTHROPIC_API_KEY")
    if not key:
        raise RuntimeError(
            "Anthropic API key missing: set ANTHROPIC_API_KEY in the environment "
            "or in a .env file at the project root (gitignored — never commit it)."
        )
    import anthropic  # lazy: tests inject a fake client and need neither dep nor key

    return anthropic.Anthropic(api_key=key)


def _read_env_file(name: str) -> str | None:
    """Minimal .env parser: KEY=VALUE lines, optional quotes, # comments."""
    env_path = _PROJECT_ROOT / ".env"
    if not env_path.exists():
        return None
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        if key.strip() == name:
            return value.strip().strip("'\"") or None
    return None
