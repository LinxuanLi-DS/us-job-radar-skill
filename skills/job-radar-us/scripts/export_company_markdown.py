#!/usr/bin/env python3
"""Export the configured company portfolio to a human-reviewable Markdown file."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path


LABELS = {"small": "Startups and Emerging Companies", "mid": "Growth-Stage and Mid-Sized Companies", "large": "Large and Established Employers"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--companies", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    with args.companies.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    counts = Counter(row["tier"] for row in rows)
    lines = [
        "# US Target Company Portfolio v0.2 (200 Companies)",
        "",
        "> Targets: Fall 2026 co-ops, Winter/Summer 2027 internships, and late-2027 through 2028 new-grad roles.",
        "> Prefer Bay Area or California startups; consider mid-sized and large employers across the United States. `expanded` marks the second portfolio batch.",
        "",
        f"Total: {len(rows)} companies — {counts['small']} startups, {counts['mid']} mid-sized companies, and {counts['large']} large employers.",
        "",
    ]
    for tier in ("small", "mid", "large"):
        selected = [row for row in rows if row["tier"] == tier]
        lines.extend([
            f"## {LABELS[tier]} ({len(selected)} companies)",
            "",
            "| # | Company | Focus | Location Hint | Batch | Review Status |",
            "|---:|---|---|---|---|---|",
        ])
        for row in selected:
            lines.append(f"| {row['id']} | {row['company']} | {row['focus']} | {row['geo_hint']} | {row['portfolio_version']} | {row['status']} |")
        lines.append("")
    lines.extend([
        "## Review Notes",
        "",
        "- Change `review` to `core`, `watch`, or `remove`. Scan core companies first.",
        "- Aerospace and defense roles often require citizenship or a security clearance; filter them using the exact posting language.",
        "- Company tiers are portfolio labels, not claims about current employee counts.",
        "- The portfolio may include non-US-headquartered companies that hire in the United States.",
    ])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
