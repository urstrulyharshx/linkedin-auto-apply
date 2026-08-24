from __future__ import annotations

from urllib.parse import urlparse

from .models import JobLead


JOB_BOARD_PLATFORMS = {
    "LinkedIn Jobs",
    "Naukri",
    "Indeed",
    "Glassdoor",
    "Internshala",
    "Wellfound",
}


def annotate_auto_apply(
    jobs: list[JobLead],
    enabled: bool,
    allowed_domains: list[str],
    applicant_profile: dict,
    resume_url: str | None,
) -> list[JobLead]:
    allowed = {domain.lower() for domain in allowed_domains}
    has_profile = bool(applicant_profile)
    has_resume = bool(resume_url)

    for job in jobs:
        host = urlparse(job.apply_link).netloc.lower()

        if job.source_platform in JOB_BOARD_PLATFORMS:
            job.auto_apply_eligible = False
            job.auto_apply_reason = f"{job.source_platform} is review-only; automated applications are not enabled for job boards."
            job.application_status = "Review only"
            continue

        if not enabled:
            job.auto_apply_eligible = False
            job.auto_apply_reason = "Auto-apply is disabled. Set AUTO_APPLY_ENABLED=true only after approving specific company/ATS domains."
            job.application_status = "Draft generated"
            continue

        if not domain_allowed(host, allowed):
            job.auto_apply_eligible = False
            job.auto_apply_reason = f"Domain {host or 'unknown'} is not in AUTO_APPLY_ALLOWED_DOMAINS."
            job.application_status = "Draft generated"
            continue

        if not has_profile or not has_resume:
            job.auto_apply_eligible = False
            job.auto_apply_reason = "Applicant profile and RESUME_URL are required for any future allowlisted auto-apply."
            job.application_status = "Draft generated"
            continue

        job.auto_apply_eligible = True
        job.auto_apply_reason = "Allowlisted public company/ATS domain. Submission adapter not run by default."
        job.application_status = "Eligible for explicit ATS submitter"

    return jobs


def domain_allowed(host: str, allowed_domains: set[str]) -> bool:
    return any(host == domain or host.endswith(f".{domain}") for domain in allowed_domains)
