"""One test proving the storage layer round-trips bars (with upsert) and raw responses.

Uses an in-memory SQLite DB, so it's deterministic and leaves nothing on disk.
"""

from datetime import date, datetime, timezone

from ingestion.prices import PriceBar
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
