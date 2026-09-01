"""Clinical trials fetcher (ClinicalTrials.gov — free, no API key).

Fetches a company's registered trials from the ClinicalTrials.gov v2 API,
normalizes each into a ``TrialSnapshot`` record, and preserves the raw JSON
for separate storage. The registry is queried by **company name** (sponsor),
not by ticker — the caller supplies both, and the ticker is carried through
for joining with the rest of the pipeline.

ClinicalTrials.gov is a live registry with no history: the API only returns
a trial's *current* state, and that state changes over time (recruiting →
completed, phase updates, terminations). So we store **observations, not
trials** — each record is a snapshot of one trial at one fetch time, and the
same trial fetched on two different dates yields two distinct records that
coexist in storage.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

SOURCE = "clinicaltrials"


@dataclass(frozen=True)
class TrialSnapshot:
    """One clinical trial as observed at one point in time.

    Identity is the trial's NCT number plus ``observed_at`` — the same trial
    seen on two dates is two records. ``company_name`` is the sponsor name the
    registry was queried by; ``last_updated`` is the registry's own last-update
    date, useful for telling whether anything changed between observations.
    """

    ticker: str
    company_name: str
    nct_id: str
    observed_at: datetime
    title: str
    status: str
    phase: str
    last_updated: date | None


@dataclass
class TrialsFetchResult:
    """Result of a trials fetch: normalized snapshots plus the raw JSON."""

    source: str
    ticker: str
    fetched_at: datetime
    normalized: list[TrialSnapshot]
    raw: Any
