---
name: job-radar-us
description: Manually scan a configured portfolio of US employers for newly published data, AI/LLM/agent, algorithm, and software-engineering roles; normalize official career-page results, identify roles not seen in prior scans, score fit against a configurable candidate profile and recruiting windows, and produce ranked Markdown/CSV reports. Use when the user asks to scan company careers, find high-match roles, rank jobs, or check co-op, internship, and new-grad openings.
---

# US Job Radar

## Required context

Read these files before scanning:

1. `references/profile.json` for role, timing, visa, location, and compensation preferences.
2. `references/companies.csv` for the approved employer portfolio and tier.
3. `references/scoring.md` for filtering, scoring, and evidence rules.
4. `references/sources.md` for ATS collection methods and timestamp semantics.

Use the expected graduation date from `references/profile.json`. Do not label a full-time new-grad role eligible when its stated degree or start-date rules exclude the configured graduation date.

## Scan workflow

1. Resolve the requested scan window. Default to the last 72 hours and call out the last 24 hours separately.
2. Read the prior state from `job-radar-output/state.json` when present. A role is new when its stable source ID or canonical URL was not present in the previous successful scan.
3. Scan official employer career pages only. Prefer public ATS data in this order:
   - Ashby public Job Postings API.
   - Greenhouse Job Board API.
   - Lever public Postings API.
   - The employer's official Workday or custom career page.
4. Use web search only to discover or recover an official source. Do not use LinkedIn, Indeed, reposting sites, or scraped job aggregators as the source of record.
5. Process companies in tiered batches. Scan `core` companies first, then `watch`, then remaining `review` companies; record failures instead of silently skipping them.
6. Use `scripts/collect_ats.py` after discovering a supported ATS provider and board slug. Normalize custom career-page results to the same schema.
7. Run the deterministic scorer. Review borderline results against the full job description before presenting them.
8. Write dated Markdown and CSV reports under `job-radar-output/` and update state only after a successful scan.

## Normalized job schema

Each collected job must include:

```json
{
  "company": "Company name",
  "company_tier": "small|mid|large",
  "title": "Job title",
  "location": "Location text",
  "url": "Official job URL",
  "description": "Plain-text job description",
  "posted_at": "ISO-8601 timestamp or null",
  "employment_type": "intern|co-op|full-time|other",
  "workplace_type": "remote|hybrid|onsite|unknown",
  "source": "ashby|greenhouse|lever|workday|official-custom",
  "source_id": "stable ATS identifier when available"
}
```

## Evidence rules

- Quote or closely paraphrase the job posting for degree timing, experience, work authorization, clearance, location, and compensation.
- Distinguish `explicitly supports`, `explicitly does not support`, and `not stated`. Never infer sponsorship from company reputation or historical H-1B filings.
- Treat Greenhouse `updated_at` as an update signal, not guaranteed original publication time.
- Prefer stable job IDs and first-seen history for systems without reliable publication dates.
- Do not submit applications, upload a resume, create accounts, or contact recruiters unless the user explicitly asks.

## Output contract

Start with counts: companies checked, successful sources, failed sources, total openings reviewed, new openings, and high matches.

Group ranked results into:

1. `Apply first` — score 80–100 and no unresolved hard blocker.
2. `Review` — score 65–79 or one material unknown such as sponsorship.
3. `Low fit / blocked` — include only concise rejection reasons.

For each recommended role show company, title, location, posting freshness, fit score, recruiting window, sponsorship evidence, three match reasons, up to three gaps, and the official link.

End with a source-failure table and the timestamp of the scan.

## Configuration changes

When the user approves company additions or removals, update `references/companies.csv` while preserving the 60 small / 60 mid / 80 large target unless the user changes that ratio. When preferences change, update `references/profile.json` and rerun validation.
