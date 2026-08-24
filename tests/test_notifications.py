from __future__ import annotations

from dataclasses import replace

from job_agent.config import load_config
from job_agent.notifications import build_email_body, email_configured
from job_agent.resume import ResumeStatus


def test_email_config_requires_all_smtp_fields() -> None:
    config = replace(
        load_config(),
        notification_email_to="harsh2mishra6@gmail.com",
        smtp_host="smtp.example.com",
        smtp_username="user",
        smtp_password="password",
        smtp_from="from@example.com",
    )

    assert email_configured(config)


def test_email_body_mentions_resume_status() -> None:
    body = build_email_body([], ResumeStatus(status="available", source="RESUME_URL", reference="x"))

    assert "Resume status: available" in body
    assert "full spreadsheet is attached" in body
