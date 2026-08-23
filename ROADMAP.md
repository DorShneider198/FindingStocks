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
- [ ] `filings` table + `save_filings`/`load_filings` + `ingest_filings` (approved, next).
- [ ] `filing_sections` table + document fetcher with section extraction (approved, after filings).

## Stage 3 — `processing/`  ·  [ ] TODO
- [ ] Sentiment scoring of social/news text.
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
