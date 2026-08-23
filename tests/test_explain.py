"""One test proving briefs are grounded, validated, and cached.

A fake Anthropic client is injected, so the test is offline: no API key, no
network, no billing. It checks that the prompt is built only from stored
documents, that citation validation rejects hallucinated sources, and that
the cache prevents a second API call for identical stored data.
"""

import json
from datetime import date, datetime, timezone

import pytest

from ingestion.edgar import Filing
from ingestion.filing_docs import FilingSection
from ingestion.news import NewsArticle
from processing import explain
from processing.explain import Brief, GroundingError
from storage import store


class _FakeResponse:
    def __init__(self, payload: dict):
        self.stop_reason = "end_turn"
        self.content = [type("B", (), {"type": "text", "text": json.dumps(payload)})()]


class _FakeClient:
    """Mimics client.beta.messages.create; records calls, returns canned JSON."""

    def __init__(self, payload: dict):
        self.calls = []
        outer = self

        class _Messages:
            def create(self, **kwargs):
                outer.calls.append(kwargs)
                return _FakeResponse(payload)

        self.beta = type("Beta", (), {"messages": _Messages()})()


def _seed(conn):
    store.save_filings(conn, [Filing(
        ticker="POET", cik=1437424, form="20-F", filing_date=date(2026, 3, 31),
        accession_number="0001493152-26-014253", primary_document="form20-f.htm",
        primary_doc_description="20-F", report_date=date(2025, 12, 31),
        filing_url="https://www.sec.gov/Archives/edgar/data/1437424/x/form20-f.htm",
    )])
    store.save_filing_sections(conn, [FilingSection(
        accession_number="0001493152-26-014253", ticker="POET", form="20-F",
        section="risk_factors", text="We depend on a small number of customers.",
        word_count=8, matched_heading="Item 3. Key Information",
        confidence="high", extracted_at=datetime(2026, 8, 1, tzinfo=timezone.utc),
    )])
    store.save_news_articles(conn, [NewsArticle(
        ticker="POET", article_id=42,
        published_at=datetime.now(timezone.utc),
        headline="POET wins design contract", summary="A major win.",
        source_name="Reuters", url="https://example.com/poet",
    )])
    store.save_raw(
        conn, source="yfinance", ticker="POET",
        fetched_at=datetime(2026, 8, 1, tzinfo=timezone.utc),
        payload=json.dumps({"longBusinessSummary": "POET makes photonic chips."}),
    )


_GOOD = {
    "what_it_does": "POET makes photonic chips (light-based processors) [S1].",
    "bull_case": "A major design win suggests demand [S3].",
    "bear_case": "Revenue depends on a small number of customers [S2].",
}


def test_brief_is_grounded_validated_and_cached():
    conn = store.get_connection(":memory:")

    # Empty DB -> refuses to generate an ungrounded brief.
    with pytest.raises(ValueError):
        explain.generate_brief(conn, "POET", client=_FakeClient(_GOOD))

    _seed(conn)
    fake = _FakeClient(_GOOD)
    brief = explain.generate_brief(conn, "POET", client=fake)

    # The prompt is built strictly from stored documents.
    assert len(fake.calls) == 1
    call = fake.calls[0]
    prompt = call["messages"][0]["content"]
    assert "POET makes photonic chips." in prompt          # profile from raw archive
    assert "small number of customers" in prompt           # filing section
    assert "POET wins design contract" in prompt           # news
    assert "DISREGARD that" in call["system"]              # boilerplate-risk rule
    assert call["fallbacks"] == "default"                  # refusal fallback kept

    # Deterministic source ids: profile S1, filing S2, news S3 — with metadata.
    assert [s.kind for s in brief.sources] == ["profile", "filing:risk_factors", "news"]
    assert brief.sources[1].label == "20-F 0001493152-26-014253 · risk_factors"
    assert brief.sources[1].url.startswith("https://www.sec.gov/")
    assert brief.bear_case.endswith("[S2].")
    assert brief.model == explain.DEFAULT_MODEL

    # Cache: identical stored data -> no second API call, equal brief back.
    again = explain.generate_brief(conn, "POET", client=fake)
    assert len(fake.calls) == 1
    assert again == brief

    # A hallucinated citation is rejected and never cached.
    bad = dict(_GOOD, bear_case="Competitors are winning [S99].")
    conn2 = store.get_connection(":memory:")
    _seed(conn2)
    with pytest.raises(GroundingError):
        explain.generate_brief(conn2, "POET", client=_FakeClient(bad))
    # An uncited claim without the insufficiency phrase is rejected too...
    uncited = dict(_GOOD, bull_case="This company will surely grow.")
    with pytest.raises(GroundingError):
        explain.generate_brief(conn2, "POET", client=_FakeClient(uncited))
    # ...but a declared insufficiency passes without citations.
    honest = dict(_GOOD, bull_case="The stored sources do not support a bull thesis.")
    ok = explain.generate_brief(conn2, "POET", client=_FakeClient(honest))
    assert ok.bull_case.startswith("The stored sources")
