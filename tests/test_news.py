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
