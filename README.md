# US Job Radar Skill

An open-source Codex skill for scanning official US employer career pages, detecting newly listed roles, and ranking them against a configurable candidate profile.

The project ships with a 200-company portfolio focused on data engineering, analytics, AI/LLM agents, machine learning, algorithms, and software engineering.

## What it does

- Scans official Ashby, Greenhouse, Lever, Workday, and custom career pages.
- Normalizes postings into one stable JSON schema.
- Detects newly seen roles with source IDs and canonical URLs.
- Scores title fit, recruiting stage, skill overlap, location, work authorization, and freshness.
- Blocks obvious seniority, experience, citizenship, clearance, and sponsorship mismatches.
- Produces ranked Markdown, CSV, and JSON reports.
- Records source failures instead of treating blocked pages as zero openings.

## Portfolio

The included portfolio contains:

- 60 startups and emerging companies
- 60 growth-stage and mid-sized companies
- 80 large and established employers

Company tiers are job-search portfolio labels, not real-time employee-count claims. Review and customize `skills/job-radar-us/references/companies.csv` before using the portfolio.

## Repository structure

```text
us-job-radar-skill/
├── README.md
├── LICENSE
└── skills/
    └── job-radar-us/
        ├── SKILL.md
        ├── agents/openai.yaml
        ├── references/
        │   ├── companies.csv
        │   ├── profile.json
        │   ├── scoring.md
        │   └── sources.md
        └── scripts/
            ├── collect_ats.py
            ├── export_company_markdown.py
            ├── score_jobs.py
            ├── test_score_jobs.py
            └── validate_config.py
```

## Install

Copy the skill folder into your personal Codex skills directory:

```bash
cp -R skills/job-radar-us ~/.codex/skills/job-radar-us
```

Start a new Codex task after installation so the skill catalog refreshes.

## Configure

Edit `skills/job-radar-us/references/profile.json` before the first scan. Replace the example values for:

- graduation date and recruiting windows
- target role families
- work authorization and sponsorship needs
- preferred locations
- skills and tools
- compensation constraints

The checked-in profile is an anonymous example and contains no private user account data.

## Use

Example prompt:

```text
Use $job-radar-us to scan my target companies for roles published or first seen in the last 72 hours. Prioritize data engineering, analytics, AI/LLM, and software engineering internships or new-grad roles. Show work-authorization evidence and official application links.
```

Focused examples:

```text
Use $job-radar-us to scan only core Bay Area startups for Summer internships.
```

```text
Use $job-radar-us to compare this scan with the previous state and report only new, updated, or removed roles.
```

## Deterministic tools

Collect a public ATS board:

```bash
python3 skills/job-radar-us/scripts/collect_ats.py \
  --provider ashby \
  --board openai \
  --company OpenAI \
  --tier large \
  --output /tmp/openai-jobs.json
```

Score normalized jobs:

```bash
python3 skills/job-radar-us/scripts/score_jobs.py \
  --jobs /tmp/openai-jobs.json \
  --profile skills/job-radar-us/references/profile.json \
  --out-dir job-radar-output
```

Validate the configuration:

```bash
python3 skills/job-radar-us/scripts/validate_config.py \
  --profile skills/job-radar-us/references/profile.json \
  --companies skills/job-radar-us/references/companies.csv
```

Run the scoring smoke test:

```bash
python3 skills/job-radar-us/scripts/test_score_jobs.py
```

## Scoring model

The deterministic scorer allocates up to 100 points:

| Signal | Maximum |
|---|---:|
| Role-family match | 30 |
| Recruiting-stage match | 20 |
| Skill overlap | 20 |
| Location fit | 15 |
| Work-authorization evidence | 10 |
| Freshness | 5 |

Explicit requirements for four or more years of relevant experience are blocked by default for the included early-career example profile. Requirements for one to three years receive a score penalty.

## Privacy and safety

- Use official employer sources as the source of record.
- Do not infer sponsorship support from company reputation or historical filings.
- Do not bypass authentication, CAPTCHAs, robots restrictions, or access controls.
- The skill never submits applications, uploads resumes, creates accounts, or contacts recruiters without explicit user authorization.
- Keep personal profiles and scan state out of public commits.

## Limitations

- Workday and custom career sites may require browser fallback.
- Greenhouse `updated_at` is an update signal, not guaranteed original publication time.
- A first scan establishes the baseline; later scans provide stronger new/updated/removed detection.
- Job matching is a prioritization aid, not a guarantee of eligibility or hiring outcome.

## License

MIT
