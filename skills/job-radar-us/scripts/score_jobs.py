#!/usr/bin/env python3
"""Score normalized job postings against the job-radar profile.

This script performs no network access. Collection remains an agent workflow so
official pages that require browser interaction can be handled transparently.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROLE_RULES = [
    ("data-engineering", 30, ("data engineer", "data development engineer", "data platform engineer", "analytics engineer", "etl developer", "data warehouse engineer", "big data engineer")),
    ("data-analytics", 28, ("data analyst", "business data analyst", "product data analyst", "business intelligence", "bi engineer", "operations analyst", "supply chain analyst")),
    ("ai-agent-llm", 27, ("ai engineer", "artificial intelligence engineer", "llm engineer", "agent engineer", "applied ai", "nlp engineer", "machine learning engineer", "ml engineer")),
    ("algorithm", 24, ("algorithm engineer", "applied scientist", "data scientist", "machine learning scientist")),
    ("software-engineering", 21, ("software engineer", "software developer", "backend engineer", "platform engineer", "software development engineer", "sde")),
]

POSITIVE_AUTH = (
    "cpt", "opt", "visa sponsorship is available", "sponsorship available",
    "we sponsor", "will sponsor", "employment sponsorship",
)
NEGATIVE_AUTH = (
    "no sponsorship", "will not sponsor", "cannot sponsor", "unable to sponsor",
    "without sponsorship now or in the future", "not eligible for sponsorship",
)
EARLY_CAREER = ("new grad", "new graduate", "university graduate", "entry level", "early career", "campus")


def plain_text(value: Any) -> str:
    text = html.unescape(str(value or ""))
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def parse_time(value: Any) -> datetime | None:
    if not value:
        return None
    raw = str(value).strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError:
        try:
            parsed = datetime.strptime(raw[:10], "%Y-%m-%d")
        except ValueError:
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def stable_key(job: dict[str, Any]) -> str:
    if job.get("source_id"):
        raw = f"{job.get('source','')}|{job['source_id']}"
    elif job.get("url"):
        raw = str(job["url"]).split("?", 1)[0].rstrip("/")
    else:
        raw = "|".join(
            plain_text(job.get(field)).lower()
            for field in ("company", "title", "location")
        )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20]


def contains_phrase(text: str, phrase: str) -> bool:
    escaped = re.escape(phrase.lower()).replace(r"\ ", r"\s+")
    return re.search(rf"(?<![a-z0-9]){escaped}(?![a-z0-9])", text.lower()) is not None


def score_role(title: str) -> tuple[str | None, int]:
    normalized = title.lower()
    for family, score, phrases in ROLE_RULES:
        if any(contains_phrase(normalized, phrase) for phrase in phrases):
            return family, score
    return None, 0


def score_timing(title: str, description: str, employment_type: str) -> tuple[int, str]:
    text = f"{title} {description} {employment_type}".lower()
    if contains_phrase(text, "co-op") or contains_phrase(text, "coop"):
        return 20, "co-op"
    if contains_phrase(text, "intern") or contains_phrase(text, "internship"):
        return 20, "intern"
    if any(term in text for term in EARLY_CAREER):
        if "new grad" in text or "new graduate" in text or "university graduate" in text:
            return 18, "new-grad"
        return 15, "early-career"
    return 7, "general-full-time"


def matched_skills(text: str, skills: list[str]) -> list[str]:
    matches: list[str] = []
    lowered = text.lower()
    for skill in skills:
        if contains_phrase(lowered, skill):
            matches.append(skill)
    return matches


def score_location(location: str, workplace: str, tier: str, profile: dict[str, Any]) -> tuple[int, str]:
    prefs = profile["location_preferences"]
    location_l = location.lower()
    workplace_l = workplace.lower()
    if any(place.lower() in location_l for place in prefs["top"]):
        return 15, "Bay Area"
    if "california" in location_l or re.search(r"\bca\b", location_l):
        return 12, "California"
    if "remote" in location_l or "remote" in workplace_l:
        return 10, "US remote"
    score = 6
    if tier == "small":
        score -= int(prefs.get("small_company_outside_california_penalty", 8))
    return max(score, 0), "Other US / unknown"


def authorization_evidence(text: str) -> tuple[int, str, list[str]]:
    lowered = text.lower()
    blockers: list[str] = []
    negative = next((phrase for phrase in NEGATIVE_AUTH if phrase in lowered), None)
    if negative:
        blockers.append(f"Explicit sponsorship restriction: {negative}")
        return 0, "explicitly_does_not_support", blockers
    positive = next((phrase for phrase in POSITIVE_AUTH if phrase in lowered), None)
    if positive:
        return 10, f"explicit support signal: {positive}", blockers
    return 0, "not stated", blockers


def hard_blockers(title: str, description: str, profile: dict[str, Any]) -> list[str]:
    title_l = title.lower()
    text_l = f"{title} {description}".lower()
    blockers: list[str] = []
    for term in profile["hard_exclusions"]["seniority_terms"]:
        if contains_phrase(title_l, term) and "intern" not in title_l:
            blockers.append(f"Seniority mismatch: {term}")
            break
    for term in profile["hard_exclusions"]["authorization_terms"]:
        if term.lower() in text_l:
            blockers.append(f"Work authorization restriction: {term}")
            break
    for term in profile["hard_exclusions"]["clearance_terms"]:
        if term.lower() in text_l:
            blockers.append(f"Clearance restriction: {term}")
            break
    return blockers


def required_experience_years(text: str) -> int | None:
    """Return the strongest explicit minimum-years requirement found."""
    patterns = (
        r"(?<!\d)(\d{1,2})\s*\+\s*years?\s+(?:of\s+)?[^.;]{0,100}?experience",
        r"(?:at\s+least|minimum\s+of|minimum)\s+(\d{1,2})\s*\+?\s*years?[^.;]{0,100}?experience",
        r"(?<!\d)(\d{1,2})\s*(?:-|–|to)\s*\d{1,2}\s+years?\s+(?:of\s+)?[^.;]{0,100}?experience",
    )
    found: list[int] = []
    lowered = text.lower()
    for pattern in patterns:
        found.extend(int(value) for value in re.findall(pattern, lowered))
    return max(found) if found else None


def freshness_score(posted_at: Any, now: datetime) -> tuple[int, str]:
    parsed = parse_time(posted_at)
    if not parsed:
        return 0, "unknown"
    hours = max(0.0, (now - parsed).total_seconds() / 3600)
    if hours <= 72:
        return 5, f"{hours:.0f}h"
    if hours <= 168:
        return 3, f"{hours / 24:.1f}d"
    return 0, f"{hours / 24:.1f}d"


def score_job(job: dict[str, Any], profile: dict[str, Any], now: datetime, seen: set[str]) -> dict[str, Any]:
    title = plain_text(job.get("title"))
    description = plain_text(job.get("description"))
    location = plain_text(job.get("location"))
    tier = plain_text(job.get("company_tier") or "mid").lower()
    workplace = plain_text(job.get("workplace_type") or "unknown")
    employment = plain_text(job.get("employment_type") or "unknown")
    combined = f"{title} {description}"

    family, role_points = score_role(title)
    timing_points, recruiting_stage = score_timing(title, description, employment)
    skills = matched_skills(combined, profile["skills"])
    skill_points = min(20, len(skills) * 2)
    location_points, location_label = score_location(location, workplace, tier, profile)
    auth_points, auth_label, auth_blockers = authorization_evidence(combined)
    fresh_points, freshness = freshness_score(job.get("posted_at"), now)
    blockers = hard_blockers(title, description, profile) + auth_blockers

    minimum_years = required_experience_years(combined)
    experience_adjustment = 0
    if recruiting_stage not in ("intern", "co-op") and minimum_years is not None:
        if minimum_years >= 4:
            blockers.append(f"Experience mismatch: requires at least {minimum_years} years")
        elif minimum_years >= 2:
            experience_adjustment = -10
        elif minimum_years == 1:
            experience_adjustment = -4

    score = role_points + timing_points + skill_points + location_points + auth_points + fresh_points + experience_adjustment
    unpaid = "unpaid" in combined.lower() or "uncompensated" in combined.lower()
    if unpaid and score < int(profile["compensation"]["unpaid_allowed_only_if_score_at_least"]):
        blockers.append("Unpaid role below required 80-point fit threshold")

    if blockers:
        bucket = "blocked"
    elif score >= int(profile["high_match_threshold"]):
        bucket = "apply-first"
    elif score >= int(profile["review_threshold"]):
        bucket = "review"
    else:
        bucket = "low-fit"

    key = stable_key(job)
    return {
        **job,
        "title": title,
        "description": description,
        "location": location,
        "stable_key": key,
        "is_new": key not in seen,
        "score": min(100, max(0, score)),
        "bucket": bucket,
        "role_family": family,
        "recruiting_stage": recruiting_stage,
        "matched_skills": skills,
        "sponsorship_evidence": auth_label,
        "freshness": freshness,
        "location_fit": location_label,
        "required_experience_years": minimum_years,
        "blockers": blockers,
        "score_breakdown": {
            "role": role_points,
            "timing": timing_points,
            "skills": skill_points,
            "location": location_points,
            "authorization": auth_points,
            "freshness": fresh_points,
            "experience_adjustment": experience_adjustment,
        },
    }


def load_seen(path: Path | None) -> set[str]:
    if not path or not path.exists():
        return set()
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        payload = payload.get("seen_keys", [])
    return {str(item) for item in payload}


def write_csv(path: Path, jobs: list[dict[str, Any]]) -> None:
    fields = ["bucket", "score", "is_new", "company", "title", "location", "recruiting_stage", "role_family", "sponsorship_evidence", "freshness", "matched_skills", "blockers", "url"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for job in jobs:
            row = {field: job.get(field, "") for field in fields}
            row["matched_skills"] = "; ".join(job.get("matched_skills", []))
            row["blockers"] = "; ".join(job.get("blockers", []))
            writer.writerow(row)


def write_markdown(path: Path, jobs: list[dict[str, Any]], now: datetime) -> None:
    lines = [f"# US Job Radar — {now.date().isoformat()}", "", f"Scored roles: {len(jobs)}", ""]
    for bucket, heading in (("apply-first", "Apply first"), ("review", "Review"), ("low-fit", "Low fit"), ("blocked", "Blocked")):
        selected = [job for job in jobs if job["bucket"] == bucket]
        lines.extend([f"## {heading} ({len(selected)})", ""])
        for job in selected:
            lines.append(f"- **{job.get('company', '')} — [{job['title']}]({job.get('url', '')})** · {job['score']}/100 · {job['location'] or 'Location unknown'} · sponsorship: {job['sponsorship_evidence']}")
            if job["matched_skills"]:
                lines.append(f"  - Skills: {', '.join(job['matched_skills'][:10])}")
            if job["blockers"]:
                lines.append(f"  - Blockers: {'; '.join(job['blockers'])}")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jobs", type=Path, required=True, help="Normalized JSON array")
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--history", type=Path)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--now", help="ISO-8601 time for reproducible tests")
    args = parser.parse_args()

    jobs = json.loads(args.jobs.read_text(encoding="utf-8"))
    profile = json.loads(args.profile.read_text(encoding="utf-8"))
    if not isinstance(jobs, list):
        raise SystemExit("--jobs must contain a JSON array")
    now = parse_time(args.now) if args.now else datetime.now(timezone.utc)
    assert now is not None
    seen = load_seen(args.history)
    ranked = [score_job(job, profile, now, seen) for job in jobs]
    ranked.sort(key=lambda item: (item["bucket"] == "blocked", -item["score"], item.get("company", ""), item["title"]))

    args.out_dir.mkdir(parents=True, exist_ok=True)
    stamp = now.date().isoformat()
    (args.out_dir / f"job-radar-{stamp}.json").write_text(json.dumps(ranked, ensure_ascii=False, indent=2), encoding="utf-8")
    write_csv(args.out_dir / f"job-radar-{stamp}.csv", ranked)
    write_markdown(args.out_dir / f"job-radar-{stamp}.md", ranked, now)
    print(json.dumps({"jobs": len(ranked), "apply_first": sum(j["bucket"] == "apply-first" for j in ranked), "review": sum(j["bucket"] == "review" for j in ranked), "blocked": sum(j["bucket"] == "blocked" for j in ranked), "out_dir": str(args.out_dir)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
