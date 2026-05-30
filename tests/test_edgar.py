"""One test proving the EDGAR fetcher resolves CIK, normalizes filings, keeps raw.

HTTP is injected via a fake ``get_json`` returning canned JSON, so the test is
deterministic and runs offline (no network, no SEC calls).
"""

from datetime import date, datetime

import pytest

from ingestion import edgar
from ingestion.edgar import Filing, FilingsFetchResult

_TICKERS = {
    "0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."},
    "1": {"cik_str": 789019, "ticker": "MSFT", "title": "MICROSOFT CORP"},
}

_SUBMISSIONS = {
    "cik": "0000320193",
    "name": "Apple Inc.",
    "filings": {
        "recent": {
            "accessionNumber": ["0000320193-24-000123", "0000320193-24-000100"],
            "form": ["10-K", "8-K"],
            "filingDate": ["2024-11-01", "2024-08-02"],
            "reportDate": ["2024-09-28", ""],  # 8-K has no reportDate here
            "primaryDocument": ["aapl-20240928.htm", "ex99.htm"],
            "primaryDocDescription": ["10-K", ""],  # 8-K description empty
        }
    },
}


def _fake_get_json(url, user_agent):
    if "company_tickers" in url:
        return _TICKERS
    if "submissions" in url:
        return _SUBMISSIONS
    raise AssertionError(f"unexpected url: {url}")


def test_fetch_filings_normalizes_filters_and_keeps_raw():
    result = edgar.fetch_filings("aapl", get_json=_fake_get_json)  # lower-case on purpose

    # Envelope
    assert isinstance(result, FilingsFetchResult)
    assert result.source == "sec_edgar"
    assert result.ticker == "AAPL"
    assert isinstance(result.fetched_at, datetime)

    # First filing fully mapped, incl. constructed archive URL.
    assert len(result.normalized) == 2
    f0 = result.normalized[0]
    assert isinstance(f0, Filing)
    assert f0.cik == 320193
    assert f0.form == "10-K"
    assert f0.filing_date == date(2024, 11, 1)
    assert f0.report_date == date(2024, 9, 28)
    assert f0.accession_number == "0000320193-24-000123"
    assert f0.primary_document == "aapl-20240928.htm"
    assert f0.primary_doc_description == "10-K"
    assert f0.filing_url == (
        "https://www.sec.gov/Archives/edgar/data/320193/"
        "000032019324000123/aapl-20240928.htm"
    )

    # Second filing: empty reportDate and description map to None.
    f1 = result.normalized[1]
    assert f1.form == "8-K"
    assert f1.report_date is None
    assert f1.primary_doc_description is None

    # Form filtering keeps only the requested type.
    only_10k = edgar.fetch_filings("AAPL", forms=("10-K",), get_json=_fake_get_json)
    assert len(only_10k.normalized) == 1
    assert only_10k.normalized[0].form == "10-K"

    # Raw submissions JSON preserved untouched.
    assert result.raw == _SUBMISSIONS

    # Unknown ticker raises.
    with pytest.raises(ValueError):
        edgar.fetch_filings("ZZZZ", get_json=_fake_get_json)
