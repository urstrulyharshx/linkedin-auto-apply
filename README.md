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
- Optionally emails the spreadsheet as an attachment after each successful run.
- Defaults to 8 search queries per daily run, roughly 240 SerpAPI searches/month, to fit the free 250/month tier.

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

4. Optional email secrets for daily email delivery:

   - `SMTP_HOST`
   - `SMTP_PORT`
   - `SMTP_USERNAME`
   - `SMTP_PASSWORD`
   - `SMTP_FROM`

   Set repository variable `NOTIFICATION_EMAIL_TO` to `harsh2mishra6@gmail.com`, or leave the workflow default as-is.

5. The workflow in `.github/workflows/daily-job-search.yml` runs daily at `03:30 UTC`, which is `09:00 AM IST`.

6. After a run finishes, open the GitHub Actions run and download the `job-search-results` artifact. If SMTP secrets are configured, the same workbook is emailed to you.

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

## Resume and Profile Setup

The cloud workflow cannot read files from your laptop. It only sees values stored in GitHub Secrets or files committed to the repo.

Recommended secrets:

- `SERPAPI_API_KEY`: required for public Google-indexed job search.
- `RESUME_URL`: a direct downloadable link to your resume PDF, hosted somewhere cloud-accessible.
- `LOCAL_RESUME_PATH`: optional local dry-run path only. GitHub Actions cannot use laptop paths.
- `APPLICANT_PROFILE_JSON`: your name, email, phone, location, summary, and skills for generating application drafts.
- `OPENAI_API_KEY`: optional, for stronger AI ranking and tailored draft generation.
- SMTP secrets: optional, for sending the generated spreadsheet to your email.

Example `APPLICANT_PROFILE_JSON`:

```json
{
  "name": "Harsh Mishra",
  "email": "your-email@example.com",
  "phone": "+91XXXXXXXXXX",
  "location": "India",
  "summary": "Python and AI developer focused on backend APIs, ML, and GenAI projects.",
  "skills": ["Python", "FastAPI", "Machine Learning", "LLMs", "RAG", "SQL"]
}
```

For `RESUME_URL`, use a link that GitHub Actions can download without logging in. Google Drive share links like `https://drive.google.com/file/d/.../view?...` are automatically converted to direct download links. A private signed URL is better than a public permanent link. The workflow downloads the resume during each run, validates that it is a PDF, and records the resume status in the `Run Metadata` sheet. The actual PDF is not committed to git.
