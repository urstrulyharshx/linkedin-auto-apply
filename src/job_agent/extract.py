from __future__ import annotations

import json
import re
import urllib.robotparser
from datetime import date
from typing import Any
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from .date_utils import parse_posted_date
from .models import JobLead, SearchResult
from .search import infer_platform


USER_AGENT = "PublicJobSearchAgent/0.1 (+https://github.com/; public pages only)"


def extract_job(result: SearchResult, timeout_seconds: int, today: date | None = None) -> JobLead:
    html = fetch_public_page(result.link, timeout_seconds)
    structured = extract_json_ld_job(html) if html else {}
    soup_text = extract_page_text(html) if html else ""

    title = pick_text(structured.get("title"), result.title)
    company = extract_company(structured) or company_from_title(result.title) or "Unknown"
    location = extract_location(structured) or extract_location_from_text(result.snippet + " " + soup_text) or "India"
    work_mode = extract_work_mode(" ".join([title, location, result.snippet, soup_text]))
    experience = extract_experience(" ".join([result.title, result.snippet, soup_text])) or "Not specified"
    posted_date = extract_posted_date(structured, result.snippet, soup_text, today=today)
    summary = summarize_text(structured.get("description") or result.snippet or soup_text)

    return JobLead(
        title=clean_text(title),
        company=clean_text(company),
        location=clean_text(location),
        experience=clean_text(experience),
        work_mode=work_mode,
        apply_link=result.link,
        source_platform=result.source_platform or infer_platform(result.link),
        posted_date=posted_date or "",
        short_summary=summary,
        description=clean_text(structured.get("description") or soup_text),
        source_url=result.link,
    )


def fetch_public_page(url: str, timeout_seconds: int) -> str:
    if not is_public_fetch_allowed(url):
        return ""
    try:
        response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=timeout_seconds)
        if response.status_code >= 400 or "text/html" not in response.headers.get("content-type", ""):
            return ""
        return response.text[:750_000]
    except requests.RequestException:
        return ""


def is_public_fetch_allowed(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return False
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    robot = urllib.robotparser.RobotFileParser()
    try:
        robot.set_url(robots_url)
        robot.read()
        return robot.can_fetch(USER_AGENT, url)
    except Exception:
        return True


def extract_json_ld_job(html: str) -> dict[str, Any]:
    soup = BeautifulSoup(html, "html.parser")
    for script in soup.find_all("script", {"type": "application/ld+json"}):
        raw = script.string or script.get_text(strip=True)
        if not raw:
            continue
        for obj in parse_json_ld(raw):
            job = find_job_posting(obj)
            if job:
                return job
    return {}


def parse_json_ld(raw: str) -> list[Any]:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return []
    return data if isinstance(data, list) else [data]


def find_job_posting(value: Any) -> dict[str, Any] | None:
    if isinstance(value, dict):
        type_value = value.get("@type")
        types = type_value if isinstance(type_value, list) else [type_value]
        if "JobPosting" in types:
            return value
        graph = value.get("@graph")
        if isinstance(graph, list):
            for item in graph:
                found = find_job_posting(item)
                if found:
                    return found
    if isinstance(value, list):
        for item in value:
            found = find_job_posting(item)
            if found:
                return found
    return None


def extract_page_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    return clean_text(soup.get_text(" ", strip=True))[:8000]


def extract_company(job: dict[str, Any]) -> str:
    org = job.get("hiringOrganization")
    if isinstance(org, dict):
        return pick_text(org.get("name"))
    if isinstance(org, str):
        return org
    return ""


def extract_location(job: dict[str, Any]) -> str:
    location = job.get("jobLocation")
    if isinstance(location, list):
        return ", ".join(filter(None, [extract_location({"jobLocation": item}) for item in location]))
    if isinstance(location, dict):
        address = location.get("address")
        if isinstance(address, dict):
            parts = [
                address.get("addressLocality"),
                address.get("addressRegion"),
                address.get("addressCountry"),
            ]
            return ", ".join(str(part) for part in parts if part)
        return pick_text(location.get("name"))
    return ""


def extract_location_from_text(text: str) -> str:
    location_words = [
        "Bengaluru",
        "Bangalore",
        "Hyderabad",
        "Pune",
        "Mumbai",
        "Delhi",
        "Noida",
        "Gurgaon",
        "Gurugram",
        "Chennai",
        "Kolkata",
        "Ahmedabad",
        "India",
        "Remote",
    ]
    found = [word for word in location_words if re.search(rf"\b{re.escape(word)}\b", text, re.I)]
    return ", ".join(dict.fromkeys(found))


def extract_work_mode(text: str) -> str:
    lowered = text.lower()
    modes = []
    if any(term in lowered for term in ["remote", "work from home", "wfh"]):
        modes.append("Remote")
    if "hybrid" in lowered:
        modes.append("Hybrid")
    if any(term in lowered for term in ["onsite", "on-site", "office"]):
        modes.append("Onsite")
    return ", ".join(modes) if modes else "Not specified"


def extract_experience(text: str) -> str:
    lowered = text.lower()
    if any(term in lowered for term in ["fresher", "entry level", "entry-level", "graduate"]):
        return "Entry level"

    patterns = [
        r"\b(\d+(?:\.\d+)?)\s*[-–to]+\s*(\d+(?:\.\d+)?)\s*(?:years?|yrs?)\b",
        r"\b(\d+(?:\.\d+)?)\+?\s*(?:years?|yrs?)\b",
        r"\bexperience\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*[-–to]+\s*(\d+(?:\.\d+)?)\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, lowered)
        if match:
            if len(match.groups()) == 2 and match.group(2):
                return f"{match.group(1)}-{match.group(2)} years"
            return f"{match.group(1)} years"
    return ""


def extract_posted_date(job: dict[str, Any], snippet: str, page_text: str, today: date | None = None) -> str:
    candidates = [
        pick_text(job.get("datePosted")),
        snippet,
        page_text[:2000],
    ]
    for candidate in candidates:
        parsed = parse_posted_date(candidate, today=today)
        if parsed:
            return parsed.isoformat()
    return ""


def summarize_text(text: str) -> str:
    cleaned = clean_text(BeautifulSoup(text or "", "html.parser").get_text(" ", strip=True))
    if len(cleaned) <= 280:
        return cleaned
    return cleaned[:277].rsplit(" ", 1)[0] + "..."


def company_from_title(title: str) -> str:
    separators = [" at ", " - ", " | "]
    for separator in separators:
        if separator in title:
            right = title.split(separator, 1)[1]
            return re.sub(r"\bJobs?\b.*$", "", right, flags=re.I).strip()
    return ""


def pick_text(*values: Any) -> str:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()
