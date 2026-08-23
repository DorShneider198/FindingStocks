"""Minimal research dashboard (Streamlit) — the first end-to-end deliverable.

Ticker in -> stored fundamentals, price chart, and recent Reddit mentions out.
Reads only from the local DB; the "Fetch fresh data" button runs the ingest
pipeline for the entered ticker. Run with:

    .venv/bin/streamlit run dashboard/app.py

All data access lives in ``dashboard/views.py`` (tested); this file is only UI.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

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
