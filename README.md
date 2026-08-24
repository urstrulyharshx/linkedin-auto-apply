# AI Job Search Agent

Cloud-ready job search automation for India roles. It runs on a schedule, searches only public Google-indexed job pages, filters stale/irrelevant/duplicate/high-experience roles, ranks matches, and creates a fresh `.xlsx` spreadsheet on every execution.

## What It Does

- Searches roles related to AI Engineer, AI Developer, Machine Learning, Gen AI Developer, Python Backend Developer, and Data Scientist.
- Targets entry-level and up to 2 years of experience jobs.
- Includes remote, hybrid, and onsite opportunities across India.
- Uses only public indexed result URLs from supported search APIs.
- Includes Naukri through public Google-indexed pages, with extra Naukri-specific searches for freshers and `0-2 years` roles.
- Does not log in to LinkedIn, Naukri, Glassdoor, Indeed, or any private page.
- Filters jobs older than 3 days, expired roles, duplicates, irrelevant roles, and roles requiring more than 2 years of experience.
- Generates only the top 20 results.
- Generates tailored application notes for every selected job.
- Flags whether a role is safe/eligible for future allowlisted company-ATS auto-apply.
- Creates a new spreadsheet file every run under `output/`.
- GitHub Actions uploads the generated spreadsheet as a downloadable workflow artifact.

## Cloud Setup

1. Push this repository to GitHub.
2. Add repository secrets:

   - `SERPAPI_API_KEY` for SerpAPI, or use the Google Custom Search secrets below.
   - Optional: `OPENAI_API_KEY` for LLM-based relevance ranking.
   - Optional: `APPLICANT_PROFILE_JSON` and `RESUME_URL` for richer application drafts.

3. Optional Google Custom Search mode secrets:

   - `SEARCH_PROVIDER=google_cse`
   - `GOOGLE_API_KEY`
   - `GOOGLE_CSE_ID`

4. The workflow in `.github/workflows/daily-job-search.yml` runs daily at `03:30 UTC`, which is `09:00 AM IST`.

5. After a run finishes, open the GitHub Actions run and download the `job-search-results` artifact.

## Local Test Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
PYTHONPATH=src python -m job_agent --dry-run
```

`--dry-run` uses sample public-style records and verifies filtering/export without calling search providers.

## Production Run

```bash
PYTHONPATH=src python -m job_agent
```

The production run requires either:

- `SEARCH_PROVIDER=serpapi` and `SERPAPI_API_KEY`, or
- `SEARCH_PROVIDER=google_cse`, `GOOGLE_API_KEY`, and `GOOGLE_CSE_ID`.

## Important Boundaries

This agent is intentionally human-safe and platform-safe:

- It does not bypass CAPTCHA, login, paywalls, robots rules, or access controls.
- It does not auto-submit applications on LinkedIn, Naukri, Indeed, Glassdoor, Internshala, or Wellfound.
- It only marks public company/ATS pages as eligible for future auto-apply when their domain is explicitly allowlisted.
- It does not scrape private/authenticated pages.
- It stores the original apply/source URL in the workbook so you can manually review and apply.

## Can It Auto Apply?

For job boards like LinkedIn, Naukri, Indeed, Glassdoor, Internshala, and Wellfound: no. Their public terms commonly restrict bots, automated site activity, or automated application submission. The agent keeps those as review-only links.

For direct public company career pages or ATS pages: maybe, but only with safeguards:

- `AUTO_APPLY_ENABLED=true`
- domain included in `AUTO_APPLY_ALLOWED_DOMAINS`
- no login, CAPTCHA, paywall, or private page
- no deceptive answers
- applicant profile supplied from cloud secrets

This repo currently generates application-ready drafts and eligibility flags. A submitter should be added only for specific ATS providers you explicitly approve.
