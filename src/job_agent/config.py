from __future__ import annotations

import os
import json
from dataclasses import dataclass, field
from pathlib import Path


DEFAULT_ROLES = [
    "AI Engineer",
    "AI Developer",
    "Machine Learning Engineer",
    "Gen AI Developer",
    "Python Backend Developer",
    "Data Scientist",
]

DEFAULT_PLATFORMS = {
    "linkedin": "linkedin.com/jobs",
    "internshala": "internshala.com",
    "wellfound": "wellfound.com/jobs",
    "indeed": "indeed.com",
    "glassdoor": "glassdoor.co.in",
    "naukri": "naukri.com",
}

COMPANY_CAREER_TERMS = [
    "site:jobs.lever.co",
    "site:boards.greenhouse.io",
    "site:careers.microsoft.com",
    "site:careers.google.com",
    "site:jobs.ashbyhq.com",
    "site:workdayjobs.com",
]


@dataclass(frozen=True)
class AgentConfig:
    search_provider: str = "serpapi"
    max_results: int = 20
    max_search_queries: int = 8
    days_back: int = 3
    country: str = "India"
    output_dir: Path = Path("output")
    request_timeout_seconds: int = 15
    roles: list[str] = field(default_factory=lambda: list(DEFAULT_ROLES))
    platform_sites: dict[str, str] = field(default_factory=lambda: dict(DEFAULT_PLATFORMS))
    company_career_terms: list[str] = field(default_factory=lambda: list(COMPANY_CAREER_TERMS))
    serpapi_api_key: str | None = None
    google_api_key: str | None = None
    google_cse_id: str | None = None
    openai_api_key: str | None = None
    openai_model: str = "gpt-4.1-mini"
    auto_apply_enabled: bool = False
    auto_apply_allowed_domains: list[str] = field(default_factory=list)
    applicant_profile: dict = field(default_factory=dict)
    resume_url: str | None = None
    local_resume_path: Path | None = None
    runtime_dir: Path = Path("runtime")


def load_config() -> AgentConfig:
    return AgentConfig(
        search_provider=os.getenv("SEARCH_PROVIDER", "serpapi").strip().lower(),
        max_results=int(os.getenv("MAX_RESULTS", "20")),
        max_search_queries=int(os.getenv("MAX_SEARCH_QUERIES", "8")),
        days_back=int(os.getenv("DAYS_BACK", "3")),
        country=os.getenv("COUNTRY", "India"),
        output_dir=Path(os.getenv("OUTPUT_DIR", "output")),
        request_timeout_seconds=int(os.getenv("REQUEST_TIMEOUT_SECONDS", "15")),
        serpapi_api_key=os.getenv("SERPAPI_API_KEY"),
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        google_cse_id=os.getenv("GOOGLE_CSE_ID"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        auto_apply_enabled=os.getenv("AUTO_APPLY_ENABLED", "false").strip().lower() == "true",
        auto_apply_allowed_domains=parse_csv_env("AUTO_APPLY_ALLOWED_DOMAINS"),
        applicant_profile=parse_json_env("APPLICANT_PROFILE_JSON"),
        resume_url=os.getenv("RESUME_URL"),
        local_resume_path=parse_optional_path_env("LOCAL_RESUME_PATH"),
        runtime_dir=Path(os.getenv("RUNTIME_DIR", "runtime")),
    )


def parse_csv_env(name: str) -> list[str]:
    value = os.getenv(name, "")
    return [item.strip().lower() for item in value.split(",") if item.strip()]


def parse_json_env(name: str) -> dict:
    value = os.getenv(name, "")
    if not value:
        return {}
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def parse_optional_path_env(name: str) -> Path | None:
    value = os.getenv(name, "").strip()
    return Path(value).expanduser() if value else None
