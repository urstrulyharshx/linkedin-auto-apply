from __future__ import annotations

from job_agent.auto_apply import annotate_auto_apply
from job_agent.models import JobLead


def make_job(source_platform: str, link: str) -> JobLead:
    return JobLead(
        title="Junior AI Engineer",
        company="Example",
        location="India",
        experience="0-2 years",
        work_mode="Remote",
        apply_link=link,
        source_platform=source_platform,
        posted_date="2026-08-24",
        short_summary="Python AI role",
    )


def test_job_boards_are_review_only_even_when_enabled() -> None:
    jobs = [make_job("LinkedIn Jobs", "https://www.linkedin.com/jobs/view/123")]
    annotated = annotate_auto_apply(
        jobs,
        enabled=True,
        allowed_domains=["linkedin.com"],
        applicant_profile={"name": "Test"},
        resume_url="https://example.com/resume.pdf",
    )
    assert not annotated[0].auto_apply_eligible
    assert annotated[0].application_status == "Review only"


def test_allowlisted_company_domain_can_be_marked_eligible() -> None:
    jobs = [make_job("Company Careers", "https://jobs.lever.co/example/123")]
    annotated = annotate_auto_apply(
        jobs,
        enabled=True,
        allowed_domains=["jobs.lever.co"],
        applicant_profile={"name": "Test"},
        resume_url="https://example.com/resume.pdf",
    )
    assert annotated[0].auto_apply_eligible
