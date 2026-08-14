#!/usr/bin/env python3
"""Validate the job-radar profile and 60/60/80 company portfolio."""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--companies", type=Path, required=True)
    args = parser.parse_args()

    profile = json.loads(args.profile.read_text(encoding="utf-8"))
    with args.companies.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    errors: list[str] = []
    ids = [row.get("id", "") for row in rows]
    names = [row.get("company", "").strip().lower() for row in rows]
    counts = Counter(row.get("tier") for row in rows)
    if len(rows) != 200:
        errors.append(f"expected 200 companies; found {len(rows)}")
    if len(ids) != len(set(ids)):
        errors.append("duplicate company ids")
    if len(names) != len(set(names)):
        errors.append("duplicate company names")
    if counts != Counter({"large": 80, "small": 60, "mid": 60}):
        errors.append(f"expected small=60 mid=60 large=80; found {dict(counts)}")
    graduation = profile.get("candidate", {}).get("expected_graduation", "")
    if not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", graduation):
        errors.append("expected_graduation must use YYYY-MM format")
    if not profile.get("role_priorities"):
        errors.append("role priorities are missing")

    result = {"valid": not errors, "companies": len(rows), "tiers": dict(counts), "errors": errors}
    print(json.dumps(result, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
