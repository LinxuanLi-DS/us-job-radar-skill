#!/usr/bin/env python3
"""Collect and normalize public jobs from Ashby, Greenhouse, or Lever."""

from __future__ import annotations

import argparse
import json
import urllib.request
from pathlib import Path
from typing import Any


USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/140.0 Safari/537.36"


def fetch_json(url: str) -> Any:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def collect_ashby(board: str, company: str, tier: str) -> list[dict[str, Any]]:
    data = fetch_json(f"https://api.ashbyhq.com/posting-api/job-board/{board}?includeCompensation=true")
    jobs = []
    for item in data.get("jobs", []):
        if not item.get("isListed", True):
            continue
        jobs.append({
            "company": company,
            "company_tier": tier,
            "title": item.get("title"),
            "location": item.get("location"),
            "url": item.get("jobUrl") or item.get("applyUrl"),
            "description": item.get("descriptionPlain") or item.get("descriptionHtml"),
            "posted_at": item.get("publishedAt"),
            "employment_type": item.get("employmentType") or "unknown",
            "workplace_type": item.get("workplaceType") or ("remote" if item.get("isRemote") else "unknown"),
            "source": "ashby",
            "source_id": item.get("id") or item.get("jobUrl"),
        })
    return jobs


def collect_greenhouse(board: str, company: str, tier: str) -> list[dict[str, Any]]:
    data = fetch_json(f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs?content=true")
    jobs = []
    for item in data.get("jobs", []):
        jobs.append({
            "company": company,
            "company_tier": tier,
            "title": item.get("title"),
            "location": (item.get("location") or {}).get("name"),
            "url": item.get("absolute_url"),
            "description": item.get("content"),
            "posted_at": item.get("updated_at"),
            "employment_type": "unknown",
            "workplace_type": "unknown",
            "source": "greenhouse",
            "source_id": item.get("id"),
        })
    return jobs


def collect_lever(board: str, company: str, tier: str) -> list[dict[str, Any]]:
    data = fetch_json(f"https://api.lever.co/v0/postings/{board}?mode=json")
    jobs = []
    for item in data:
        categories = item.get("categories") or {}
        created = item.get("createdAt")
        if isinstance(created, (int, float)):
            from datetime import datetime, timezone
            created = datetime.fromtimestamp(created / 1000, tz=timezone.utc).isoformat()
        jobs.append({
            "company": company,
            "company_tier": tier,
            "title": item.get("text"),
            "location": categories.get("location"),
            "url": item.get("hostedUrl") or item.get("applyUrl"),
            "description": item.get("descriptionPlain") or item.get("description"),
            "posted_at": created,
            "employment_type": categories.get("commitment") or "unknown",
            "workplace_type": item.get("workplaceType") or "unknown",
            "source": "lever",
            "source_id": item.get("id"),
        })
    return jobs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", required=True, choices=("ashby", "greenhouse", "lever"))
    parser.add_argument("--board", required=True)
    parser.add_argument("--company", required=True)
    parser.add_argument("--tier", required=True, choices=("small", "mid", "large"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    collector = {"ashby": collect_ashby, "greenhouse": collect_greenhouse, "lever": collect_lever}[args.provider]
    jobs = collector(args.board, args.company, args.tier)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(jobs, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"provider": args.provider, "board": args.board, "jobs": len(jobs), "output": str(args.output)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
