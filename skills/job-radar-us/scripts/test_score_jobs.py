#!/usr/bin/env python3
"""Small deterministic smoke test for score_jobs.py."""

from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from score_jobs import score_job


HERE = Path(__file__).resolve().parent
PROFILE = HERE.parent / "references" / "profile.json"


def main() -> int:
    profile = json.loads(PROFILE.read_text(encoding="utf-8"))
    now = datetime(2026, 8, 14, tzinfo=timezone.utc)
    strong = {
        "company": "Example Data Co",
        "company_tier": "small",
        "title": "Fall 2026 Data Engineer Co-op",
        "location": "San Jose, CA",
        "url": "https://example.com/jobs/1",
        "description": "Build Python and SQL ETL pipelines with data quality checks. CPT and OPT candidates are welcome.",
        "posted_at": "2026-08-13T12:00:00Z",
        "employment_type": "co-op",
        "workplace_type": "hybrid",
        "source": "ashby",
        "source_id": "1"
    }
    blocked = {
        **strong,
        "source_id": "2",
        "title": "Senior Staff Data Engineer",
        "description": "Must be a US citizen. Active security clearance required. No sponsorship.",
    }
    experienced = {
        **strong,
        "source_id": "3",
        "title": "Machine Learning Engineer",
        "description": "Build Python and PyTorch systems. 7+ years of professional engineering experience required.",
        "employment_type": "full-time",
    }
    internal_only = {
        **strong,
        "source_id": "4",
        "title": "Data Engineer",
        "description": "Collaborate with internal teams on Python and SQL pipelines.",
        "employment_type": "full-time",
    }
    a = score_job(strong, profile, now, set())
    b = score_job(blocked, profile, now, set())
    c = score_job(experienced, profile, now, set())
    d = score_job(internal_only, profile, now, set())
    assert a["bucket"] == "apply-first", a
    assert a["score"] >= 80, a
    assert b["bucket"] == "blocked", b
    assert len(b["blockers"]) >= 2, b
    assert c["bucket"] == "blocked", c
    assert c["required_experience_years"] == 7, c
    assert d["recruiting_stage"] == "general-full-time", d
    print(json.dumps({"ok": True, "strong_score": a["score"], "blocked_reasons": len(b["blockers"]), "experience_blocked": c["required_experience_years"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
