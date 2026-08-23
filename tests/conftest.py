"""Shared test fixtures.

The yfinance fetchers keep module-level TTL caches; clear them around every
test so a fetch cached in one test can never satisfy (or pollute) another.
"""

import pytest

from ingestion import fundamentals, prices


@pytest.fixture(autouse=True)
def _clear_fetch_caches():
    prices._cache.clear()
    fundamentals._cache.clear()
    yield
    prices._cache.clear()
    fundamentals._cache.clear()
