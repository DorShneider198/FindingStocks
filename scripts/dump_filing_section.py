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

from ingestion.pipeline import ingest_filing_sections, ingest_filings  # noqa: E402
from storage import store  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("ticker")
    parser.add_argument("section", choices=("business", "risk_factors", "mdna"))
    parser.add_argument("--form", default="10-K", choices=("10-K", "10-Q"))
    args = parser.parse_args()
    ticker = args.ticker.strip().upper()

    conn = store.get_connection()
    sections = [
        s for s in store.load_filing_sections(conn, ticker, section=args.section)
        if s.form == args.form
    ]
    if not sections:
        print(f"nothing stored for {ticker} {args.section} — ingesting...", file=sys.stderr)
        ingest_filings(conn, ticker, forms=(args.form,), limit=1)
        ingest_filing_sections(conn, ticker, forms=(args.form,), limit=1)
        sections = [
            s for s in store.load_filing_sections(conn, ticker, section=args.section)
            if s.form == args.form
        ]
    if not sections:
        print(f"no {args.section} found for {ticker} ({args.form})", file=sys.stderr)
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
