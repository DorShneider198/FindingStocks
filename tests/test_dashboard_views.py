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
