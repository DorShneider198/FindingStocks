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
