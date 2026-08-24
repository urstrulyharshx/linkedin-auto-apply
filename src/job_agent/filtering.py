from __future__ import annotations

import re
from datetime import date
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from .date_utils import is_within_days
from .models import JobLead


ROLE_KEYWORDS = [
    "ai engineer",
    "ai developer",
    "artificial intelligence",
    "machine learning",
    "ml engineer",
    "gen ai",
    "generative ai",
    "python backend",
    "backend developer",
    "data scientist",
    "data science",
]

EXPIRED_TERMS = ["expired", "closed", "no longer accepting", "not accepting applications", "position filled"]


def filter_jobs(jobs: list[JobLead], days_back: int, today: date | None = None) -> list[JobLead]:
    filtered: list[JobLead] = []
    seen_urls: set[str] = set()
    seen_title_company: set[str] = set()

    for job in jobs:
        text = job.ranking_text().lower()
        normalized_url = normalize_url(job.apply_link)
        title_company = normalize_key(f"{job.title} {job.company}")

        if normalized_url in seen_urls or title_company in seen_title_company:
            continue
        if not is_relevant(text):
            continue
        if has_expired_signal(text):
            continue
        if not is_within_days(job.posted_date, days_back, today=today):
            continue
        if requires_more_than_two_years(text, job.experience):
            continue

        seen_urls.add(normalized_url)
        seen_title_company.add(title_company)
        filtered.append(job)

    return filtered


def is_relevant(text: str) -> bool:
    return any(keyword in text for keyword in ROLE_KEYWORDS)


def has_expired_signal(text: str) -> bool:
    return any(term in text for term in EXPIRED_TERMS)


def requires_more_than_two_years(text: str, experience: str) -> bool:
    combined = f"{experience} {text}".lower()

    senior_terms = ["senior", "staff engineer", "lead ", "manager", "principal", "architect"]
    if any(term in combined for term in senior_terms):
        return True

    ranges = re.findall(r"\b(\d+(?:\.\d+)?)\s*[-–to]+\s*(\d+(?:\.\d+)?)\s*(?:years?|yrs?)\b", combined)
    if ranges:
        return any(float(high) > 2 for _, high in ranges)

    plus_values = re.findall(r"\b(\d+(?:\.\d+)?)\s*\+\s*(?:years?|yrs?)\b", combined)
    if plus_values:
        return any(float(value) > 2 for value in plus_values)

    exact_values = re.findall(r"\b(?:minimum|min\.?|at least|required)\s*(\d+(?:\.\d+)?)\s*(?:years?|yrs?)\b", combined)
    if exact_values:
        return any(float(value) > 2 for value in exact_values)

    return False


def normalize_url(url: str) -> str:
    parsed = urlparse(url)
    tracking_prefixes = ("utm_",)
    allowed_query = [
        (key, value)
        for key, value in parse_qsl(parsed.query, keep_blank_values=False)
        if not key.startswith(tracking_prefixes) and key not in {"ref", "source", "trk"}
    ]
    return urlunparse(
        (
            parsed.scheme,
            parsed.netloc.lower(),
            parsed.path.rstrip("/"),
            "",
            urlencode(allowed_query),
            "",
        )
    )


def normalize_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()
