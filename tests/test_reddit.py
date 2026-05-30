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
