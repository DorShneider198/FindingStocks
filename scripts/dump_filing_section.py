#!/usr/bin/env python
"""Dump an extracted filing section to stdout, for eyeballing the extraction.

Usage (from the repo root):

    .venv/bin/python scripts/dump_filing_section.py AAPL risk_factors
    .venv/bin/python scripts/dump_filing_section.py AAPL mdna --form 10-Q
    .venv/bin/python scripts/dump_filing_section.py AAPL business | less

Reads from the local DB; if the section isn't stored yet, it ingests the
filing metadata and documents first (live SEC calls — no key needed).
Extraction metadata goes to stderr, the section text to stdout, so piping
to a file or ``less`` gives you clean text.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ingestion.pipeline import DEFAULT_DOC_FORMS, ingest_filing_sections, ingest_filings  # noqa: E402
from storage import store  # noqa: E402


def _matching(conn, ticker: str, section: str, form: str | None):
    """Stored sections for the ticker, optionally narrowed to one base form."""
    return [
        s for s in store.load_filing_sections(conn, ticker, section=section)
        if form is None or s.form.upper().removesuffix("/A") == form
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("ticker")
    parser.add_argument("section", choices=("business", "risk_factors", "mdna"))
    parser.add_argument(
        "--form", default=None, choices=("10-K", "10-Q", "20-F"),
        help="restrict to one form type; default: newest of any supported form "
             "(so foreign issuers filing 20-F work without knowing the form)",
    )
    args = parser.parse_args()
    ticker = args.ticker.strip().upper()

    conn = store.get_connection()
    sections = _matching(conn, ticker, args.section, args.form)
    if not sections:
        print(f"nothing stored for {ticker} {args.section} — ingesting...", file=sys.stderr)
        forms = (args.form, f"{args.form}/A") if args.form else DEFAULT_DOC_FORMS
        ingest_filings(conn, ticker, forms=forms, limit=3)
        ingest_filing_sections(conn, ticker, forms=forms, limit=3)
        sections = _matching(conn, ticker, args.section, args.form)
    if not sections:
        wanted = args.form or "any supported form"
        print(f"no {args.section} found for {ticker} ({wanted})", file=sys.stderr)
        return 1

    s = sections[0]  # newest accession
    print(
        f"{s.ticker} {s.form} {s.accession_number} · {s.section}\n"
        f"confidence={s.confidence} words={s.word_count} "
        f"heading={s.matched_heading!r} extracted={s.extracted_at:%Y-%m-%d}\n"
        + "-" * 72,
        file=sys.stderr,
    )
    print(s.text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
