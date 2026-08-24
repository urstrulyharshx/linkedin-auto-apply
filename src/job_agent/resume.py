from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

import requests

from .config import AgentConfig


PDF_MAGIC = b"%PDF"


@dataclass(frozen=True)
class ResumeStatus:
    status: str
    source: str
    reference: str | None = None
    local_path: Path | None = None


def resolve_resume(config: AgentConfig, allow_local: bool = False) -> ResumeStatus:
    if config.resume_url:
        target = config.runtime_dir / "resume.pdf"
        return download_resume(config.resume_url, target, config.request_timeout_seconds)

    if allow_local and config.local_resume_path:
        return validate_local_resume(config.local_resume_path)

    if config.local_resume_path and not allow_local:
        return ResumeStatus(
            status="ignored",
            source="local file",
            reference="LOCAL_RESUME_PATH is only used for local dry-runs. Use RESUME_URL in GitHub Actions.",
        )

    return ResumeStatus(
        status="missing",
        source="none",
        reference="Set RESUME_URL as a GitHub secret so the cloud workflow can access your resume.",
    )


def download_resume(url: str, target: Path, timeout_seconds: int) -> ResumeStatus:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return ResumeStatus(status="invalid", source="RESUME_URL", reference="Resume URL must start with http or https.")

    try:
        response = requests.get(url, timeout=timeout_seconds)
        response.raise_for_status()
    except requests.RequestException as exc:
        return ResumeStatus(status="unavailable", source="RESUME_URL", reference=str(exc))

    content = response.content
    if not looks_like_pdf(content):
        return ResumeStatus(status="invalid", source="RESUME_URL", reference="Downloaded file is not a PDF.")

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)
    return ResumeStatus(status="available", source="RESUME_URL", reference=url, local_path=target)


def validate_local_resume(path: Path) -> ResumeStatus:
    expanded = path.expanduser()
    if not expanded.exists():
        return ResumeStatus(status="missing", source="LOCAL_RESUME_PATH", reference=str(expanded))

    content = expanded.read_bytes()[:8]
    if not looks_like_pdf(content):
        return ResumeStatus(status="invalid", source="LOCAL_RESUME_PATH", reference=str(expanded))

    return ResumeStatus(status="available", source="LOCAL_RESUME_PATH", reference=str(expanded), local_path=expanded)


def looks_like_pdf(content: bytes) -> bool:
    return content.startswith(PDF_MAGIC)
