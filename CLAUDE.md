# CLAUDE.md — Stock Research & Sentiment Aggregation Tool

This file is the durable context for this project. Read it at the start of every
session and follow the working rules below without exception.

## What this is
A stock research / sentiment aggregation tool for a **private investor**. Today the
user researches stocks manually — reading Reddit, news, and financial data, then
forming a view and a sense of market sentiment. This tool automates that collection
and summarization. It is a large, multi-stage project to be built **slowly and
methodically**.

## Goal, in priority order
1. **PRIMARY — the MVP: a research / aggregation tool.** Give it a ticker and see:
   - fundamentals,
   - a sentiment timeline from social sources,
   - detection of spikes in mention volume (hype detection),
   - an LLM-generated summary of what people are saying.
2. **MUCH LATER, and completely separate — a predictive modeling layer.** Realistic
   framing ONLY — **not** "predict the exact price a year out." One-year returns are
   dominated by unpredictable events and have a very low signal-to-noise ratio. The
   realistic goal is **relative ranking / classification** to help prioritize manual
   research, **always benchmarked against dumb baselines** (buy & hold, simple
   momentum). **DO NOT build this until the user explicitly says so.**

## How we work — the single most important rule
This is a massive project. **Do not try to build it all at once.** Work **ONE module
at a time**. For every module:
1. **First propose a short interface contract** (what goes in, what comes out) and
   **WAIT for approval.**
2. **Only after approval** — write the module: small and focused, with **one test**
   that proves it works.
3. **Stop, show the user, and WAIT** before moving to the next module.

Hard rules:
- **Never** dump hundreds of lines at once.
- **Never** jump ahead to modules that weren't asked for.
- **Never** touch the `models/` layer until the user explicitly says so.
- If anything is unclear — **ask, don't assume.**

## Architecture (separate modules)
- `ingestion/`  — one fetcher per source (prices, fundamentals, reddit, news). Each
  returns a normalized format; **always store the raw response separately too.**
- `storage/`    — schema + DB access layer.
- `processing/` — sentiment scoring + aggregation per ticker per day (sentiment score,
  mention volume, change in volume).
- `features/`   — assemble a feature vector per ticker per day.
- `dashboard/`  — the first useful deliverable (the MVP).
- `models/`     — last, and separate. **Locked** (see priority #2).

## Data sources (current state, 2026)
- **Prices & fundamentals:** yfinance (free, fine to start).
- **Official filings:** SEC EDGAR (free).
- **Reddit:** PRAW (free, rate-limited) — subreddits like wallstreetbets, stocks,
  investing.
- **News:** a news API such as Finnhub or NewsAPI.
- **Twitter/X:** SKIP for now — paid pay-per-use API, no real free tier, expensive
  for reads.
- **StockTwits:** SKIP for now — new developer API registration is currently paused.
- **Storage:** SQLite to start (single file, zero setup); migrate to Postgres only if
  it grows.

## Status
Scaffolding complete (folder skeleton + this file + `ROADMAP.md`). No feature code
written yet. See `ROADMAP.md` for the staged breakdown and which module is next.
