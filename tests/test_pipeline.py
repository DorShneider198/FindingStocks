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
