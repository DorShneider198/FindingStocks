"""One test proving section extraction skips the TOC, maps forms, flags gaps.

The HTTP getter is injected with canned mini-filings, so the test is
deterministic and runs offline (no SEC calls, no throttling).
"""

from datetime import date, datetime

from ingestion import filing_docs
from ingestion.edgar import Filing
from ingestion.filing_docs import FilingSection, FilingSectionsResult


def _filing(form: str) -> Filing:
    return Filing(
        ticker="AAPL",
        cik=320193,
        form=form,
        filing_date=date(2025, 10, 31),
        accession_number="0000320193-25-000079",
        primary_document="aapl-20250927.htm",
        primary_doc_description=form,
        report_date=date(2025, 9, 27),
        filing_url="https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm",
    )


# Long bodies (>500 words) so the real sections clear the confidence bar.
_BUSINESS = "The company designs products. " * 130   # 650 words
_RISKS = "Demand may fluctuate materially. " * 130
_MDNA = "Revenue increased due to volume. " * 130

_TEN_K_HTML = f"""
<html><head><style>p {{ margin: 0 }}</style></head><body>
<script>var tracking = "ignore me";</script>
<div>TABLE OF CONTENTS</div>
<p>Item 1. Business</p>
<p>Item 1A. Risk Factors</p>
<p>Item 7. Management&#8217;s Discussion and Analysis</p>
<h2>Item 1. Business</h2>
<p>{_BUSINESS}</p>
<h2>Item 1A. Risk Factors</h2>
<p>{_RISKS}</p>
<h2>Item 7. Management&#8217;s Discussion and Analysis</h2>
<p>{_MDNA}</p>
<h2>Item 8. Financial Statements</h2>
<p>Not extracted.</p>
</body></html>
"""

# A 10-Q: MD&A lives at Part I Item 2; there's a Part II Item 2 decoy and
# no Risk Factors section at all (common when nothing material changed).
_TEN_Q_HTML = f"""
<html><body>
<h2>PART I</h2>
<h2>Item 2. Management&#8217;s Discussion and Analysis</h2>
<p>{_MDNA}</p>
<h2>PART II</h2>
<h2>Item 2. Unregistered Sales of Equity Securities</h2>
<p>None.</p>
</body></html>
"""


def test_extracts_sections_skips_toc_and_flags_missing():
    # --- 10-K: all three sections, TOC entries not mistaken for bodies.
    result = filing_docs.fetch_filing_sections(
        _filing("10-K"), get_text=lambda url, ua: _TEN_K_HTML
    )
    assert isinstance(result, FilingSectionsResult)
    assert result.source == "sec_edgar_doc"
    by_name = {s.section: s for s in result.normalized}
    assert set(by_name) == {"business", "risk_factors", "mdna"}

    business = by_name["business"]
    assert isinstance(business, FilingSection)
    # Body is the real section (title line + prose), not the one-line TOC entry.
    assert business.text.startswith("Business")
    assert "The company designs products." in business.text
    assert "Demand may fluctuate" not in business.text   # stopped at next heading
    assert business.confidence == "high"
    assert business.word_count >= 500
    assert "Item 1" in business.matched_heading
    assert isinstance(business.extracted_at, datetime)

    assert "Demand may fluctuate" in by_name["risk_factors"].text
    assert "Revenue increased" in by_name["mdna"].text
    assert "Not extracted" not in by_name["mdna"].text  # stopped before Item 8

    # Raw is a provenance record, not the HTML (approved deviation).
    assert set(result.raw) == {"filing_url", "bytes", "sha256"}
    assert result.raw["bytes"] > 0 and len(result.raw["sha256"]) == 64

    # --- 10-Q: mdna maps to Item 2 and the Part II decoy loses; the absent
    # risk-factors section still yields a row, flagged missing.
    ten_q = filing_docs.fetch_filing_sections(
        _filing("10-Q"), get_text=lambda url, ua: _TEN_Q_HTML
    )
    q = {s.section: s for s in ten_q.normalized}
    assert set(q) == {"risk_factors", "mdna"}           # no "business" in a 10-Q
    assert "Revenue increased" in q["mdna"].text
    assert q["risk_factors"].confidence == "missing"
    assert q["risk_factors"].text == ""
    assert q["risk_factors"].word_count == 0

    # Unknown form types are rejected up front.
    try:
        filing_docs.fetch_filing_sections(_filing("8-K"), get_text=lambda u, a: "")
        raise AssertionError("expected ValueError")
    except ValueError:
        pass
