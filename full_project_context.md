# Project Overview: `FindingStocks`

## Directory Tree
```text
├── dashboard
│   ├── .DS_Store
│   ├── __init__.py
│   ├── app.py
│   └── views.py
├── data
│   └── findingstocks.db
├── features
│   └── __init__.py
├── ingestion
│   ├── __init__.py
│   ├── _logging.py
│   ├── _resilience.py
│   ├── edgar.py
│   ├── filing_docs.py
│   ├── fundamentals.py
│   ├── news.py
│   ├── pipeline.py
│   ├── prices.py
│   └── reddit.py
├── models
│   └── __init__.py
├── processing
│   ├── .DS_Store
│   ├── __init__.py
│   └── explain.py
├── scripts
│   └── dump_filing_section.py
├── storage
│   ├── .DS_Store
│   ├── __init__.py
│   └── store.py
├── tests
│   ├── conftest.py
│   ├── test_dashboard_views.py
│   ├── test_edgar.py
│   ├── test_explain.py
│   ├── test_filing_docs.py
│   ├── test_fundamentals.py
│   ├── test_logging.py
│   ├── test_news.py
│   ├── test_pipeline.py
│   ├── test_prices.py
│   ├── test_reddit.py
│   ├── test_resilience.py
│   └── test_store.py
├── .DS_Store
├── .env
├── .env.save
├── .gitignore
├── bundle.py
├── CLAUDE.md
├── requirements.txt
├── ROADMAP.md
└── WALKTHROUGH.md
```

## Source Files

### `CLAUDE.md`

```python
# CLAUDE.md — Stock Research & Sentiment Aggregation Tool

This file is the durable context for this project. Read it at the start of every
session and follow the working rules below without exception.

## Orientation
- `CLAUDE.md` (this file) — the goal, the rules, the architecture.
- `ROADMAP.md` — the staged checklist; which module is next.
- `WALKTHROUGH.md` — **how the code actually works**: the fetcher pattern, every
  file, the DB schema, the data flow. Read this when returning after a break.

## What this is
A stock research / sentiment aggregation tool for a **private investor**. Today the
user researches stocks manually — reading Reddit, news, and financial data, then
forming a view and a sense of market sentiment. This tool automates that collection
and summarization. It is a large, multi-stage project to be built **slowly and
methodically**.

## Goal, in priority order
1. **PRIMARY — the MVP: a research / aggregation tool.** Give it a ticker and see:
   - fundamentals,
   - a sentiment timeline from social sources,
   - detection of spikes in mention volume (hype detection),
   - an LLM-generated summary of what people are saying.
2. **MUCH LATER, and completely separate — a predictive modeling layer.** Realistic
   framing ONLY — **not** "predict the exact price a year out." One-year returns are
   dominated by unpredictable events and have a very low signal-to-noise ratio. The
   realistic goal is **relative ranking / classification** to help prioritize manual
   research, **always benchmarked against dumb baselines** (buy & hold, simple
   momentum). **DO NOT build this until the user explicitly says so.**

## How we work — the single most important rule
This is a massive project. **Do not try to build it all at once.** Work **ONE module
at a time**. For every module:
1. **First propose a short interface contract** (what goes in, what comes out) and
   **WAIT for approval.**
2. **Only after approval** — write the module: small and focused, with **one test**
   that proves it works.
3. **Stop, show the user, and WAIT** before moving to the next module.

Hard rules:
- **Never** dump hundreds of lines at once.
- **Never** jump ahead to modules that weren't asked for.
- **Never** touch the `models/` layer until the user explicitly says so.
- If anything is unclear — **ask, don't assume.**

## Architecture (separate modules)
- `ingestion/`  — one fetcher per source (prices, fundamentals, reddit, news). Each
  returns a normalized format; **always store the raw response separately too.**
- `storage/`    — schema + DB access layer.
- `processing/` — sentiment scoring + aggregation per ticker per day (sentiment score,
  mention volume, change in volume).
- `features/`   — assemble a feature vector per ticker per day.
- `dashboard/`  — the first useful deliverable (the MVP).
- `models/`     — last, and separate. **Locked** (see priority #2).

## Data sources (current state, 2026)
- **Prices & fundamentals:** yfinance (free, fine to start).
- **Official filings:** SEC EDGAR (free).
- **Reddit:** PRAW (free, rate-limited) — subreddits like wallstreetbets, stocks,
  investing.
- **News:** a news API such as Finnhub or NewsAPI.
- **Twitter/X:** SKIP for now — paid pay-per-use API, no real free tier, expensive
  for reads.
- **StockTwits:** SKIP for now — new developer API registration is currently paused.
- **Storage:** SQLite to start (single file, zero setup); migrate to Postgres only if
  it grows.

## Status
Scaffolding complete (folder skeleton + this file + `ROADMAP.md`). No feature code
written yet. See `ROADMAP.md` for the staged breakdown and which module is next.

```

### `ROADMAP.md`

```python
# ROADMAP

Staged breakdown of the project, by module. Everything is **TODO** until built.

**Reminder — every module follows the same loop** (see `CLAUDE.md`):
propose interface contract → **wait for approval** → write small module + one test →
**stop and show** → next module. Never jump ahead. `models/` stays locked until
explicitly unlocked.

---

## Stage 0 — Scaffolding
- [x] Folder skeleton (6 packages, each with a placeholder `__init__.py`).
- [x] `CLAUDE.md` (goal, priorities, working rules, architecture, data sources).
- [x] `ROADMAP.md` (this file).

## Stage 1 — `ingestion/`  ·  [ ] TODO
One fetcher per source. Each returns a **normalized format** AND stores the **raw
response separately**.
- [x] Prices fetcher (yfinance).  ← done: `ingestion/prices.py` + `tests/test_prices.py`
- [x] Ingest pipeline glue: `ingest_prices` + `ingest_fundamentals` (fetch + persist in one call).  ← `ingestion/pipeline.py` + `tests/test_pipeline.py`
- [x] Fundamentals fetcher (yfinance snapshot).  ← `ingestion/fundamentals.py` + `tests/test_fundamentals.py`
- [x] SEC EDGAR filings fetcher (free, no key — stdlib `urllib`).  ← `ingestion/edgar.py` + `tests/test_edgar.py`
- [x] Reddit fetcher (PRAW — wallstreetbets, stocks, investing).  ← `ingestion/reddit.py` + `tests/test_reddit.py`
- [x] News fetcher (Finnhub company-news, key via `FINNHUB_API_KEY`).  ← `ingestion/news.py` + `tests/test_news.py`
- [x] Retry (exponential backoff) + 15-min TTL cache for the yfinance fetchers.  ← `ingestion/_resilience.py` + `tests/test_resilience.py`
- [ ] **PARKED** — Reddit match confidence (cashtag/exact/loose tiers + `match` field on `RedditMention`; drop non-matches). Contract was approved in principle; revisit when Reddit credentials are available.
- [ ] (Skipped for now: Twitter/X — paid; StockTwits — registration paused.)

## Stage 2 — `storage/`  ·  [ ] IN PROGRESS
- [x] SQLite schema (raw store + normalized `price_bars` table).  ← `storage/store.py`
- [x] DB access layer (save/load price bars with upsert; save/load raw).  ← `storage/store.py` + `tests/test_store.py`
- [x] `fundamentals` table + `save_fundamentals`/`load_fundamentals` (snapshot data).  ← `storage/store.py`
- [x] `reddit_mentions` table + `save_reddit_mentions`/`load_reddit_mentions` + `ingest_reddit` glue.  ← `storage/store.py` + `ingestion/pipeline.py`
- [x] `news_articles` table + `save_news_articles`/`load_news_articles` + `ingest_news` glue.  ← `storage/store.py` + `ingestion/pipeline.py`
- [x] `filings` table + `save_filings`/`load_filings` + `ingest_filings` (metadata).  ← `storage/store.py` + `ingestion/pipeline.py`
- [x] `filing_sections` table + document fetcher with section extraction (business / risk factors / MD&A, extraction metadata + confidence flag, provenance instead of raw HTML, CLI dump script).  ← `ingestion/filing_docs.py` + `scripts/dump_filing_section.py` + `tests/test_filing_docs.py`
- [x] Foreign-issuer support: 20-F section map (Items 3/4/5) + widened default forms incl. amendments; section loads ordered by true filing date.  ← `ingestion/filing_docs.py` + `ingestion/pipeline.py`
- [ ] 40-F section extraction (wrapper form — content lives in exhibits: AIF + MD&A docs via the accession's index.json). Separate step; until then 40-F skips with a logged `no_section_map`.

## Stage 3 — `processing/`  ·  [ ] IN PROGRESS
- [x] LLM research briefs (`generate_brief`): what-it-does / bull / bear, grounded strictly in stored docs with per-claim `[S#]` citations, validated in code, cached in `briefs` by `(ticker, source_hash)`. Anthropic API, key via `ANTHROPIC_API_KEY` (.env supported, gitignored).  ← `processing/explain.py` + `tests/test_explain.py`
- [ ] Sentiment scoring of social/news text.  (deliberately skipped for now — the brief layer above is the product; revisit later)
- [ ] Aggregation per ticker per day: sentiment score, mention volume, change in
      mention volume.
- [ ] Hype / spike detection on mention volume.

## Stage 4 — `features/`  ·  [ ] TODO
- [ ] Assemble a feature vector per ticker per day (processing outputs + fundamentals).

## Stage 5 — `dashboard/`  ·  [ ] IN PROGRESS  ← the MVP, first useful deliverable
- [x] Minimal raw-data dashboard: ticker → fundamentals table, price chart, Reddit
      mentions, with a per-source "Fetch fresh data" button and clean degradation
      when Reddit creds are unset.  ← `dashboard/app.py` + `dashboard/views.py` + `tests/test_dashboard_views.py`
- [ ] Ticker in → fundamentals view.
- [ ] Sentiment timeline.
- [ ] Hype detection display.
- [ ] LLM-generated summary of what people are saying.

## Stage 6 — `models/`  ·  [ ] LOCKED
Do **not** build until the user explicitly says so.
- [ ] Relative ranking / classification (not price prediction).
- [ ] Always benchmarked vs dumb baselines (buy & hold, simple momentum).

---

## Suggested order (user decides)
`storage/` and `ingestion/` are the natural first two — everything downstream consumes
their output. A reasonable first concrete step is a single ingestion fetcher (e.g.
prices via yfinance) returning a normalized shape, then `storage/` to persist it. But
**the user picks the starting module.**

```

### `WALKTHROUGH.md`

```python
# WALKTHROUGH — how this project actually works

Written for you coming back after time away. `CLAUDE.md` holds the goal and the
rules; `ROADMAP.md` holds the checklist. **This file explains the code itself** —
the pattern every module follows, a file-by-file map, and how data travels from
an API into the database.

**Contents:**
[Status](#status) · [Running it](#running-it) · [The one pattern](#the-one-pattern-that-explains-everything) ·
[Data flow](#how-data-flows) · [File by file](#file-by-file) · [The database](#the-database) ·
[Working rules](#working-rules)

---

## Status

*Stages 1–2 built (ingestion + storage), minimal dashboard live. 19 tests passing.*

| Source | Fetch | Store | Notes |
|---|:---:|:---:|---|
| Prices (yfinance) | ✅ | ✅ | `price_bars` table, full pipeline glue |
| Fundamentals (yfinance) | ✅ | ✅ | `fundamentals` table, full pipeline glue |
| Reddit (PRAW) | ✅ | ✅ | `reddit_mentions` table, full pipeline glue |
| News (Finnhub) | ✅ | ✅ | `news_articles` table, full pipeline glue (needs `FINNHUB_API_KEY` to fetch live) |
| SEC filings (EDGAR) | ✅ | ✅ | `filings` (metadata) + `filing_sections` (extracted 10-K/10-Q text) |

**Ingestion is fully wired** — every source fetches *and* stores. Filing
documents get carved into business / risk-factors / MD&A text with a
per-section confidence flag; eyeball one with
`.venv/bin/python scripts/dump_filing_section.py AAPL risk_factors`.

**New — the explanation layer** (`processing/explain.py`): `generate_brief`
turns stored documents into three plain-English briefs — what the company
does, the bull case, the bear case — via the Anthropic API, strictly grounded:
every claim cites a stored source (`[S#]`), hallucinated citations are
rejected in code, thin sources produce an honest "sources don't support this"
instead of an invented thesis. Cached in the `briefs` table by
`(ticker, source_hash)` so identical stored data never re-bills. Needs
`ANTHROPIC_API_KEY` (env or gitignored `.env` at the repo root).

**Next in `processing/`:** sentiment scoring + per-day aggregation
(deliberately parked — the brief layer is the product). Also pending: the
dashboard tab that renders briefs with citation links.

`dashboard/` now holds the minimal app (`app.py` UI + `views.py` data layer —
see [File by file](#file-by-file)). `processing/`, `features/`, and `models/`
are still empty `__init__.py`s; `models/` stays **locked** until you say
otherwise. Parked: Reddit match-confidence tiers (see `ROADMAP.md`).

---

## The 30-second version

You give the tool a ticker. It collects data about that ticker from several
sources — prices, fundamentals, SEC filings, Reddit, news — and stores it in a
local SQLite file. Later it will score sentiment, detect hype spikes, and show it
all on a dashboard.

Built so far: the **collect-and-store layer**, a **minimal dashboard**, and the
first analysis piece — **grounded LLM research briefs** (`processing/explain.py`).
No sentiment scoring or hype detection yet. The dashboard shows stored raw data
per ticker and can trigger fresh ingests; briefs don't render there yet.

---

## Running it

```bash
cd ~/FindingStocks
.venv/bin/python -m pytest                    # 19 passed in a few seconds
.venv/bin/streamlit run dashboard/app.py      # the dashboard, on localhost:8501
```

The dashboard is the front door: enter a ticker, see what's stored, and hit
"Fetch fresh data" to ingest. Prices and fundamentals work with no setup at
all; the Reddit section shows "Reddit not configured" until you set the env
vars below. You can also drive it from a REPL:

```python
from storage import store
from ingestion.pipeline import ingest_prices

conn = store.get_connection()        # creates data/findingstocks.db
ingest_prices(conn, "AAPL")          # fetch a year of prices and save it
store.load_price_bars(conn, "AAPL")  # read it back
```

### Secrets live in the environment, never in the code

| Variable | Needed for | Where it comes from |
|---|---|---|
| `FINNHUB_API_KEY` | news | finnhub.io dashboard |
| `REDDIT_CLIENT_ID` | Reddit | reddit.com/prefs/apps → create a "script" app |
| `REDDIT_CLIENT_SECRET` | Reddit | same page |
| `REDDIT_USER_AGENT` | Reddit | optional; defaults to a sensible string |
| `SEC_EDGAR_USER_AGENT` | SEC filings | optional; SEC just wants a contact email |
| `ANTHROPIC_API_KEY` | research briefs | console.anthropic.com — env or `.env` file (gitignored) |

Prices and fundamentals need **no key at all** — yfinance is free and
unauthenticated. And no key is needed to run the tests: every test injects a fake
client, so the whole suite runs offline.

---

## The one pattern that explains everything

**Every fetcher in `ingestion/` is built identically.** Learn it once and all
five files read the same way:

```
fetch_<source>(ticker, ...options, <injectable client>) -> <Source>FetchResult
```

The returned object is always the same envelope:

| Field | What it holds |
|---|---|
| `source` | a string tag — `"yfinance"`, `"sec_edgar"`, `"reddit"`, `"finnhub"` |
| `ticker` | the cleaned, upper-cased ticker |
| `fetched_at` | UTC timestamp of the fetch |
| `normalized` | tidy dataclass records — the useful shape |
| `raw` | the untouched API response |

**Why `raw` always tags along:** it's a project rule. If you later want a field
you didn't normalize, you can mine it out of the stored raw responses instead of
re-fetching everything and re-spending your rate limits. The raw archive is the
safety net for every decision you haven't made yet.

Every fetcher also:

- **cleans the ticker** — `.strip().upper()`, raising `ValueError` if it's empty;
- **logs four events** — `fetch.start`, `fetch.ok`, `fetch.empty`, `fetch.error`;
- **takes an injectable client** so tests never touch the network;
- **reads secrets lazily** — only when a real fetch actually happens.

That last point is why the tests need no API keys: pass a fake client and the
code never goes looking for one.

---

## How data flows

```
      yfinance / SEC EDGAR / PRAW / Finnhub
                        |
                        v
              ingestion/<source>.py         fetch + normalize
                        |
                        v
         FetchResult { normalized, raw }    the envelope
                        |
                        v
              ingestion/pipeline.py         glue: raw -> text
                        |
             +----------+----------+
             |                     |
             v                     v
      save_<thing>()          save_raw()
      (typed table)           (raw archive)
             |                     |
             +----------+----------+
                        |
                        v
              data/findingstocks.db         SQLite, one file
```

The **pipeline** layer exists for exactly one reason: to keep `storage/` ignorant
of where data came from. yfinance returns a pandas DataFrame, PRAW returns Python
objects, Finnhub returns a JSON list — the pipeline turns each into a plain
string before handing it over. Storage only ever sees text.

---

## File by file

### `ingestion/` — one fetcher per source

| File | Source | Key? | Produces |
|---|---|:---:|---|
| `prices.py` | yfinance | no | `list[PriceBar]` — daily OHLCV |
| `fundamentals.py` | yfinance | no | one `FundamentalsSnapshot` — P/E, market cap, sector |
| `edgar.py` | SEC EDGAR | no | `list[Filing]` — 10-K, 10-Q, 8-K |
| `reddit.py` | PRAW | yes | `list[RedditMention]` — posts naming the ticker |
| `news.py` | Finnhub | yes | `list[NewsArticle]` — headlines + summaries |

Two details worth re-learning:

- **`fundamentals.py` is a snapshot, not a time series.** One fetch makes one
  row, stamped with today's date. Fetch it monthly and you accumulate history
  that way.
- **`edgar.py` makes two HTTP calls.** First it looks up the ticker's CIK number
  in SEC's public ticker map, then it fetches that company's filings. SEC's only
  requirement is a User-Agent carrying a contact email — no key, no account.

### `ingestion/pipeline.py` — fetch and save in one call

Six functions today: `ingest_prices`, `ingest_fundamentals`, `ingest_reddit`,
`ingest_news`, `ingest_filings`, `ingest_filing_sections`. Each does the same
three steps — fetch, save the normalized rows, save the raw payload — and
returns an `IngestSummary(ticker, rows_written, raw_id)`.
`ingest_filing_sections` is the one that composes: it reads the `filings`
table (so run `ingest_filings` first), downloads each document once, and
skips accessions already extracted — EDGAR documents are immutable.

### `ingestion/filing_docs.py` — 10-K/10-Q section extraction

Downloads a filing's primary document and extracts **business / risk_factors /
mdna** as plain text. The item numbers differ per form and the map handles it:
10-K (Items 1/1A/7), 10-Q (MD&A at Part I Item 2, no business section), and
20-F for foreign private issuers (Items 3/4/5) — amendments (`/A`) normalize
to the same maps. 40-F is a wrapper form whose content lives in exhibits;
it's skipped with a logged `no_section_map` until exhibit support lands.
Extraction is heuristic — headings are matched at line starts so mid-sentence
cross-references ("see Item 1A…") don't fool it, and the TOC loses to the real
section by body length. Every section records **word_count, matched_heading,
and a confidence flag** (`high`/`low`/`missing`) so a bad grab is visible in
the DB, never silent. Raw HTML (5–30 MB per filing) is deliberately *not*
stored — `raw_responses` gets a provenance record (URL, bytes, SHA-256)
instead, since EDGAR documents are immutable and re-fetchable. Downloads are
throttled to ≥0.5 s apart with a 10 s backoff on SEC's 403 rate-limit reply.

Eyeball an extraction any time:

```bash
.venv/bin/python scripts/dump_filing_section.py AAPL risk_factors
```

### `ingestion/_resilience.py` — retry + short-lived cache

`with_retry(fn)` calls `fn` and, on failure, retries with exponential backoff
plus jitter (1s, 2s, 4s… capped), logging each `retry.attempt`. `TTLCache`
holds successful results for 15 minutes. Both yfinance fetchers use them: a
repeat call for the same ticker within the window logs `fetch.cache_hit` and
returns the cached result — with its **original** `fetched_at`, so the
timestamp is honest about data age. Reddit/Finnhub/EDGAR don't use it yet.

### `ingestion/_logging.py` — structured logging

A thin wrapper over stdlib `logging` that emits lines like
`fetch.ok source=finnhub ticker=AAPL rows=12`.

The rule baked into its docstring: **never log credentials or payloads** — only
source, ticker, small counts, and exception *type names*. No API keys, no post
bodies, no `.info` dicts.

It deliberately does *not* configure output — that's an application's job, and
there's no application yet. Call `configure_logging()` in a REPL when you want to
watch it work.

### `dashboard/` — the minimal app

Two files, split so the logic stays testable without streamlit:

- **`views.py`** — the data layer. `load_ticker_view(conn, ticker)` reads what's
  stored (fundamentals, a year of price bars, up to 50 newest mentions) and
  never fetches. `ingest_ticker(conn, ticker)` runs the wired ingests with
  per-source isolation: each source reports `ok: N rows` or `error: <type>`,
  and Reddit reports a plain "not configured" message when the env vars are
  unset — one broken source never blocks the others.
- **`app.py`** — thin Streamlit UI over `views.py`: ticker input, fundamentals
  table, close-price line chart, mentions table with links, and a single
  "Fetch fresh data" button. Run it with
  `.venv/bin/streamlit run dashboard/app.py`.

### `tests/` — one test per module

19 tests, all offline. Each proves its module normalizes correctly, preserves
`raw`, and rejects an empty ticker. `tests/conftest.py` clears the yfinance
caches around every test so nothing leaks between them.

---

## The database

`storage/store.py` is the whole storage layer — schema and access in one file.
`get_connection()` opens the DB and creates any missing tables, so there's no
migration step to remember. Pass `":memory:"` for a throwaway DB; that's what the
tests use.

| Table | Primary key | One row per |
|---|---|---|
| `price_bars` | `(ticker, date)` | trading day |
| `fundamentals` | `(ticker, as_of)` | fetch-day snapshot |
| `reddit_mentions` | `(ticker, post_id)` | Reddit post |
| `news_articles` | `(ticker, article_id)` | news article |
| `filings` | `(ticker, accession_number)` | SEC filing (metadata) |
| `filing_sections` | `(accession_number, section)` | extracted 10-K/10-Q section + confidence |
| `briefs` | `(ticker, source_hash)` | generated research brief |
| `raw_responses` | auto `id` | raw payload ever fetched |

**Everything upserts.** Re-running an ingest never creates duplicates — it
overwrites the existing row. For Reddit that's deliberate: re-fetching a post
refreshes its score and comment count, so those numbers stay current rather than
freezing at whatever they were the first time.

`raw_responses` is the one table that only grows. It's an append-only archive,
one row per fetch, and it's what makes the "always keep the raw response" rule
real rather than aspirational.

---

## Working rules

From `CLAUDE.md`, and they exist because this project is big enough to get away
from you:

1. **One module at a time.** Propose the interface contract → wait for approval →
   write it with one test → stop and show.
2. **Never dump hundreds of lines at once.**
3. **Never touch `models/`** until you explicitly unlock it.
4. **When something's unclear, ask.** Don't assume.

The reason for contract-first: it's far cheaper to change your mind about a
dataclass shape in conversation than after three modules already depend on it.

---

*Keep this file current as modules land — it's what makes coming back after a
break cheap.*

```

### `bundle.py`

```python
from pathlib import Path

# הגדרות
OUTPUT_FILE = "full_project_context.md"
TARGET_EXTENSIONS = {".py", ".md"}  # אפשר להוסיף סיומות כמו .env.example, .toml, .sql
IGNORE_DIRS = {
    ".git",
    "__pycache__",
    "venv",
    ".venv",
    "env",
    ".pytest_cache",
    ".mypy_cache",
    ".idea",
    ".vscode",
    "dist",
    "build",
}


def should_ignore(path: Path) -> bool:
    return any(part in IGNORE_DIRS for part in path.parts)


def generate_tree(root: Path, prefix: str = "") -> list[str]:
    lines = []
    items = sorted(
        [p for p in root.iterdir() if not should_ignore(p)],
        key=lambda p: (p.is_file(), p.name.lower()),
    )

    for i, item in enumerate(items):
        is_last = i == len(items) - 1
        connector = "└── " if is_last else "├── "
        lines.append(f"{prefix}{connector}{item.name}")

        if item.is_dir():
            new_prefix = prefix + ("    " if is_last else "│   ")
            lines.extend(generate_tree(item, new_prefix))

    return lines


def bundle_project(root_dir: str = "."):
    root = Path(root_dir).resolve()
    markdown_lines = []

    # 1. יצירת עץ התיקיות
    markdown_lines.append(f"# Project Overview: `{root.name}`\n")
    markdown_lines.append("## Directory Tree\n```text")
    markdown_lines.extend(generate_tree(root))
    markdown_lines.append("```\n")

    # 2. מעבר על הקבצים ואיחוד התוכן
    markdown_lines.append("## Source Files\n")
    py_files = sorted(
        [
            p
            for p in root.rglob("*")
            if p.is_file()
            and p.suffix in TARGET_EXTENSIONS
            and not should_ignore(p)
        ]
    )

    for file_path in py_files:
        relative_path = file_path.relative_to(root)
        markdown_lines.append(f"### `{relative_path}`\n")
        markdown_lines.append("```python")

        try:
            content = file_path.read_text(encoding="utf-8")
            markdown_lines.append(content)
        except Exception as e:
            markdown_lines.append(f"# Error reading file: {e}")

        markdown_lines.append("```\n")

    # שמירה לקובץ
    out_path = root / OUTPUT_FILE
    out_path.write_text("\n".join(markdown_lines), encoding="utf-8")
    print(
        f"Bundled {len(py_files)} files into '{OUTPUT_FILE}' successfully."
    )


if __name__ == "__main__":
    bundle_project()
```

### `dashboard/__init__.py`

```python
"""Dashboard: the MVP deliverable.

Ticker in -> fundamentals + sentiment timeline + mention-volume spike (hype)
detection + an LLM-generated summary of what people are saying. Placeholder
package — not implemented yet.
"""

```

### `dashboard/app.py`

```python
"""Minimal research dashboard (Streamlit) — the first end-to-end deliverable.

Ticker in -> stored fundamentals, price chart, and recent Reddit mentions out.
Reads only from the local DB; the "Fetch fresh data" button runs the ingest
pipeline for the entered ticker. Run with:

    .venv/bin/streamlit run dashboard/app.py

All data access lives in ``dashboard/views.py`` (tested); this file is only UI.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

# Streamlit puts this file's folder on sys.path, not the project root, so make
# the project imports work no matter which directory the app is launched from.
_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from dashboard import views
from storage import store

st.set_page_config(page_title="FindingStocks", page_icon="📈", layout="wide")

st.title("FindingStocks")
st.caption("Ticker research: fundamentals, prices, and Reddit chatter from the local DB.")

ticker = st.text_input("Ticker", placeholder="e.g. AAPL").strip().upper()

if not ticker:
    st.info("Enter a ticker to see what's stored for it.")
    st.stop()

conn = store.get_connection()
view = views.load_ticker_view(conn, ticker)

# --- Ingest controls -------------------------------------------------------

if view.is_empty:
    st.warning(f"Nothing stored for {ticker} yet.")

if st.button("Fetch fresh data", type="primary"):
    with st.spinner(f"Ingesting {ticker}..."):
        results = views.ingest_ticker(conn, ticker)
    for source, outcome in results.items():
        if outcome.startswith("ok"):
            st.success(f"{source}: {outcome}")
        elif outcome.startswith("skipped"):
            st.info(f"{source}: {outcome}")
        else:
            st.error(f"{source}: {outcome}")
    view = views.load_ticker_view(conn, ticker)

# --- Fundamentals ----------------------------------------------------------

st.header("Fundamentals")
snap = view.fundamentals
if snap is None:
    st.caption(f"No fundamentals stored for {ticker}.")
else:
    st.caption(f"{snap.name or ticker} — snapshot from {snap.as_of.isoformat()}")
    labeled = {
        "Sector": snap.sector,
        "Industry": snap.industry,
        "Market cap": f"{snap.market_cap:,.0f}" if snap.market_cap else None,
        "Trailing P/E": snap.trailing_pe,
        "Forward P/E": snap.forward_pe,
        "Price / book": snap.price_to_book,
        "Dividend yield": snap.dividend_yield,
        "Profit margin": snap.profit_margin,
    }
    rows = [(k, str(v)) for k, v in labeled.items() if v is not None]
    st.table(pd.DataFrame(rows, columns=["Metric", "Value"]).set_index("Metric"))

# --- Prices ----------------------------------------------------------------

st.header("Price — last year")
if not view.price_bars:
    st.caption(f"No price data stored for {ticker}.")
else:
    frame = pd.DataFrame(
        {"date": [b.date for b in view.price_bars], "close": [b.close for b in view.price_bars]}
    ).set_index("date")
    st.line_chart(frame, y="close")
    latest = view.price_bars[-1]
    st.caption(f"{len(view.price_bars)} trading days · latest close {latest.close:,.2f} on {latest.date.isoformat()}")

# --- Reddit ----------------------------------------------------------------

st.header("Reddit mentions")
if not views.reddit_configured() and not view.mentions:
    st.info("Reddit not configured — set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET to enable this section.")
elif not view.mentions:
    st.caption(f"No Reddit mentions stored for {ticker}.")
else:
    frame = pd.DataFrame(
        {
            "date": [m.created_at.date().isoformat() for m in view.mentions],
            "subreddit": [m.subreddit for m in view.mentions],
            "title": [m.title for m in view.mentions],
            "score": [m.score for m in view.mentions],
            "comments": [m.num_comments for m in view.mentions],
            "link": [f"https://reddit.com{m.permalink}" for m in view.mentions],
        }
    )
    st.dataframe(
        frame,
        hide_index=True,
        column_config={"link": st.column_config.LinkColumn("link", display_text="open")},
    )

```

### `dashboard/views.py`

```python
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

```

### `features/__init__.py`

```python
"""Features: assemble a feature vector per ticker per day.

Combines outputs from processing (and fundamentals) into one row per
ticker per day. Placeholder package — not implemented yet.
"""

```

### `ingestion/__init__.py`

```python
"""Ingestion: one fetcher per source (prices, fundamentals, reddit, news).

Each fetcher returns a normalized format; the raw response is always stored
separately too. Placeholder package — no fetchers implemented yet.
"""

```

### `ingestion/_logging.py`

```python
"""Lightweight structured logging for ingestion (stdlib only, no new dependency).

Library code: modules get a logger via ``get_logger(__name__)`` and emit
consistent ``key=value`` event lines via ``info`` / ``warning`` / ``error``. We
deliberately **do not** attach handlers or call ``basicConfig`` here — configuring
output is the application's job. ``configure_logging`` is an opt-in convenience for
tests, a REPL, or a future entry point.

Never log credentials or payloads: emit only ``source``, ``ticker``, small counts,
and exception *types* — never User-Agents, client secrets, ``.info`` dicts, or post
bodies.
"""

from __future__ import annotations

import logging


def get_logger(name: str) -> logging.Logger:
    """Return the module-level logger for ``name`` (typically ``__name__``)."""
    return logging.getLogger(name)


def event(logger: logging.Logger, level: int, name: str, *, exc_info: bool = False, **fields) -> None:
    """Emit one structured event: ``name key=value key=value ...``.

    ``None``-valued fields are dropped. String building is skipped when the level
    is disabled. ``exc_info=True`` attaches the current traceback (errors only).
    """
    if not logger.isEnabledFor(level):
        return
    parts = " ".join(f"{k}={v}" for k, v in fields.items() if v is not None)
    message = f"{name} {parts}" if parts else name
    logger.log(level, message, exc_info=exc_info)


def info(logger: logging.Logger, name: str, **fields) -> None:
    """Emit an INFO event."""
    event(logger, logging.INFO, name, **fields)


def warning(logger: logging.Logger, name: str, **fields) -> None:
    """Emit a WARNING event (e.g. a fetch that returned empty/partial data)."""
    event(logger, logging.WARNING, name, **fields)


def error(logger: logging.Logger, name: str, *, exc_info: bool = True, **fields) -> None:
    """Emit an ERROR event, with the traceback attached by default."""
    event(logger, logging.ERROR, name, exc_info=exc_info, **fields)


def configure_logging(level: int = logging.INFO) -> None:
    """Opt-in handler setup for tests / REPL / a future entry point.

    Not called by library code. Safe to call once at process start.
    """
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

```

### `ingestion/_resilience.py`

```python
"""Retry with exponential backoff + a short-lived in-process cache (stdlib only).

Shared by the yfinance fetchers: ``with_retry`` survives transient failures
(rate limits, network hiccups), and ``TTLCache`` keeps repeated calls for the
same ticker from re-hitting the API within a short window. Both are small and
injectable (``sleep`` / ``clock``) so tests run instantly with no real waiting.
"""

from __future__ import annotations

import random
import time
from typing import Any, Callable, TypeVar

from ingestion import _logging

T = TypeVar("T")

_logger = _logging.get_logger(__name__)


def with_retry(
    fn: Callable[[], T],
    *,
    attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    sleep: Callable[[float], None] = time.sleep,
) -> T:
    """Call ``fn()``; on exception, retry with exponential backoff plus jitter.

    Delays double each attempt (1s, 2s, 4s, ... capped at ``max_delay``), with
    up to 10% random jitter so parallel callers don't retry in lockstep. Each
    failure logs a ``retry.attempt`` event; the final failure re-raises.
    """
    if attempts < 1:
        raise ValueError("attempts must be >= 1")

    for attempt in range(1, attempts + 1):
        try:
            return fn()
        except Exception as exc:
            if attempt == attempts:
                raise
            delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
            delay *= 1 + random.random() * 0.1
            _logging.warning(
                _logger, "retry.attempt", attempt=attempt, error=type(exc).__name__
            )
            sleep(delay)
    raise AssertionError("unreachable")  # for the type checker


class TTLCache:
    """In-process cache with per-entry expiry and a size cap.

    ``get`` returns ``None`` for a missing or expired key. ``put`` evicts the
    oldest entry once ``maxsize`` is exceeded. Not thread-safe — fine for the
    single-threaded fetchers and the Streamlit dashboard.
    """

    def __init__(
        self,
        ttl_seconds: float = 900.0,
        maxsize: int = 128,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._ttl = ttl_seconds
        self._maxsize = maxsize
        self._clock = clock
        self._entries: dict[Any, tuple[float, Any]] = {}

    def get(self, key: Any) -> Any | None:
        entry = self._entries.get(key)
        if entry is None:
            return None
        stored_at, value = entry
        if self._clock() - stored_at >= self._ttl:
            del self._entries[key]
            return None
        return value

    def put(self, key: Any, value: Any) -> None:
        self._entries.pop(key, None)  # re-inserting refreshes insertion order
        self._entries[key] = (self._clock(), value)
        while len(self._entries) > self._maxsize:
            del self._entries[next(iter(self._entries))]

    def clear(self) -> None:
        self._entries.clear()

```

### `ingestion/edgar.py`

```python
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

```

### `ingestion/filing_docs.py`

```python
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

```

### `ingestion/fundamentals.py`

```python
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

```

### `ingestion/news.py`

```python
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

```

### `ingestion/pipeline.py`

```python
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
from ingestion import filing_docs
from ingestion.edgar import fetch_filings
from ingestion.filing_docs import fetch_filing_sections

# Annual/quarterly report forms across domestic and foreign issuers, with
# amendments. 40-F is requested (metadata is worth storing) even though
# section extraction doesn't support it yet — those skip with a log line.
DEFAULT_DOC_FORMS = (
    "10-K", "10-Q", "20-F", "40-F",
    "10-K/A", "10-Q/A", "20-F/A", "40-F/A",
)
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
    forms: tuple[str, ...] = DEFAULT_DOC_FORMS,
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
            if not filing_docs.has_section_map(filing.form):
                _logging.warning(
                    _logger, "ingest.skip", source="sec_edgar_doc", ticker=ticker_clean,
                    form=filing.form, reason="no_section_map",
                )
                continue
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

```

### `ingestion/prices.py`

```python
"""Prices fetcher (yfinance).

Fetches historical daily OHLCV price data for a single ticker, returns a
normalized list of ``PriceBar`` records, and preserves the raw yfinance
response so it can be stored separately (per the project's "always keep the raw
response" rule). The storage module — built later — decides on-disk format.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any

import yfinance as yf

from ingestion import _logging
from ingestion._resilience import TTLCache, with_retry

SOURCE = "yfinance"
_DEFAULT_LOOKBACK_DAYS = 365
_logger = _logging.get_logger(__name__)

# Successful fetches are cached for 15 minutes so repeated calls for the same
# ticker/range (e.g. dashboard reruns) don't re-hit the API.
_cache = TTLCache()


@dataclass(frozen=True)
class PriceBar:
    """One trading day of normalized price data."""

    ticker: str
    date: date
    open: float
    high: float
    low: float
    close: float
    adj_close: float
    volume: int


@dataclass
class PriceFetchResult:
    """Result of a price fetch: normalized records plus the raw response."""

    source: str
    ticker: str
    fetched_at: datetime
    normalized: list[PriceBar]
    raw: Any


def fetch_prices(
    ticker: str,
    start: date | None = None,
    end: date | None = None,
) -> PriceFetchResult:
    """Fetch daily OHLCV prices for ``ticker`` between ``start`` and ``end``.

    Defaults to roughly the last year if the range is omitted. Raises
    ``ValueError`` for an empty ticker or when no data is returned.
    """
    ticker = ticker.strip().upper()
    if not ticker:
        raise ValueError("ticker must be a non-empty string")

    if end is None:
        end = date.today()
    if start is None:
        start = end - timedelta(days=_DEFAULT_LOOKBACK_DAYS)

    cache_key = (ticker, start.isoformat(), end.isoformat())
    cached = _cache.get(cache_key)
    if cached is not None:
        # fetched_at stays the original fetch time — honest about data age.
        _logging.info(_logger, "fetch.cache_hit", source=SOURCE, ticker=ticker)
        return cached

    _logging.info(_logger, "fetch.start", source=SOURCE, ticker=ticker)

    # auto_adjust=False keeps both the raw Close and a separate Adj Close.
    try:
        raw = with_retry(
            lambda: yf.Ticker(ticker).history(start=start, end=end, auto_adjust=False)
        )
    except Exception as exc:
        _logging.error(_logger, "fetch.error", source=SOURCE, ticker=ticker, error=type(exc).__name__)
        raise
    fetched_at = datetime.now(timezone.utc)

    if raw is None or raw.empty:
        _logging.warning(_logger, "fetch.empty", source=SOURCE, ticker=ticker)
        raise ValueError(f"no price data returned for ticker {ticker!r}")

    bars = _normalize(ticker, raw)
    _logging.info(_logger, "fetch.ok", source=SOURCE, ticker=ticker, rows=len(bars))
    result = PriceFetchResult(
        source=SOURCE,
        ticker=ticker,
        fetched_at=fetched_at,
        normalized=bars,
        raw=raw,
    )
    _cache.put(cache_key, result)
    return result


def _normalize(ticker: str, frame: Any) -> list[PriceBar]:
    """Turn a yfinance history DataFrame into a list of ``PriceBar`` records."""
    has_adj = "Adj Close" in frame.columns
    bars: list[PriceBar] = []
    for ts, row in frame.iterrows():
        close = float(row["Close"])
        bars.append(
            PriceBar(
                ticker=ticker,
                date=ts.date() if hasattr(ts, "date") else ts,
                open=float(row["Open"]),
                high=float(row["High"]),
                low=float(row["Low"]),
                close=close,
                adj_close=float(row["Adj Close"]) if has_adj else close,
                volume=int(row["Volume"]),
            )
        )
    return bars

```

### `ingestion/reddit.py`

```python
"""Reddit mentions fetcher (PRAW — read-only, free).

Searches the configured investing subreddits for posts mentioning a ticker,
normalizes each into a ``RedditMention`` record, and preserves a plain-dict copy
of every post's fields for separate raw storage. PRAW objects aren't
JSON-serializable, so ``raw`` is a list of dicts mirroring the attributes we read
(faithful and serializable).

Auth is read-only: a Reddit "script" app needs only client id/secret + a
User-Agent — no username/password. Credentials come from the environment
(``REDDIT_CLIENT_ID``, ``REDDIT_CLIENT_SECRET``, ``REDDIT_USER_AGENT``). The
``reddit`` client is injectable so tests run offline with no network and no
credentials.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from ingestion import _logging

SOURCE = "reddit"
_DEFAULT_SUBREDDITS = ("wallstreetbets", "stocks", "investing")
_logger = _logging.get_logger(__name__)


@dataclass(frozen=True)
class RedditMention:
    """One normalized Reddit post mentioning a ticker."""

    ticker: str
    post_id: str
    subreddit: str
    created_at: datetime
    title: str
    body: str
    score: int
    num_comments: int
    author: str | None
    url: str
    permalink: str


@dataclass
class RedditFetchResult:
    """Result of a Reddit fetch: normalized mentions plus raw post dicts."""

    source: str
    ticker: str
    fetched_at: datetime
    normalized: list[RedditMention]
    raw: Any


def fetch_reddit_mentions(
    ticker: str,
    subreddits: tuple[str, ...] | None = None,
    limit: int = 50,
    time_filter: str = "month",
    reddit: Any | None = None,
) -> RedditFetchResult:
    """Fetch recent Reddit posts mentioning ``ticker``.

    Searches ``subreddits`` (default: wallstreetbets, stocks, investing) for the
    ticker, newest first, capped at ``limit`` posts. ``time_filter`` bounds the
    search window (one of PRAW's: hour/day/week/month/year/all). ``reddit`` is an
    injectable PRAW client for tests. Raises ``ValueError`` for an empty ticker.
    """
    ticker = ticker.strip().upper()
    if not ticker:
        raise ValueError("ticker must be a non-empty string")

    subreddits = subreddits or _DEFAULT_SUBREDDITS

    _logging.info(_logger, "fetch.start", source=SOURCE, ticker=ticker)

    try:
        reddit = reddit or _make_reddit()
        multi = reddit.subreddit("+".join(subreddits))
        submissions = multi.search(ticker, sort="new", time_filter=time_filter, limit=limit)

        fetched_at = datetime.now(timezone.utc)
        normalized: list[RedditMention] = []
        raw: list[dict] = []
        for sub in submissions:
            normalized.append(_normalize(ticker, sub))
            raw.append(_raw_dict(sub))
    except Exception as exc:
        _logging.error(_logger, "fetch.error", source=SOURCE, ticker=ticker, error=type(exc).__name__)
        raise

    if not normalized:
        _logging.warning(_logger, "fetch.empty", source=SOURCE, ticker=ticker)
    else:
        _logging.info(_logger, "fetch.ok", source=SOURCE, ticker=ticker, rows=len(normalized))

    return RedditFetchResult(
        source=SOURCE,
        ticker=ticker,
        fetched_at=fetched_at,
        normalized=normalized,
        raw=raw,
    )


def _normalize(ticker: str, sub: Any) -> RedditMention:
    """Map a PRAW submission to a normalized ``RedditMention``."""
    author = getattr(sub, "author", None)
    return RedditMention(
        ticker=ticker,
        post_id=sub.id,
        subreddit=str(sub.subreddit),
        created_at=datetime.fromtimestamp(sub.created_utc, tz=timezone.utc),
        title=sub.title,
        body=sub.selftext or "",
        score=sub.score,
        num_comments=sub.num_comments,
        author=str(author) if author is not None else None,
        url=sub.url,
        permalink=sub.permalink,
    )


def _raw_dict(sub: Any) -> dict:
    """Capture a serializable dict of the post fields we read (PRAW objs aren't JSON)."""
    author = getattr(sub, "author", None)
    return {
        "id": sub.id,
        "subreddit": str(sub.subreddit),
        "created_utc": sub.created_utc,
        "title": sub.title,
        "selftext": sub.selftext,
        "score": sub.score,
        "num_comments": sub.num_comments,
        "author": str(author) if author is not None else None,
        "url": sub.url,
        "permalink": sub.permalink,
    }


def _make_reddit() -> Any:
    """Build a read-only PRAW client from environment credentials.

    Lazily imports ``praw`` so tests (which inject a fake client) need neither the
    dependency nor credentials. Raises ``RuntimeError`` if credentials are unset.
    """
    client_id = os.environ.get("REDDIT_CLIENT_ID")
    client_secret = os.environ.get("REDDIT_CLIENT_SECRET")
    user_agent = os.environ.get("REDDIT_USER_AGENT", "findingstocks dor.shneider@gmail.com")

    if not client_id or not client_secret:
        raise RuntimeError(
            "Reddit credentials missing: set REDDIT_CLIENT_ID and "
            "REDDIT_CLIENT_SECRET (and optionally REDDIT_USER_AGENT) in the "
            "environment. Create a free 'script' app at "
            "https://www.reddit.com/prefs/apps (read-only, no username/password)."
        )

    import praw  # lazy: only needed for live fetches

    return praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent,
        check_for_async=False,
    )

```

### `models/__init__.py`

```python
"""Models: predictive modeling layer. LOCKED.

DO NOT build until the user explicitly says so. Realistic framing only: NOT
"predict the exact price." Relative ranking / classification to prioritize
manual research, always benchmarked against dumb baselines (buy & hold, simple
momentum). Placeholder package — intentionally empty.
"""

```

### `processing/__init__.py`

```python
"""Processing: sentiment scoring + aggregation per ticker per day.

Produces, per ticker per day: a sentiment score, mention volume, and the change
in mention volume. Placeholder package — not implemented yet.
"""

```

### `processing/explain.py`

```python
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

```

### `scripts/dump_filing_section.py`

```python
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

```

### `storage/__init__.py`

```python
"""Storage: schema definitions + DB access layer.

SQLite to start (single file, zero setup); migrate to Postgres only if it grows.
Holds both raw responses and normalized records. Placeholder package — not
implemented yet.
"""

```

### `storage/store.py`

```python
"""SQLite storage layer.

Two responsibilities:
  * persist + read normalized price bars (``price_bars`` table), and
  * persist + read raw source responses (``raw_responses`` table), generically.

Storage stays source-agnostic about raw payloads: callers serialize their raw
response to text (for prices, ``raw.to_json()``) and pass it in. SQLite to start;
the access layer is thin so a later move to Postgres stays contained.
"""

from __future__ import annotations

import sqlite3
from datetime import date, datetime
from pathlib import Path

from ingestion.edgar import Filing
from ingestion.filing_docs import FilingSection
from ingestion.fundamentals import FundamentalsSnapshot
from ingestion.news import NewsArticle
from ingestion.prices import PriceBar
from ingestion.reddit import RedditMention

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = _PROJECT_ROOT / "data" / "findingstocks.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS price_bars (
    ticker    TEXT    NOT NULL,
    date      TEXT    NOT NULL,
    open      REAL    NOT NULL,
    high      REAL    NOT NULL,
    low       REAL    NOT NULL,
    close     REAL    NOT NULL,
    adj_close REAL    NOT NULL,
    volume    INTEGER NOT NULL,
    PRIMARY KEY (ticker, date)
);

CREATE TABLE IF NOT EXISTS briefs (
    ticker       TEXT NOT NULL,
    source_hash  TEXT NOT NULL,
    generated_at TEXT NOT NULL,
    model        TEXT NOT NULL,
    what_it_does TEXT NOT NULL,
    bull_case    TEXT NOT NULL,
    bear_case    TEXT NOT NULL,
    sources_json TEXT NOT NULL,
    PRIMARY KEY (ticker, source_hash)
);

CREATE TABLE IF NOT EXISTS raw_responses (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    source     TEXT NOT NULL,
    ticker     TEXT NOT NULL,
    fetched_at TEXT NOT NULL,
    payload    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS fundamentals (
    ticker         TEXT NOT NULL,
    as_of          TEXT NOT NULL,
    name           TEXT,
    sector         TEXT,
    industry       TEXT,
    market_cap     REAL,
    trailing_pe    REAL,
    forward_pe     REAL,
    price_to_book  REAL,
    dividend_yield REAL,
    profit_margin  REAL,
    PRIMARY KEY (ticker, as_of)
);

CREATE TABLE IF NOT EXISTS filings (
    ticker                  TEXT    NOT NULL,
    accession_number        TEXT    NOT NULL,
    cik                     INTEGER NOT NULL,
    form                    TEXT    NOT NULL,
    filing_date             TEXT    NOT NULL,
    primary_document        TEXT    NOT NULL,
    primary_doc_description TEXT,
    report_date             TEXT,
    filing_url              TEXT    NOT NULL,
    PRIMARY KEY (ticker, accession_number)
);

CREATE TABLE IF NOT EXISTS filing_sections (
    accession_number TEXT    NOT NULL,
    section          TEXT    NOT NULL,
    ticker           TEXT    NOT NULL,
    form             TEXT    NOT NULL,
    text             TEXT    NOT NULL,
    word_count       INTEGER NOT NULL,
    matched_heading  TEXT,
    confidence       TEXT    NOT NULL,
    extracted_at     TEXT    NOT NULL,
    PRIMARY KEY (accession_number, section)
);

CREATE TABLE IF NOT EXISTS news_articles (
    ticker       TEXT    NOT NULL,
    article_id   INTEGER NOT NULL,
    published_at TEXT    NOT NULL,
    headline     TEXT    NOT NULL,
    summary      TEXT    NOT NULL,
    source_name  TEXT    NOT NULL,
    url          TEXT    NOT NULL,
    PRIMARY KEY (ticker, article_id)
);

CREATE TABLE IF NOT EXISTS reddit_mentions (
    ticker       TEXT    NOT NULL,
    post_id      TEXT    NOT NULL,
    subreddit    TEXT    NOT NULL,
    created_at   TEXT    NOT NULL,
    title        TEXT    NOT NULL,
    body         TEXT    NOT NULL,
    score        INTEGER NOT NULL,
    num_comments INTEGER NOT NULL,
    author       TEXT,
    url          TEXT    NOT NULL,
    permalink    TEXT    NOT NULL,
    PRIMARY KEY (ticker, post_id)
);
"""


def get_connection(db_path: str | Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Open a SQLite connection and ensure the schema exists.

    Pass ``":memory:"`` for an ephemeral in-memory DB (used by tests). For a file
    path, the parent directory is created on demand.
    """
    if db_path != ":memory:":
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.executescript(_SCHEMA)
    conn.commit()
    return conn


def save_price_bars(conn: sqlite3.Connection, bars: list[PriceBar]) -> int:
    """Upsert price bars on ``(ticker, date)``; re-ingesting never duplicates.

    Returns the number of bars written.
    """
    rows = [
        (b.ticker, b.date.isoformat(), b.open, b.high, b.low, b.close, b.adj_close, b.volume)
        for b in bars
    ]
    conn.executemany(
        """
        INSERT INTO price_bars (ticker, date, open, high, low, close, adj_close, volume)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(ticker, date) DO UPDATE SET
            open=excluded.open, high=excluded.high, low=excluded.low,
            close=excluded.close, adj_close=excluded.adj_close, volume=excluded.volume
        """,
        rows,
    )
    conn.commit()
    return len(rows)


def load_price_bars(
    conn: sqlite3.Connection,
    ticker: str,
    start: date | None = None,
    end: date | None = None,
) -> list[PriceBar]:
    """Load price bars for ``ticker``, optionally bounded by ``start``/``end``."""
    query = "SELECT ticker, date, open, high, low, close, adj_close, volume FROM price_bars WHERE ticker = ?"
    params: list[object] = [ticker.strip().upper()]
    if start is not None:
        query += " AND date >= ?"
        params.append(start.isoformat())
    if end is not None:
        query += " AND date <= ?"
        params.append(end.isoformat())
    query += " ORDER BY date"

    return [
        PriceBar(
            ticker=row["ticker"],
            date=date.fromisoformat(row["date"]),
            open=row["open"],
            high=row["high"],
            low=row["low"],
            close=row["close"],
            adj_close=row["adj_close"],
            volume=row["volume"],
        )
        for row in conn.execute(query, params)
    ]


def save_brief(
    conn: sqlite3.Connection,
    ticker: str,
    source_hash: str,
    generated_at: datetime,
    model: str,
    what_it_does: str,
    bull_case: str,
    bear_case: str,
    sources_json: str,
) -> int:
    """Upsert one generated research brief, keyed by ``(ticker, source_hash)``.

    Plain fields rather than a dataclass so ``storage`` never imports from
    ``processing`` (which imports storage — a dataclass here would be a cycle).
    """
    conn.execute(
        """
        INSERT INTO briefs (
            ticker, source_hash, generated_at, model,
            what_it_does, bull_case, bear_case, sources_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(ticker, source_hash) DO UPDATE SET
            generated_at=excluded.generated_at, model=excluded.model,
            what_it_does=excluded.what_it_does, bull_case=excluded.bull_case,
            bear_case=excluded.bear_case, sources_json=excluded.sources_json
        """,
        (ticker, source_hash, generated_at.isoformat(), model,
         what_it_does, bull_case, bear_case, sources_json),
    )
    conn.commit()
    return 1


def load_brief(conn: sqlite3.Connection, ticker: str, source_hash: str) -> dict | None:
    """Load a cached brief for ``(ticker, source_hash)``, or ``None``."""
    row = conn.execute(
        "SELECT * FROM briefs WHERE ticker = ? AND source_hash = ?",
        (ticker.strip().upper(), source_hash),
    ).fetchone()
    return dict(row) if row is not None else None


def load_raw_payloads(
    conn: sqlite3.Connection, source: str, ticker: str, limit: int = 5
) -> list[str]:
    """Load the newest raw payloads for ``(source, ticker)``, newest first.

    Lets callers mine fields we never normalized (e.g. yfinance's
    ``longBusinessSummary``) out of the raw archive. Returns up to ``limit``
    payloads because one source tag can carry several shapes (yfinance stores
    both price frames and ``.info`` dicts under the same tag).
    """
    rows = conn.execute(
        "SELECT payload FROM raw_responses WHERE source = ? AND ticker = ? "
        "ORDER BY id DESC LIMIT ?",
        (source, ticker.strip().upper(), limit),
    ).fetchall()
    return [row["payload"] for row in rows]


def save_raw(
    conn: sqlite3.Connection,
    source: str,
    ticker: str,
    fetched_at: datetime,
    payload: str,
) -> int:
    """Store a raw (already-serialized) response. Returns its row id."""
    cur = conn.execute(
        "INSERT INTO raw_responses (source, ticker, fetched_at, payload) VALUES (?, ?, ?, ?)",
        (source, ticker, fetched_at.isoformat(), payload),
    )
    conn.commit()
    return int(cur.lastrowid)


def load_raw(conn: sqlite3.Connection, raw_id: int) -> dict | None:
    """Load a raw response by id, or ``None`` if it doesn't exist."""
    row = conn.execute(
        "SELECT id, source, ticker, fetched_at, payload FROM raw_responses WHERE id = ?",
        (raw_id,),
    ).fetchone()
    return dict(row) if row is not None else None


def save_fundamentals(conn: sqlite3.Connection, snapshot: FundamentalsSnapshot) -> int:
    """Upsert a fundamentals snapshot on ``(ticker, as_of)``. Returns rows written."""
    conn.execute(
        """
        INSERT INTO fundamentals (
            ticker, as_of, name, sector, industry, market_cap,
            trailing_pe, forward_pe, price_to_book, dividend_yield, profit_margin
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(ticker, as_of) DO UPDATE SET
            name=excluded.name, sector=excluded.sector, industry=excluded.industry,
            market_cap=excluded.market_cap, trailing_pe=excluded.trailing_pe,
            forward_pe=excluded.forward_pe, price_to_book=excluded.price_to_book,
            dividend_yield=excluded.dividend_yield, profit_margin=excluded.profit_margin
        """,
        (
            snapshot.ticker,
            snapshot.as_of.isoformat(),
            snapshot.name,
            snapshot.sector,
            snapshot.industry,
            snapshot.market_cap,
            snapshot.trailing_pe,
            snapshot.forward_pe,
            snapshot.price_to_book,
            snapshot.dividend_yield,
            snapshot.profit_margin,
        ),
    )
    conn.commit()
    return 1


def load_fundamentals(
    conn: sqlite3.Connection,
    ticker: str,
    as_of: date | None = None,
) -> FundamentalsSnapshot | None:
    """Load a fundamentals snapshot for ``ticker``.

    With ``as_of`` given, returns that specific snapshot; otherwise the most
    recent one. Returns ``None`` if nothing is stored.
    """
    ticker = ticker.strip().upper()
    if as_of is not None:
        row = conn.execute(
            "SELECT * FROM fundamentals WHERE ticker = ? AND as_of = ?",
            (ticker, as_of.isoformat()),
        ).fetchone()
    else:
        row = conn.execute(
            "SELECT * FROM fundamentals WHERE ticker = ? ORDER BY as_of DESC LIMIT 1",
            (ticker,),
        ).fetchone()

    if row is None:
        return None
    return FundamentalsSnapshot(
        ticker=row["ticker"],
        as_of=date.fromisoformat(row["as_of"]),
        name=row["name"],
        sector=row["sector"],
        industry=row["industry"],
        market_cap=row["market_cap"],
        trailing_pe=row["trailing_pe"],
        forward_pe=row["forward_pe"],
        price_to_book=row["price_to_book"],
        dividend_yield=row["dividend_yield"],
        profit_margin=row["profit_margin"],
    )


def save_filings(conn: sqlite3.Connection, filings: list[Filing]) -> int:
    """Upsert filings on ``(ticker, accession_number)``; re-ingesting never duplicates.

    Filings are immutable at SEC, but the upsert keeps re-ingests harmless.
    Returns rows written.
    """
    rows = [
        (
            f.ticker,
            f.accession_number,
            f.cik,
            f.form,
            f.filing_date.isoformat(),
            f.primary_document,
            f.primary_doc_description,
            f.report_date.isoformat() if f.report_date else None,
            f.filing_url,
        )
        for f in filings
    ]
    conn.executemany(
        """
        INSERT INTO filings (
            ticker, accession_number, cik, form, filing_date,
            primary_document, primary_doc_description, report_date, filing_url
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(ticker, accession_number) DO UPDATE SET
            cik=excluded.cik, form=excluded.form, filing_date=excluded.filing_date,
            primary_document=excluded.primary_document,
            primary_doc_description=excluded.primary_doc_description,
            report_date=excluded.report_date, filing_url=excluded.filing_url
        """,
        rows,
    )
    conn.commit()
    return len(rows)


def load_filings(
    conn: sqlite3.Connection,
    ticker: str,
    forms: tuple[str, ...] | None = None,
    limit: int | None = None,
) -> list[Filing]:
    """Load filings for ``ticker``, newest first, optionally filtered by form.

    Newest-first (unlike the timeline loaders) because filings are looked up as
    "the latest 10-K", not plotted over time.
    """
    query = (
        "SELECT ticker, accession_number, cik, form, filing_date, "
        "primary_document, primary_doc_description, report_date, filing_url "
        "FROM filings WHERE ticker = ?"
    )
    params: list[object] = [ticker.strip().upper()]
    if forms:
        placeholders = ", ".join("?" for _ in forms)
        query += f" AND form IN ({placeholders})"
        params.extend(forms)
    query += " ORDER BY filing_date DESC"
    if limit is not None:
        query += " LIMIT ?"
        params.append(limit)

    return [
        Filing(
            ticker=row["ticker"],
            cik=row["cik"],
            form=row["form"],
            filing_date=date.fromisoformat(row["filing_date"]),
            accession_number=row["accession_number"],
            primary_document=row["primary_document"],
            primary_doc_description=row["primary_doc_description"],
            report_date=date.fromisoformat(row["report_date"]) if row["report_date"] else None,
            filing_url=row["filing_url"],
        )
        for row in conn.execute(query, params)
    ]


def save_filing_sections(conn: sqlite3.Connection, sections: list[FilingSection]) -> int:
    """Upsert extracted sections on ``(accession_number, section)``.

    A re-extraction (e.g. after improving the heuristics) overwrites the old
    text and metadata. Returns rows written.
    """
    rows = [
        (
            s.accession_number,
            s.section,
            s.ticker,
            s.form,
            s.text,
            s.word_count,
            s.matched_heading,
            s.confidence,
            s.extracted_at.isoformat(),
        )
        for s in sections
    ]
    conn.executemany(
        """
        INSERT INTO filing_sections (
            accession_number, section, ticker, form, text,
            word_count, matched_heading, confidence, extracted_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(accession_number, section) DO UPDATE SET
            ticker=excluded.ticker, form=excluded.form, text=excluded.text,
            word_count=excluded.word_count, matched_heading=excluded.matched_heading,
            confidence=excluded.confidence, extracted_at=excluded.extracted_at
        """,
        rows,
    )
    conn.commit()
    return len(rows)


def load_filing_sections(
    conn: sqlite3.Connection,
    ticker: str,
    section: str | None = None,
    accession_number: str | None = None,
) -> list[FilingSection]:
    """Load extracted sections for ``ticker``, newest filing first.

    ``section`` and/or ``accession_number`` narrow the result. Ordering joins
    the ``filings`` table for the true filing date — accession-number order is
    NOT chronological (its prefix is the filing agent's CIK, which varies).
    """
    query = (
        "SELECT fs.accession_number, fs.section, fs.ticker, fs.form, fs.text, "
        "fs.word_count, fs.matched_heading, fs.confidence, fs.extracted_at "
        "FROM filing_sections fs "
        "LEFT JOIN filings f ON f.ticker = fs.ticker "
        "AND f.accession_number = fs.accession_number "
        "WHERE fs.ticker = ?"
    )
    params: list[object] = [ticker.strip().upper()]
    if section is not None:
        query += " AND fs.section = ?"
        params.append(section)
    if accession_number is not None:
        query += " AND fs.accession_number = ?"
        params.append(accession_number)
    query += " ORDER BY f.filing_date DESC, fs.section"

    return [
        FilingSection(
            accession_number=row["accession_number"],
            ticker=row["ticker"],
            form=row["form"],
            section=row["section"],
            text=row["text"],
            word_count=row["word_count"],
            matched_heading=row["matched_heading"],
            confidence=row["confidence"],
            extracted_at=datetime.fromisoformat(row["extracted_at"]),
        )
        for row in conn.execute(query, params)
    ]


def save_news_articles(conn: sqlite3.Connection, articles: list[NewsArticle]) -> int:
    """Upsert news articles on ``(ticker, article_id)``; re-ingesting never duplicates.

    Mutable fields (headline, summary, url) are refreshed on conflict, since
    publishers edit articles after the fact. Returns rows written.
    """
    rows = [
        (
            a.ticker,
            a.article_id,
            a.published_at.isoformat(),
            a.headline,
            a.summary,
            a.source_name,
            a.url,
        )
        for a in articles
    ]
    conn.executemany(
        """
        INSERT INTO news_articles (
            ticker, article_id, published_at, headline, summary, source_name, url
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(ticker, article_id) DO UPDATE SET
            published_at=excluded.published_at, headline=excluded.headline,
            summary=excluded.summary, source_name=excluded.source_name,
            url=excluded.url
        """,
        rows,
    )
    conn.commit()
    return len(rows)


def load_news_articles(
    conn: sqlite3.Connection,
    ticker: str,
    start: datetime | None = None,
    end: datetime | None = None,
) -> list[NewsArticle]:
    """Load news articles for ``ticker``, optionally bounded by ``published_at``.

    Ordered oldest-first so callers can build a timeline directly.
    """
    query = (
        "SELECT ticker, article_id, published_at, headline, summary, source_name, url "
        "FROM news_articles WHERE ticker = ?"
    )
    params: list[object] = [ticker.strip().upper()]
    if start is not None:
        query += " AND published_at >= ?"
        params.append(start.isoformat())
    if end is not None:
        query += " AND published_at <= ?"
        params.append(end.isoformat())
    query += " ORDER BY published_at"

    return [
        NewsArticle(
            ticker=row["ticker"],
            article_id=row["article_id"],
            published_at=datetime.fromisoformat(row["published_at"]),
            headline=row["headline"],
            summary=row["summary"],
            source_name=row["source_name"],
            url=row["url"],
        )
        for row in conn.execute(query, params)
    ]


def save_reddit_mentions(conn: sqlite3.Connection, mentions: list[RedditMention]) -> int:
    """Upsert Reddit mentions on ``(ticker, post_id)``; re-ingesting never duplicates.

    Mutable fields (score, comments, title, body) are refreshed on conflict, so a
    later fetch of the same post updates its running counts. Returns rows written.
    """
    rows = [
        (
            m.ticker,
            m.post_id,
            m.subreddit,
            m.created_at.isoformat(),
            m.title,
            m.body,
            m.score,
            m.num_comments,
            m.author,
            m.url,
            m.permalink,
        )
        for m in mentions
    ]
    conn.executemany(
        """
        INSERT INTO reddit_mentions (
            ticker, post_id, subreddit, created_at, title, body,
            score, num_comments, author, url, permalink
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(ticker, post_id) DO UPDATE SET
            subreddit=excluded.subreddit, created_at=excluded.created_at,
            title=excluded.title, body=excluded.body, score=excluded.score,
            num_comments=excluded.num_comments, author=excluded.author,
            url=excluded.url, permalink=excluded.permalink
        """,
        rows,
    )
    conn.commit()
    return len(rows)


def load_reddit_mentions(
    conn: sqlite3.Connection,
    ticker: str,
    start: datetime | None = None,
    end: datetime | None = None,
) -> list[RedditMention]:
    """Load Reddit mentions for ``ticker``, optionally bounded by ``created_at``.

    Ordered oldest-first so callers can build a timeline directly.
    """
    query = (
        "SELECT ticker, post_id, subreddit, created_at, title, body, "
        "score, num_comments, author, url, permalink "
        "FROM reddit_mentions WHERE ticker = ?"
    )
    params: list[object] = [ticker.strip().upper()]
    if start is not None:
        query += " AND created_at >= ?"
        params.append(start.isoformat())
    if end is not None:
        query += " AND created_at <= ?"
        params.append(end.isoformat())
    query += " ORDER BY created_at"

    return [
        RedditMention(
            ticker=row["ticker"],
            post_id=row["post_id"],
            subreddit=row["subreddit"],
            created_at=datetime.fromisoformat(row["created_at"]),
            title=row["title"],
            body=row["body"],
            score=row["score"],
            num_comments=row["num_comments"],
            author=row["author"],
            url=row["url"],
            permalink=row["permalink"],
        )
        for row in conn.execute(query, params)
    ]

```

### `tests/conftest.py`

```python
"""Shared test fixtures.

The yfinance fetchers keep module-level TTL caches; clear them around every
test so a fetch cached in one test can never satisfy (or pollute) another.
"""

import pytest

from ingestion import fundamentals, prices


@pytest.fixture(autouse=True)
def _clear_fetch_caches():
    prices._cache.clear()
    fundamentals._cache.clear()
    yield
    prices._cache.clear()
    fundamentals._cache.clear()

```

### `tests/test_dashboard_views.py`

```python
"""One test proving the dashboard data layer reads views and isolates failures.

Uses an in-memory DB and monkeypatched ingest functions — offline, no
credentials, and no streamlit import anywhere.
"""

from datetime import date, datetime, timezone

from dashboard import views
from ingestion.fundamentals import FundamentalsSnapshot
from ingestion.pipeline import IngestSummary
from ingestion.prices import PriceBar
from ingestion.reddit import RedditMention
from storage import store


def _seed(conn):
    store.save_fundamentals(
        conn,
        FundamentalsSnapshot(
            ticker="AAPL", as_of=date(2026, 8, 20), name="Apple Inc.",
            sector="Technology", industry="Consumer Electronics",
            market_cap=3e12, trailing_pe=30.5, forward_pe=28.0,
            price_to_book=45.2, dividend_yield=0.005, profit_margin=0.25,
        ),
    )
    store.save_price_bars(
        conn,
        [
            PriceBar("AAPL", date(2026, 8, 19), 100, 105, 99, 104, 103.5, 1_000_000),
            PriceBar("AAPL", date(2026, 8, 20), 104, 106, 103, 105, 104.5, 1_100_000),
        ],
    )
    store.save_reddit_mentions(
        conn,
        [
            RedditMention("AAPL", "old1", "stocks", datetime(2026, 8, 1, tzinfo=timezone.utc),
                          "older post", "", 5, 1, "u1", "u", "/r/stocks/old1"),
            RedditMention("AAPL", "new1", "wallstreetbets", datetime(2026, 8, 20, tzinfo=timezone.utc),
                          "newer post", "", 50, 9, "u2", "u", "/r/wallstreetbets/new1"),
        ],
    )


def test_load_ticker_view_and_ingest_ticker_isolate_failures(monkeypatch):
    conn = store.get_connection(":memory:")

    # Empty DB -> empty view.
    assert views.load_ticker_view(conn, "aapl").is_empty

    # Seeded DB -> view is shaped for display.
    _seed(conn)
    view = views.load_ticker_view(conn, "aapl")  # lower-case on purpose
    assert view.ticker == "AAPL"
    assert not view.is_empty
    assert view.fundamentals.name == "Apple Inc."
    assert [b.date for b in view.price_bars] == [date(2026, 8, 19), date(2026, 8, 20)]
    assert [m.post_id for m in view.mentions] == ["new1", "old1"]  # newest first

    # ingest_ticker: prices ok, fundamentals failing, reddit unconfigured.
    monkeypatch.setattr(
        views, "ingest_prices", lambda conn, t: IngestSummary(ticker="AAPL", rows_written=2, raw_id=1)
    )

    def boom(conn, t):
        raise ConnectionError("api down")

    monkeypatch.setattr(views, "ingest_fundamentals", boom)
    monkeypatch.delenv("REDDIT_CLIENT_ID", raising=False)
    monkeypatch.delenv("REDDIT_CLIENT_SECRET", raising=False)

    results = views.ingest_ticker(conn, "AAPL")
    assert results["prices"] == "ok: 2 rows"
    assert results["fundamentals"] == "error: ConnectionError"  # isolated, not raised
    assert results["reddit"] == views.REDDIT_NOT_CONFIGURED    # plain message, no attempt

    # With credentials set, reddit is attempted (and its failure is isolated too).
    monkeypatch.setenv("REDDIT_CLIENT_ID", "x")
    monkeypatch.setenv("REDDIT_CLIENT_SECRET", "y")
    monkeypatch.setattr(views, "ingest_reddit", boom)
    assert views.ingest_ticker(conn, "AAPL")["reddit"] == "error: ConnectionError"

```

### `tests/test_edgar.py`

```python
"""One test proving the EDGAR fetcher resolves CIK, normalizes filings, keeps raw.

HTTP is injected via a fake ``get_json`` returning canned JSON, so the test is
deterministic and runs offline (no network, no SEC calls).
"""

from datetime import date, datetime

import pytest

from ingestion import edgar
from ingestion.edgar import Filing, FilingsFetchResult

_TICKERS = {
    "0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."},
    "1": {"cik_str": 789019, "ticker": "MSFT", "title": "MICROSOFT CORP"},
}

_SUBMISSIONS = {
    "cik": "0000320193",
    "name": "Apple Inc.",
    "filings": {
        "recent": {
            "accessionNumber": ["0000320193-24-000123", "0000320193-24-000100"],
            "form": ["10-K", "8-K"],
            "filingDate": ["2024-11-01", "2024-08-02"],
            "reportDate": ["2024-09-28", ""],  # 8-K has no reportDate here
            "primaryDocument": ["aapl-20240928.htm", "ex99.htm"],
            "primaryDocDescription": ["10-K", ""],  # 8-K description empty
        }
    },
}


def _fake_get_json(url, user_agent):
    if "company_tickers" in url:
        return _TICKERS
    if "submissions" in url:
        return _SUBMISSIONS
    raise AssertionError(f"unexpected url: {url}")


def test_fetch_filings_normalizes_filters_and_keeps_raw():
    result = edgar.fetch_filings("aapl", get_json=_fake_get_json)  # lower-case on purpose

    # Envelope
    assert isinstance(result, FilingsFetchResult)
    assert result.source == "sec_edgar"
    assert result.ticker == "AAPL"
    assert isinstance(result.fetched_at, datetime)

    # First filing fully mapped, incl. constructed archive URL.
    assert len(result.normalized) == 2
    f0 = result.normalized[0]
    assert isinstance(f0, Filing)
    assert f0.cik == 320193
    assert f0.form == "10-K"
    assert f0.filing_date == date(2024, 11, 1)
    assert f0.report_date == date(2024, 9, 28)
    assert f0.accession_number == "0000320193-24-000123"
    assert f0.primary_document == "aapl-20240928.htm"
    assert f0.primary_doc_description == "10-K"
    assert f0.filing_url == (
        "https://www.sec.gov/Archives/edgar/data/320193/"
        "000032019324000123/aapl-20240928.htm"
    )

    # Second filing: empty reportDate and description map to None.
    f1 = result.normalized[1]
    assert f1.form == "8-K"
    assert f1.report_date is None
    assert f1.primary_doc_description is None

    # Form filtering keeps only the requested type.
    only_10k = edgar.fetch_filings("AAPL", forms=("10-K",), get_json=_fake_get_json)
    assert len(only_10k.normalized) == 1
    assert only_10k.normalized[0].form == "10-K"

    # Raw submissions JSON preserved untouched.
    assert result.raw == _SUBMISSIONS

    # Unknown ticker raises.
    with pytest.raises(ValueError):
        edgar.fetch_filings("ZZZZ", get_json=_fake_get_json)

```

### `tests/test_explain.py`

```python
"""One test proving briefs are grounded, validated, and cached.

A fake Anthropic client is injected, so the test is offline: no API key, no
network, no billing. It checks that the prompt is built only from stored
documents, that citation validation rejects hallucinated sources, and that
the cache prevents a second API call for identical stored data.
"""

import json
from datetime import date, datetime, timezone

import pytest

from ingestion.edgar import Filing
from ingestion.filing_docs import FilingSection
from ingestion.news import NewsArticle
from processing import explain
from processing.explain import Brief, GroundingError
from storage import store


class _FakeResponse:
    def __init__(self, payload: dict):
        self.stop_reason = "end_turn"
        self.content = [type("B", (), {"type": "text", "text": json.dumps(payload)})()]


class _FakeClient:
    """Mimics client.beta.messages.create; records calls, returns canned JSON."""

    def __init__(self, payload: dict):
        self.calls = []
        outer = self

        class _Messages:
            def create(self, **kwargs):
                outer.calls.append(kwargs)
                return _FakeResponse(payload)

        self.beta = type("Beta", (), {"messages": _Messages()})()


def _seed(conn):
    store.save_filings(conn, [Filing(
        ticker="POET", cik=1437424, form="20-F", filing_date=date(2026, 3, 31),
        accession_number="0001493152-26-014253", primary_document="form20-f.htm",
        primary_doc_description="20-F", report_date=date(2025, 12, 31),
        filing_url="https://www.sec.gov/Archives/edgar/data/1437424/x/form20-f.htm",
    )])
    store.save_filing_sections(conn, [FilingSection(
        accession_number="0001493152-26-014253", ticker="POET", form="20-F",
        section="risk_factors", text="We depend on a small number of customers.",
        word_count=8, matched_heading="Item 3. Key Information",
        confidence="high", extracted_at=datetime(2026, 8, 1, tzinfo=timezone.utc),
    )])
    store.save_news_articles(conn, [NewsArticle(
        ticker="POET", article_id=42,
        published_at=datetime.now(timezone.utc),
        headline="POET wins design contract", summary="A major win.",
        source_name="Reuters", url="https://example.com/poet",
    )])
    store.save_raw(
        conn, source="yfinance", ticker="POET",
        fetched_at=datetime(2026, 8, 1, tzinfo=timezone.utc),
        payload=json.dumps({"longBusinessSummary": "POET makes photonic chips."}),
    )


_GOOD = {
    "what_it_does": "POET makes photonic chips (light-based processors) [S1].",
    "bull_case": "A major design win suggests demand [S3].",
    "bear_case": "Revenue depends on a small number of customers [S2].",
}


def test_brief_is_grounded_validated_and_cached():
    conn = store.get_connection(":memory:")

    # Empty DB -> refuses to generate an ungrounded brief.
    with pytest.raises(ValueError):
        explain.generate_brief(conn, "POET", client=_FakeClient(_GOOD))

    _seed(conn)
    fake = _FakeClient(_GOOD)
    brief = explain.generate_brief(conn, "POET", client=fake)

    # The prompt is built strictly from stored documents.
    assert len(fake.calls) == 1
    call = fake.calls[0]
    prompt = call["messages"][0]["content"]
    assert "POET makes photonic chips." in prompt          # profile from raw archive
    assert "small number of customers" in prompt           # filing section
    assert "POET wins design contract" in prompt           # news
    assert "DISREGARD that" in call["system"]              # boilerplate-risk rule
    assert call["fallbacks"] == "default"                  # refusal fallback kept

    # Deterministic source ids: profile S1, filing S2, news S3 — with metadata.
    assert [s.kind for s in brief.sources] == ["profile", "filing:risk_factors", "news"]
    assert brief.sources[1].label == "20-F 0001493152-26-014253 · risk_factors"
    assert brief.sources[1].url.startswith("https://www.sec.gov/")
    assert brief.bear_case.endswith("[S2].")
    assert brief.model == explain.DEFAULT_MODEL

    # Cache: identical stored data -> no second API call, equal brief back.
    again = explain.generate_brief(conn, "POET", client=fake)
    assert len(fake.calls) == 1
    assert again == brief

    # A hallucinated citation is rejected and never cached.
    bad = dict(_GOOD, bear_case="Competitors are winning [S99].")
    conn2 = store.get_connection(":memory:")
    _seed(conn2)
    with pytest.raises(GroundingError):
        explain.generate_brief(conn2, "POET", client=_FakeClient(bad))
    # An uncited claim without the insufficiency phrase is rejected too...
    uncited = dict(_GOOD, bull_case="This company will surely grow.")
    with pytest.raises(GroundingError):
        explain.generate_brief(conn2, "POET", client=_FakeClient(uncited))
    # ...but a declared insufficiency passes without citations.
    honest = dict(_GOOD, bull_case="The stored sources do not support a bull thesis.")
    ok = explain.generate_brief(conn2, "POET", client=_FakeClient(honest))
    assert ok.bull_case.startswith("The stored sources")

```

### `tests/test_filing_docs.py`

```python
"""One test proving section extraction skips the TOC, maps forms, flags gaps.

The HTTP getter is injected with canned mini-filings, so the test is
deterministic and runs offline (no SEC calls, no throttling).
"""

from datetime import date, datetime

from ingestion import filing_docs
from ingestion.edgar import Filing
from ingestion.filing_docs import FilingSection, FilingSectionsResult


def _filing(form: str) -> Filing:
    return Filing(
        ticker="AAPL",
        cik=320193,
        form=form,
        filing_date=date(2025, 10, 31),
        accession_number="0000320193-25-000079",
        primary_document="aapl-20250927.htm",
        primary_doc_description=form,
        report_date=date(2025, 9, 27),
        filing_url="https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm",
    )


# Long bodies (>500 words) so the real sections clear the confidence bar.
_BUSINESS = "The company designs products. " * 130   # 650 words
_RISKS = "Demand may fluctuate materially. " * 130
_MDNA = "Revenue increased due to volume. " * 130

_TEN_K_HTML = f"""
<html><head><style>p {{ margin: 0 }}</style></head><body>
<script>var tracking = "ignore me";</script>
<div>TABLE OF CONTENTS</div>
<p>Item 1. Business</p>
<p>Item 1A. Risk Factors</p>
<p>Item 7. Management&#8217;s Discussion and Analysis</p>
<h2>Item 1. Business</h2>
<p>{_BUSINESS}</p>
<h2>Item 1A. Risk Factors</h2>
<p>{_RISKS}</p>
<h2>Item 7. Management&#8217;s Discussion and Analysis</h2>
<p>{_MDNA}</p>
<h2>Item 8. Financial Statements</h2>
<p>Not extracted.</p>
</body></html>
"""

# A 10-Q: MD&A lives at Part I Item 2; there's a Part II Item 2 decoy and
# no Risk Factors section at all (common when nothing material changed).
_TEN_Q_HTML = f"""
<html><body>
<h2>PART I</h2>
<h2>Item 2. Management&#8217;s Discussion and Analysis</h2>
<p>{_MDNA}</p>
<h2>PART II</h2>
<h2>Item 2. Unregistered Sales of Equity Securities</h2>
<p>None.</p>
</body></html>
"""

# A 20-F (foreign private issuer): risk in Item 3, business in Item 4,
# MD&A-equivalent in Item 5.
_TWENTY_F_HTML = f"""
<html><body>
<h2>Item 3. Key Information</h2>
<p>D. Risk Factors</p>
<p>{_RISKS}</p>
<h2>Item 4. Information on the Company</h2>
<p>{_BUSINESS}</p>
<h2>Item 5. Operating and Financial Review and Prospects</h2>
<p>{_MDNA}</p>
<h2>Item 6. Directors and Senior Management</h2>
<p>Not extracted.</p>
</body></html>
"""


def test_extracts_sections_skips_toc_and_flags_missing():
    # --- 10-K: all three sections, TOC entries not mistaken for bodies.
    result = filing_docs.fetch_filing_sections(
        _filing("10-K"), get_text=lambda url, ua: _TEN_K_HTML
    )
    assert isinstance(result, FilingSectionsResult)
    assert result.source == "sec_edgar_doc"
    by_name = {s.section: s for s in result.normalized}
    assert set(by_name) == {"business", "risk_factors", "mdna"}

    business = by_name["business"]
    assert isinstance(business, FilingSection)
    # Body is the real section (title line + prose), not the one-line TOC entry.
    assert business.text.startswith("Business")
    assert "The company designs products." in business.text
    assert "Demand may fluctuate" not in business.text   # stopped at next heading
    assert business.confidence == "high"
    assert business.word_count >= 500
    assert "Item 1" in business.matched_heading
    assert isinstance(business.extracted_at, datetime)

    assert "Demand may fluctuate" in by_name["risk_factors"].text
    assert "Revenue increased" in by_name["mdna"].text
    assert "Not extracted" not in by_name["mdna"].text  # stopped before Item 8

    # Raw is a provenance record, not the HTML (approved deviation).
    assert set(result.raw) == {"filing_url", "bytes", "sha256"}
    assert result.raw["bytes"] > 0 and len(result.raw["sha256"]) == 64

    # --- 10-Q: mdna maps to Item 2 and the Part II decoy loses; the absent
    # risk-factors section still yields a row, flagged missing.
    ten_q = filing_docs.fetch_filing_sections(
        _filing("10-Q"), get_text=lambda url, ua: _TEN_Q_HTML
    )
    q = {s.section: s for s in ten_q.normalized}
    assert set(q) == {"risk_factors", "mdna"}           # no "business" in a 10-Q
    assert "Revenue increased" in q["mdna"].text
    assert q["risk_factors"].confidence == "missing"
    assert q["risk_factors"].text == ""
    assert q["risk_factors"].word_count == 0

    # --- 20-F (foreign private issuer): Items 3/4/5 map to the same canonical
    # names, and an amendment ("20-F/A") normalizes to the same map.
    for form in ("20-F", "20-F/A"):
        tf = filing_docs.fetch_filing_sections(
            _filing(form), get_text=lambda url, ua: _TWENTY_F_HTML
        )
        f = {s.section: s for s in tf.normalized}
        assert set(f) == {"business", "risk_factors", "mdna"}
        assert "Demand may fluctuate" in f["risk_factors"].text
        assert "The company designs products." in f["business"].text
        assert "Revenue increased" in f["mdna"].text
        assert "Not extracted" not in f["mdna"].text     # stopped before Item 6
        assert all(s.confidence == "high" for s in tf.normalized)

    assert filing_docs.has_section_map("10-K/A")
    assert not filing_docs.has_section_map("40-F")       # wrapper form: not yet

    # Unmapped form types are rejected up front (the pipeline skips them).
    try:
        filing_docs.fetch_filing_sections(_filing("8-K"), get_text=lambda u, a: "")
        raise AssertionError("expected ValueError")
    except ValueError:
        pass

```

### `tests/test_fundamentals.py`

```python
"""One test proving the fundamentals fetcher maps .info to a snapshot and keeps raw.

yfinance is mocked, so the test is deterministic and runs offline (no network).
"""

from datetime import datetime

from ingestion import fundamentals
from ingestion.fundamentals import FundamentalsFetchResult, FundamentalsSnapshot


class _FakeTicker:
    """Stand-in for yfinance.Ticker exposing a fixed ``.info`` dict."""

    def __init__(self, symbol):
        self.symbol = symbol

    @property
    def info(self):
        return {
            "longName": "Apple Inc.",
            "sector": "Technology",
            "industry": "Consumer Electronics",
            "marketCap": 3_000_000_000_000,
            "trailingPE": 30.5,
            "forwardPE": 28.0,
            "priceToBook": 45.2,
            "dividendYield": 0.005,
            # profitMargins intentionally omitted -> should map to None
        }


def test_fetch_fundamentals_maps_snapshot_and_keeps_raw(monkeypatch):
    monkeypatch.setattr(fundamentals.yf, "Ticker", _FakeTicker)

    result = fundamentals.fetch_fundamentals("aapl")  # lower-case on purpose

    # Envelope
    assert isinstance(result, FundamentalsFetchResult)
    assert result.source == "yfinance"
    assert result.ticker == "AAPL"  # normalized to upper-case
    assert isinstance(result.fetched_at, datetime)

    # Normalized snapshot
    snap = result.normalized
    assert isinstance(snap, FundamentalsSnapshot)
    assert snap.ticker == "AAPL"
    assert snap.as_of == result.fetched_at.date()
    assert snap.name == "Apple Inc."
    assert snap.sector == "Technology"
    assert snap.industry == "Consumer Electronics"
    assert snap.market_cap == 3_000_000_000_000
    assert snap.trailing_pe == 30.5
    assert snap.forward_pe == 28.0
    assert snap.price_to_book == 45.2
    assert snap.dividend_yield == 0.005
    assert snap.profit_margin is None  # missing field maps to None

    # Raw response preserved (the full .info dict)
    assert isinstance(result.raw, dict)
    assert result.raw["longName"] == "Apple Inc."

```

### `tests/test_logging.py`

```python
"""One test proving the structured logging convention end-to-end.

Drives the prices fetcher (with yfinance faked) and inspects records via
pytest's ``caplog``: a success emits ``fetch.start`` + ``fetch.ok`` with the
right ``source``/``ticker`` fields; a transient failure emits a ``fetch.error``
ERROR carrying the exception type. No network, deterministic.
"""

import logging

import pandas as pd
import pytest

from ingestion import prices


class _FakeTicker:
    def __init__(self, frame):
        self._frame = frame

    def history(self, **kwargs):
        return self._frame


class _BoomTicker:
    def history(self, **kwargs):
        raise RuntimeError("network down")


def _frame():
    idx = pd.to_datetime(["2024-01-02", "2024-01-03"])
    return pd.DataFrame(
        {
            "Open": [100.0, 102.0],
            "High": [105.0, 106.0],
            "Low": [99.0, 101.0],
            "Close": [104.0, 103.0],
            "Adj Close": [103.5, 102.5],
            "Volume": [1_000_000, 1_200_000],
        },
        index=idx,
    )


def test_fetch_logs_start_and_ok(monkeypatch, caplog):
    monkeypatch.setattr(prices.yf, "Ticker", lambda t: _FakeTicker(_frame()))

    with caplog.at_level(logging.INFO, logger="ingestion.prices"):
        prices.fetch_prices("AAPL")

    messages = [r.getMessage() for r in caplog.records]
    assert any(
        m.startswith("fetch.start") and "source=yfinance" in m and "ticker=AAPL" in m
        for m in messages
    )
    assert any(m.startswith("fetch.ok") and "ticker=AAPL" in m and "rows=2" in m for m in messages)


def test_fetch_logs_error_with_exception_type(monkeypatch, caplog):
    monkeypatch.setattr(prices.yf, "Ticker", lambda t: _BoomTicker())

    with caplog.at_level(logging.ERROR, logger="ingestion.prices"):
        with pytest.raises(RuntimeError):
            prices.fetch_prices("AAPL")

    errors = [r for r in caplog.records if r.levelno == logging.ERROR]
    assert any(
        r.getMessage().startswith("fetch.error") and "error=RuntimeError" in r.getMessage()
        for r in errors
    )

```

### `tests/test_news.py`

```python
"""One test proving the news fetcher normalizes articles and keeps raw, offline.

A fake HTTP getter is injected, so the test is deterministic and runs with no
network and no Finnhub API key.
"""

from datetime import date, datetime, timezone

import pytest

from ingestion import news
from ingestion.news import NewsArticle, NewsFetchResult


def _canned_articles():
    # Shape mirrors Finnhub's /company-news response.
    return [
        {
            "category": "company",
            "datetime": 1_700_000_000,  # 2023-11-14T22:13:20Z
            "headline": "Apple unveils new chip",
            "id": 7891011,
            "image": "https://example.com/img.png",
            "related": "AAPL",
            "source": "Reuters",
            "summary": "Apple announced a new chip today.",
            "url": "https://example.com/apple-chip",
        },
        {
            "category": "company",
            "datetime": 1_700_100_000,
            "headline": "AAPL earnings preview",
            "id": 7891012,
            "image": "",
            "related": "AAPL",
            "source": "MarketWatch",
            "summary": "",  # some articles have no summary
            "url": "https://example.com/aapl-earnings",
        },
    ]


def test_fetch_news_normalizes_and_keeps_raw():
    calls = []

    def fake_http_get(url):
        calls.append(url)
        return _canned_articles()

    result = news.fetch_news(
        "aapl",  # lower-case on purpose
        start=date(2023, 11, 1),
        end=date(2023, 11, 30),
        http_get=fake_http_get,
    )

    # Envelope.
    assert isinstance(result, NewsFetchResult)
    assert result.source == "finnhub"
    assert result.ticker == "AAPL"
    assert isinstance(result.fetched_at, datetime)

    # Called the company-news endpoint with symbol + window; no token when injected.
    assert len(calls) == 1
    assert calls[0].startswith("https://finnhub.io/api/v1/company-news?")
    assert "symbol=AAPL" in calls[0]
    assert "from=2023-11-01" in calls[0]
    assert "to=2023-11-30" in calls[0]
    assert "token" not in calls[0]

    # First article fully mapped.
    assert len(result.normalized) == 2
    a0 = result.normalized[0]
    assert isinstance(a0, NewsArticle)
    assert a0.article_id == 7891011
    assert a0.published_at == datetime(2023, 11, 14, 22, 13, 20, tzinfo=timezone.utc)
    assert a0.headline == "Apple unveils new chip"
    assert a0.summary == "Apple announced a new chip today."
    assert a0.source_name == "Reuters"
    assert a0.url == "https://example.com/apple-chip"

    # Second article: empty summary stays "".
    assert result.normalized[1].summary == ""

    # Raw is the untouched JSON list.
    assert result.raw == _canned_articles()

    # Empty ticker raises.
    with pytest.raises(ValueError):
        news.fetch_news("  ", http_get=fake_http_get)

```

### `tests/test_pipeline.py`

```python
"""One test proving ingest_prices fetches and persists bars + raw in one call.

``fetch_prices`` is monkeypatched to a canned result, so the test is
deterministic and offline; it focuses on the fetch->store glue.
"""

import json
from datetime import date, datetime, timezone

import pandas as pd

from ingestion import pipeline
from ingestion.fundamentals import FundamentalsFetchResult, FundamentalsSnapshot
from ingestion.prices import PriceBar, PriceFetchResult
from ingestion.reddit import RedditFetchResult, RedditMention
from storage import store


def _canned_result():
    bars = [
        PriceBar("AAPL", date(2024, 1, 2), 100.0, 105.0, 99.0, 104.0, 103.5, 1_000_000),
        PriceBar("AAPL", date(2024, 1, 3), 102.0, 106.0, 101.0, 103.0, 102.5, 1_200_000),
    ]
    raw = pd.DataFrame(
        {"Close": [104.0, 103.0]},
        index=pd.to_datetime(["2024-01-02", "2024-01-03"]),
    )
    return PriceFetchResult(
        source="yfinance",
        ticker="AAPL",
        fetched_at=datetime(2024, 1, 3, 12, 0, tzinfo=timezone.utc),
        normalized=bars,
        raw=raw,
    )


def test_ingest_prices_fetches_and_persists(monkeypatch):
    canned = _canned_result()
    monkeypatch.setattr(pipeline, "fetch_prices", lambda ticker, start, end: canned)

    conn = store.get_connection(":memory:")
    summary = pipeline.ingest_prices(conn, "AAPL")

    # Summary reflects what was persisted.
    assert summary.ticker == "AAPL"
    assert summary.rows_written == 2
    assert summary.raw_id == 1

    # Bars are actually readable back.
    assert store.load_price_bars(conn, "AAPL") == canned.normalized

    # Raw is readable back, and is the serialized DataFrame.
    rec = store.load_raw(conn, summary.raw_id)
    assert rec["source"] == "yfinance"
    assert rec["payload"] == canned.raw.to_json(orient="split")


def _canned_fundamentals():
    snap = FundamentalsSnapshot(
        ticker="AAPL",
        as_of=date(2024, 1, 3),
        name="Apple Inc.",
        sector="Technology",
        industry="Consumer Electronics",
        market_cap=3_000_000_000_000,
        trailing_pe=30.5,
        forward_pe=28.0,
        price_to_book=45.2,
        dividend_yield=0.35,
        profit_margin=0.27,
    )
    raw = {"longName": "Apple Inc.", "marketCap": 3_000_000_000_000}
    return FundamentalsFetchResult(
        source="yfinance",
        ticker="AAPL",
        fetched_at=datetime(2024, 1, 3, 12, 0, tzinfo=timezone.utc),
        normalized=snap,
        raw=raw,
    )


def test_ingest_fundamentals_persists(monkeypatch):
    canned = _canned_fundamentals()
    monkeypatch.setattr(pipeline, "fetch_fundamentals", lambda ticker: canned)

    conn = store.get_connection(":memory:")
    summary = pipeline.ingest_fundamentals(conn, "AAPL")

    # Summary reflects what was persisted.
    assert summary.ticker == "AAPL"
    assert summary.rows_written == 1
    assert summary.raw_id == 1

    # Snapshot is readable back exactly.
    assert store.load_fundamentals(conn, "AAPL") == canned.normalized

    # Raw .info is readable back as serialized JSON.
    rec = store.load_raw(conn, summary.raw_id)
    assert rec["source"] == "yfinance"
    assert json.loads(rec["payload"])["marketCap"] == 3_000_000_000_000


def _canned_reddit():
    mentions = [
        RedditMention(
            ticker="AAPL",
            post_id="abc123",
            subreddit="wallstreetbets",
            created_at=datetime(2024, 1, 2, 10, 0, tzinfo=timezone.utc),
            title="AAPL to the moon",
            body="loaded calls",
            score=420,
            num_comments=69,
            author="ape_one",
            url="https://reddit.com/r/wallstreetbets/abc123",
            permalink="/r/wallstreetbets/comments/abc123/aapl/",
        ),
    ]
    raw = [{"id": "abc123", "score": 420}]
    return RedditFetchResult(
        source="reddit",
        ticker="AAPL",
        fetched_at=datetime(2024, 1, 3, 12, 0, tzinfo=timezone.utc),
        normalized=mentions,
        raw=raw,
    )


def test_ingest_reddit_persists(monkeypatch):
    canned = _canned_reddit()
    monkeypatch.setattr(
        pipeline,
        "fetch_reddit_mentions",
        lambda ticker, subreddits, limit, time_filter, reddit: canned,
    )

    conn = store.get_connection(":memory:")
    summary = pipeline.ingest_reddit(conn, "AAPL")

    # Summary reflects what was persisted.
    assert summary.ticker == "AAPL"
    assert summary.rows_written == 1
    assert summary.raw_id == 1

    # Mentions are readable back exactly.
    assert store.load_reddit_mentions(conn, "AAPL") == canned.normalized

    # Raw post list is readable back as serialized JSON.
    rec = store.load_raw(conn, summary.raw_id)
    assert rec["source"] == "reddit"
    assert json.loads(rec["payload"])[0]["id"] == "abc123"


def _canned_news():
    from ingestion.news import NewsArticle, NewsFetchResult

    articles = [
        NewsArticle(
            ticker="AAPL",
            article_id=7891011,
            published_at=datetime(2024, 1, 2, 9, 0, tzinfo=timezone.utc),
            headline="Apple unveils new chip",
            summary="Apple announced a new chip today.",
            source_name="Reuters",
            url="https://example.com/apple-chip",
        ),
    ]
    raw = [{"id": 7891011, "headline": "Apple unveils new chip"}]
    return NewsFetchResult(
        source="finnhub",
        ticker="AAPL",
        fetched_at=datetime(2024, 1, 3, 12, 0, tzinfo=timezone.utc),
        normalized=articles,
        raw=raw,
    )


def test_ingest_news_persists_with_upsert(monkeypatch):
    canned = _canned_news()
    monkeypatch.setattr(
        pipeline, "fetch_news", lambda ticker, start, end, http_get: canned
    )

    conn = store.get_connection(":memory:")
    summary = pipeline.ingest_news(conn, "AAPL")

    # Summary reflects what was persisted.
    assert summary.ticker == "AAPL"
    assert summary.rows_written == 1
    assert summary.raw_id == 1

    # Articles are readable back exactly.
    assert store.load_news_articles(conn, "AAPL") == canned.normalized

    # Raw article list is readable back as serialized JSON.
    rec = store.load_raw(conn, summary.raw_id)
    assert rec["source"] == "finnhub"
    assert json.loads(rec["payload"])[0]["id"] == 7891011

    # Re-ingesting upserts: still one row, refreshed headline wins.
    from dataclasses import replace

    canned.normalized[0] = replace(canned.normalized[0], headline="Apple unveils new chip (updated)")
    pipeline.ingest_news(conn, "AAPL")
    stored = store.load_news_articles(conn, "AAPL")
    assert len(stored) == 1
    assert stored[0].headline == "Apple unveils new chip (updated)"


def test_ingest_filings_persists_with_upsert_and_filtered_load(monkeypatch):
    from tests.test_edgar import _fake_get_json

    conn = store.get_connection(":memory:")
    summary = pipeline.ingest_filings(conn, "AAPL", get_json=_fake_get_json)

    # Summary reflects what was persisted (canned data has a 10-K and an 8-K).
    assert summary.ticker == "AAPL"
    assert summary.rows_written == 2
    assert summary.raw_id == 1

    # Newest first, and the form filter narrows.
    filings = store.load_filings(conn, "AAPL")
    assert [f.form for f in filings] == ["10-K", "8-K"]
    assert filings[0].filing_date == date(2024, 11, 1)
    only_10k = store.load_filings(conn, "AAPL", forms=("10-K",))
    assert [f.accession_number for f in only_10k] == ["0000320193-24-000123"]
    assert store.load_filings(conn, "AAPL", limit=1)[0].form == "10-K"

    # Raw submissions JSON is readable back.
    rec = store.load_raw(conn, summary.raw_id)
    assert rec["source"] == "sec_edgar"
    assert json.loads(rec["payload"])["cik"] == "0000320193"

    # Re-ingesting upserts: still two rows, no duplicates.
    pipeline.ingest_filings(conn, "AAPL", get_json=_fake_get_json)
    assert len(store.load_filings(conn, "AAPL")) == 2


def test_ingest_filing_sections_extracts_skips_stored(monkeypatch):
    from tests.test_edgar import _fake_get_json
    from tests.test_filing_docs import _TEN_K_HTML

    calls = []

    def fake_get_text(url, user_agent):
        calls.append(url)
        return _TEN_K_HTML

    conn = store.get_connection(":memory:")
    pipeline.ingest_filings(conn, "AAPL", get_json=_fake_get_json)  # canned 10-K + 8-K

    summary = pipeline.ingest_filing_sections(conn, "AAPL", forms=("10-K",), get_text=fake_get_text)
    assert summary.rows_written == 3  # business + risk_factors + mdna
    assert len(calls) == 1

    # Sections are readable back with their metadata.
    sections = store.load_filing_sections(conn, "AAPL")
    assert {s.section for s in sections} == {"business", "risk_factors", "mdna"}
    assert all(s.confidence == "high" for s in sections)
    assert store.load_filing_sections(conn, "AAPL", section="mdna")[0].word_count >= 500

    # Raw is the provenance record, not the HTML.
    rec = store.load_raw(conn, summary.raw_id)
    assert rec["source"] == "sec_edgar_doc"
    payload = json.loads(rec["payload"])
    assert set(payload) == {"filing_url", "bytes", "sha256"}
    assert _TEN_K_HTML not in rec["payload"]

    # Immutable documents: second run downloads nothing.
    again = pipeline.ingest_filing_sections(conn, "AAPL", forms=("10-K",), get_text=fake_get_text)
    assert again.rows_written == 0
    assert len(calls) == 1

```

### `tests/test_prices.py`

```python
"""One test proving the prices fetcher normalizes data and keeps the raw response.

yfinance is mocked, so the test is deterministic and runs offline (no network).
"""

from datetime import date, datetime

import pandas as pd

from ingestion import prices
from ingestion.prices import PriceBar, PriceFetchResult


class _FakeTicker:
    """Stand-in for yfinance.Ticker with a fixed two-day history."""

    def __init__(self, symbol):
        self.symbol = symbol

    def history(self, start=None, end=None, auto_adjust=False):
        index = pd.to_datetime(["2024-01-02", "2024-01-03"])
        return pd.DataFrame(
            {
                "Open": [100.0, 102.0],
                "High": [105.0, 106.0],
                "Low": [99.0, 101.0],
                "Close": [104.0, 103.0],
                "Adj Close": [103.5, 102.5],
                "Volume": [1_000_000, 1_200_000],
            },
            index=index,
        )


def test_fetch_prices_normalizes_and_keeps_raw(monkeypatch):
    monkeypatch.setattr(prices.yf, "Ticker", _FakeTicker)

    result = prices.fetch_prices("aapl")  # lower-case on purpose

    # Envelope
    assert isinstance(result, PriceFetchResult)
    assert result.source == "yfinance"
    assert result.ticker == "AAPL"  # normalized to upper-case
    assert isinstance(result.fetched_at, datetime)

    # Normalized records
    assert len(result.normalized) == 2
    first = result.normalized[0]
    assert isinstance(first, PriceBar)
    assert first.ticker == "AAPL"
    assert first.date == date(2024, 1, 2)
    assert (first.open, first.high, first.low, first.close) == (100.0, 105.0, 99.0, 104.0)
    assert first.adj_close == 103.5
    assert first.volume == 1_000_000

    # Raw response preserved untouched
    assert isinstance(result.raw, pd.DataFrame)
    assert list(result.raw.columns) == ["Open", "High", "Low", "Close", "Adj Close", "Volume"]
    assert len(result.raw) == 2

```

### `tests/test_reddit.py`

```python
"""One test proving the Reddit fetcher normalizes posts and keeps raw, offline.

A fake PRAW client is injected, so the test is deterministic and runs with no
network and no Reddit credentials.
"""

from datetime import datetime, timezone

import pytest

from ingestion import reddit
from ingestion.reddit import RedditFetchResult, RedditMention


class _FakeAuthor:
    def __init__(self, name):
        self._name = name

    def __str__(self):
        return self._name


class _FakeSubmission:
    def __init__(self, **kw):
        self.__dict__.update(kw)


class _FakeSubredditQuery:
    """Records the multi-subreddit name and the search args, returns canned posts."""

    def __init__(self, name, posts):
        self.name = name
        self._posts = posts
        self.search_calls = []

    def search(self, query, sort, time_filter, limit):
        self.search_calls.append((query, sort, time_filter, limit))
        return iter(self._posts)


class _FakeReddit:
    def __init__(self, posts):
        self._posts = posts
        self.last_query = None

    def subreddit(self, name):
        self.last_query = _FakeSubredditQuery(name, self._posts)
        return self.last_query


def _canned_posts():
    return [
        _FakeSubmission(
            id="abc123",
            subreddit="wallstreetbets",
            created_utc=1_700_000_000,  # 2023-11-14T22:13:20Z
            title="AAPL to the moon",
            selftext="loaded calls",
            score=420,
            num_comments=69,
            author=_FakeAuthor("ape_one"),
            url="https://reddit.com/r/wallstreetbets/abc123",
            permalink="/r/wallstreetbets/comments/abc123/aapl_to_the_moon/",
        ),
        _FakeSubmission(
            id="def456",
            subreddit="stocks",
            created_utc=1_700_100_000,
            title="Thoughts on AAPL earnings?",
            selftext="",  # link post, no body
            score=12,
            num_comments=4,
            author=None,  # deleted author
            url="https://reddit.com/r/stocks/def456",
            permalink="/r/stocks/comments/def456/thoughts_on_aapl_earnings/",
        ),
    ]


def test_fetch_reddit_mentions_normalizes_and_keeps_raw():
    fake = _FakeReddit(_canned_posts())
    result = reddit.fetch_reddit_mentions("aapl", reddit=fake)  # lower-case on purpose

    # Envelope.
    assert isinstance(result, RedditFetchResult)
    assert result.source == "reddit"
    assert result.ticker == "AAPL"
    assert isinstance(result.fetched_at, datetime)

    # Searched the default subreddits, combined, newest-first, with the ticker.
    assert fake.last_query.name == "wallstreetbets+stocks+investing"
    assert fake.last_query.search_calls == [("AAPL", "new", "month", 50)]

    # First post fully mapped.
    assert len(result.normalized) == 2
    m0 = result.normalized[0]
    assert isinstance(m0, RedditMention)
    assert m0.post_id == "abc123"
    assert m0.subreddit == "wallstreetbets"
    assert m0.created_at == datetime(2023, 11, 14, 22, 13, 20, tzinfo=timezone.utc)
    assert m0.title == "AAPL to the moon"
    assert m0.body == "loaded calls"
    assert m0.score == 420
    assert m0.num_comments == 69
    assert m0.author == "ape_one"

    # Second post: empty body stays "", deleted author maps to None.
    m1 = result.normalized[1]
    assert m1.body == ""
    assert m1.author is None

    # Raw is a serializable list of dicts, preserved per post.
    assert result.raw[0]["id"] == "abc123"
    assert result.raw[1]["author"] is None

    # Empty ticker raises.
    with pytest.raises(ValueError):
        reddit.fetch_reddit_mentions("  ", reddit=fake)

```

### `tests/test_resilience.py`

```python
"""One test proving retry backs off then succeeds, and the TTL cache serves hits.

Sleep and clock are injected, so the test runs instantly with no real waiting.
"""

import pytest

from ingestion._resilience import TTLCache, with_retry


def test_with_retry_backs_off_and_ttl_cache_serves_and_expires():
    # --- with_retry: two failures, then success, with doubling jittered delays.
    calls = {"n": 0}
    delays: list[float] = []

    def flaky():
        calls["n"] += 1
        if calls["n"] < 3:
            raise ConnectionError("transient")
        return "payload"

    assert with_retry(flaky, attempts=3, base_delay=1.0, sleep=delays.append) == "payload"
    assert calls["n"] == 3
    assert len(delays) == 2  # no sleep after the final success
    assert 1.0 <= delays[0] <= 1.1  # base delay + up to 10% jitter
    assert 2.0 <= delays[1] <= 2.2  # doubled

    # Exhausted attempts re-raise the last error.
    def always_fails():
        raise ConnectionError("still down")

    with pytest.raises(ConnectionError):
        with_retry(always_fails, attempts=2, sleep=delays.append)

    # --- TTLCache: hit within ttl, miss after expiry, oldest evicted at maxsize.
    now = {"t": 0.0}
    cache = TTLCache(ttl_seconds=10.0, maxsize=2, clock=lambda: now["t"])

    cache.put("AAPL", "cached-result")
    assert cache.get("AAPL") == "cached-result"

    now["t"] = 10.0  # ttl reached -> expired
    assert cache.get("AAPL") is None

    cache.put("A", 1)
    cache.put("B", 2)
    cache.put("C", 3)  # over maxsize -> "A" (oldest) evicted
    assert cache.get("A") is None
    assert cache.get("B") == 2
    assert cache.get("C") == 3

```

### `tests/test_store.py`

```python
"""One test proving the storage layer round-trips bars (with upsert) and raw responses.

Uses an in-memory SQLite DB, so it's deterministic and leaves nothing on disk.
"""

from datetime import date, datetime, timezone

from ingestion.prices import PriceBar
from ingestion.reddit import RedditMention
from storage import store


def _bars():
    return [
        PriceBar("AAPL", date(2024, 1, 2), 100.0, 105.0, 99.0, 104.0, 103.5, 1_000_000),
        PriceBar("AAPL", date(2024, 1, 3), 102.0, 106.0, 101.0, 103.0, 102.5, 1_200_000),
    ]


def test_store_round_trips_bars_and_raw():
    conn = store.get_connection(":memory:")
    bars = _bars()

    # Price bars round-trip exactly (dataclass equality, including date types).
    assert store.save_price_bars(conn, bars) == 2
    assert store.load_price_bars(conn, "AAPL") == bars

    # Upsert: saving the same bars again must not create duplicates.
    store.save_price_bars(conn, bars)
    assert len(store.load_price_bars(conn, "AAPL")) == 2

    # Date filtering works.
    second_only = store.load_price_bars(conn, "AAPL", start=date(2024, 1, 3))
    assert len(second_only) == 1 and second_only[0].date == date(2024, 1, 3)

    # Raw response round-trips.
    fetched_at = datetime(2024, 1, 3, 12, 0, tzinfo=timezone.utc)
    raw_id = store.save_raw(conn, "yfinance", "AAPL", fetched_at, '{"hello": "world"}')
    rec = store.load_raw(conn, raw_id)
    assert rec["source"] == "yfinance"
    assert rec["ticker"] == "AAPL"
    assert rec["fetched_at"] == fetched_at.isoformat()
    assert rec["payload"] == '{"hello": "world"}'

    # Missing id returns None.
    assert store.load_raw(conn, 9999) is None


def _mentions():
    return [
        RedditMention(
            ticker="AAPL",
            post_id="abc123",
            subreddit="wallstreetbets",
            created_at=datetime(2024, 1, 2, 10, 0, tzinfo=timezone.utc),
            title="AAPL to the moon",
            body="loaded calls",
            score=420,
            num_comments=69,
            author="ape_one",
            url="https://reddit.com/r/wallstreetbets/abc123",
            permalink="/r/wallstreetbets/comments/abc123/aapl/",
        ),
        RedditMention(
            ticker="AAPL",
            post_id="def456",
            subreddit="stocks",
            created_at=datetime(2024, 1, 5, 14, 0, tzinfo=timezone.utc),
            title="Thoughts on AAPL earnings?",
            body="",
            score=12,
            num_comments=4,
            author=None,
            url="https://reddit.com/r/stocks/def456",
            permalink="/r/stocks/comments/def456/aapl_earnings/",
        ),
    ]


def test_store_round_trips_reddit_mentions_with_upsert():
    conn = store.get_connection(":memory:")
    mentions = _mentions()

    # Mentions round-trip exactly (incl. datetime + None author), oldest-first.
    assert store.save_reddit_mentions(conn, mentions) == 2
    assert store.load_reddit_mentions(conn, "AAPL") == mentions

    # Upsert on (ticker, post_id): re-saving the same post refreshes its score,
    # never duplicates.
    bumped = mentions[0].__class__(**{**mentions[0].__dict__, "score": 999})
    store.save_reddit_mentions(conn, [bumped])
    loaded = store.load_reddit_mentions(conn, "AAPL")
    assert len(loaded) == 2
    assert loaded[0].score == 999

    # created_at filtering works.
    later = store.load_reddit_mentions(
        conn, "AAPL", start=datetime(2024, 1, 4, tzinfo=timezone.utc)
    )
    assert len(later) == 1 and later[0].post_id == "def456"

```
