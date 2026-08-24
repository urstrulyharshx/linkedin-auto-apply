from __future__ import annotations

import smtplib
from email.message import EmailMessage
from pathlib import Path

from .config import AgentConfig
from .models import JobLead
from .resume import ResumeStatus


def maybe_send_results_email(
    config: AgentConfig,
    workbook_path: Path,
    jobs: list[JobLead],
    resume_status: ResumeStatus,
) -> bool:
    if not email_configured(config):
        return False

    message = EmailMessage()
    message["Subject"] = f"Daily Job Search Results - Top {min(len(jobs), 20)} Jobs"
    message["From"] = config.smtp_from or config.smtp_username or ""
    message["To"] = config.notification_email_to or ""
    message.set_content(build_email_body(jobs, resume_status))

    message.add_attachment(
        workbook_path.read_bytes(),
        maintype="application",
        subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=workbook_path.name,
    )

    with smtplib.SMTP(config.smtp_host or "", config.smtp_port, timeout=config.request_timeout_seconds) as smtp:
        smtp.starttls()
        smtp.login(config.smtp_username or "", config.smtp_password or "")
        smtp.send_message(message)

    return True


def email_configured(config: AgentConfig) -> bool:
    required = [
        config.notification_email_to,
        config.smtp_host,
        config.smtp_username,
        config.smtp_password,
        config.smtp_from,
    ]
    return all(required)


def build_email_body(jobs: list[JobLead], resume_status: ResumeStatus) -> str:
    lines = [
        "Your daily job search agent has finished.",
        "",
        f"Top jobs included: {min(len(jobs), 20)}",
        f"Resume status: {resume_status.status} ({resume_status.source})",
        "",
        "Top matches:",
    ]
    for index, job in enumerate(jobs[:5], start=1):
        lines.append(f"{index}. {job.title} - {job.company} - {job.location} - score {job.match_score:.1f}")
    lines.extend(
        [
            "",
            "The full spreadsheet is attached.",
            "",
            "Note: Job-board applications remain review-only. This agent does not auto-submit on LinkedIn, Naukri, Indeed, Glassdoor, Internshala, or Wellfound.",
        ]
    )
    return "\n".join(lines)
