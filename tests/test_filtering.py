from __future__ import annotations

from datetime import date, timedelta

from job_agent.filtering import filter_jobs, requires_more_than_two_years
from job_agent.models import JobLead


def make_job(**overrides) -> JobLead:
    today = date(2026, 8, 24)
    data = {
        "title": "Junior AI Engineer",
        "company": "Example",
        "location": "Remote, India",
        "experience": "0-2 years",
        "work_mode": "Remote",
        "apply_link": "https://example.com/jobs/1?utm_source=test",
        "source_platform": "Company Careers",
        "posted_date": today.isoformat(),
        "short_summary": "Python LLM RAG role.",
        "description": "Entry level AI Engineer with Python.",
    }
    data.update(overrides)
    return JobLead(**data)


def test_filters_out_old_jobs() -> None:
    today = date(2026, 8, 24)
    jobs = [
        make_job(posted_date=today.isoformat()),
        make_job(apply_link="https://example.com/jobs/2", posted_date=(today - timedelta(days=4)).isoformat()),
    ]
    assert len(filter_jobs(jobs, days_back=3, today=today)) == 1


def test_filters_out_duplicate_urls() -> None:
    today = date(2026, 8, 24)
    jobs = [
        make_job(apply_link="https://example.com/jobs/1?utm_source=a", posted_date=today.isoformat()),
        make_job(apply_link="https://example.com/jobs/1?utm_source=b", posted_date=today.isoformat()),
    ]
    assert len(filter_jobs(jobs, days_back=3, today=today)) == 1


def test_experience_filter_detects_senior_roles() -> None:
    assert requires_more_than_two_years("senior machine learning engineer", "0-2 years")
    assert requires_more_than_two_years("minimum 3 years python", "3 years")
    assert not requires_more_than_two_years("junior python backend developer", "1-2 years")
