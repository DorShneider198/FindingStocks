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
