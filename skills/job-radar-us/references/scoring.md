# Matching and evidence rules

## Score composition

Calculate a 0–100 score before applying hard blockers.

| Component | Maximum | Rule |
|---|---:|---|
| Title and role family | 30 | Data engineering 30; data analytics 28; AI/LLM/agent 27; algorithm/data science 24; software engineering 21. |
| Recruiting stage and timing | 20 | Co-op/intern 20; explicitly eligible new grad 18; early career 15; generic full-time 7. |
| Evidence-backed skill overlap | 20 | Award 2 points per distinct matched skill, capped at 20. Do not count substring duplicates. |
| Location | 15 | Bay Area 15; elsewhere in California 12; US remote 10; other US 6. Subtract 8 for a small company outside California. |
| Work authorization evidence | 10 | Explicit CPT/OPT or sponsorship acceptance 10; not stated 0 and mark unknown; explicit refusal is a blocker. |
| Freshness | 5 | Published/first seen within 72 hours 5; within 7 days 3; older or unknown 0. |

Apply an experience adjustment after the component score: subtract 4 for an explicit one-year minimum and 10 for a two-to-three-year minimum. An explicit minimum of four or more years is a hard blocker for the current student profile.

Clamp non-blocked scores to 0–100.

## Hard blockers

- Explicitly requires citizenship, permanent residency, an active security clearance, or states that sponsorship is unavailable.
- Seniority is Staff, Principal, Lead, Manager, Director, or higher unless the posting is explicitly an internship/student role.
- The posting explicitly requires at least four years of professional, industry, relevant, or engineering experience.
- Required graduation or degree-completion date excludes December 2027.
- Required start date is before degree completion for a full-time new-grad role and the posting does not allow continued enrollment.
- Unpaid role scores below 80 before the compensation rule.

Do not hard-block a role merely because sponsorship is not mentioned. Mark it `authorization_unknown` and place it in Review unless the remaining evidence is unusually strong.

## Recruiting-window interpretation

- Prioritize Fall 2026 co-op immediately.
- Treat Winter 2027 as January–April 2027 unless the user clarifies otherwise.
- Prioritize Summer 2027 internships.
- Treat Summer 2027 new-grad roles as normally incompatible with December 2027 graduation. Retain only explicit exceptions.
- Search late-2027 and 2028 new-grad openings for post-graduation starts.

## Freshness and deduplication

Use this evidence order:

1. ATS stable job ID plus `publishedAt`/creation timestamp.
2. Stable canonical URL plus prior first-seen state.
3. Company + normalized title + normalized location fallback key.

An ATS `updated_at` value proves an update, not necessarily a new publication. Label it accordingly.

## Report language

Write recommendations in English and preserve exact job titles and requirement keywords. Separate facts from inferences. For every work-authorization conclusion, provide the relevant posting language or state `not stated in the posting`.
