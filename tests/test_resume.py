from __future__ import annotations

from dataclasses import replace

from job_agent.config import load_config
from job_agent.resume import resolve_resume


def test_local_resume_is_ignored_in_cloud_mode(tmp_path) -> None:
    resume = tmp_path / "resume.pdf"
    resume.write_bytes(b"%PDF-1.7\n")
    config = replace(load_config(), resume_url=None, local_resume_path=resume)

    status = resolve_resume(config, allow_local=False)

    assert status.status == "ignored"


def test_local_resume_is_available_for_dry_run(tmp_path) -> None:
    resume = tmp_path / "resume.pdf"
    resume.write_bytes(b"%PDF-1.7\n")
    config = replace(load_config(), resume_url=None, local_resume_path=resume)

    status = resolve_resume(config, allow_local=True)

    assert status.status == "available"
    assert status.local_path == resume
