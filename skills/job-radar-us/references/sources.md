# Official job-source collection

## Preferred sources

### Ashby

Use:

```text
GET https://api.ashbyhq.com/posting-api/job-board/{board}?includeCompensation=true
```

Useful fields include `title`, `location`, `secondaryLocations`, `isRemote`, `workplaceType`, `descriptionPlain`, `publishedAt`, `employmentType`, `jobUrl`, and `applyUrl`. Send a standard browser User-Agent because the service may reject the default Python client with HTTP 403. A 404 commonly means the board slug is wrong, not that the company has no jobs.

### Greenhouse

Use:

```text
GET https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true
```

Treat `updated_at` as a modification timestamp. Determine newness primarily from stable IDs and first-seen state.

### Lever

Use:

```text
GET https://api.lever.co/v0/postings/{site}?mode=json
```

Use `id`, `text`, `categories`, `createdAt`, `descriptionPlain`, `hostedUrl`, and `applyUrl`. Published public postings require no applicant API key. Never use the application endpoint during a scan.

## Discovery and fallback

1. Search for the company name plus `careers`, restricted to the official company domain when known.
2. Follow the official Careers or Jobs link and identify Ashby, Greenhouse, Lever, Workday, or a custom site from the URL and page structure.
3. Record the verified provider and slug in scan state for the next run.
4. If the API is blocked, use the official hosted job board through browser navigation.
5. If neither path works, report `source_failed` with the HTTP or browser reason. Do not report zero openings.

## Rate and integrity rules

- Fetch listings only; do not call application-submission endpoints.
- Use bounded concurrency and retry HTTP 429/5xx responses with backoff.
- Do not bypass authentication, CAPTCHAs, robots restrictions, or access controls.
- Preserve the official job URL and source ID in every normalized record.
