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

*Stages 1–2 built (ingestion + storage), minimal dashboard live. 16 tests passing.*

| Source | Fetch | Store | Notes |
|---|:---:|:---:|---|
| Prices (yfinance) | ✅ | ✅ | `price_bars` table, full pipeline glue |
| Fundamentals (yfinance) | ✅ | ✅ | `fundamentals` table, full pipeline glue |
| Reddit (PRAW) | ✅ | ✅ | `reddit_mentions` table, full pipeline glue |
| News (Finnhub) | ✅ | ✅ | `news_articles` table, full pipeline glue (needs `FINNHUB_API_KEY` to fetch live) |
| SEC filings (EDGAR) | ✅ | ✅ | `filings` table (metadata only — form, dates, URL) |

**The gap:** filing *documents* — the actual 10-K/10-Q text — aren't downloaded
yet. We store where each filing lives, not what it says.

**Next step (approved):** a filing-document fetcher that downloads the primary
document and extracts business / risk factors / MD&A text into a
`filing_sections` table, with per-section extraction metadata and a CLI dump
for eyeballing the output.

**After that:** `processing/` — sentiment scoring and per-day aggregation. That's
the first module that *thinks* about the data instead of just moving it.

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

Right now the **collect-and-store half plus a minimal dashboard** exist. Nothing
analyzes anything yet — no sentiment, no hype detection — but the dashboard
shows the stored raw data per ticker and can trigger fresh ingests.

---

## Running it

```bash
cd ~/FindingStocks
.venv/bin/python -m pytest                    # 16 passed in a few seconds
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

Five functions today: `ingest_prices`, `ingest_fundamentals`, `ingest_reddit`,
`ingest_news`, `ingest_filings`. Each does the same three steps — fetch, save
the normalized rows, save the raw payload — and returns an
`IngestSummary(ticker, rows_written, raw_id)`.

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

16 tests, all offline. Each proves its module normalizes correctly, preserves
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
