from __future__ import annotations

import time
from abc import ABC, abstractmethod
from urllib.parse import urlparse

import requests

from .config import AgentConfig
from .models import SearchResult


class SearchProvider(ABC):
    @abstractmethod
    def search(self, query: str, limit: int) -> list[SearchResult]:
        raise NotImplementedError


class SerpApiSearchProvider(SearchProvider):
    def __init__(self, api_key: str, timeout_seconds: int) -> None:
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds

    def search(self, query: str, limit: int) -> list[SearchResult]:
        params = {
            "engine": "google",
            "q": query,
            "api_key": self.api_key,
            "num": min(limit, 10),
            "gl": "in",
            "hl": "en",
            "tbs": "qdr:d3",
        }
        response = requests.get("https://serpapi.com/search.json", params=params, timeout=self.timeout_seconds)
        response.raise_for_status()
        payload = response.json()
        results = []
        for item in payload.get("organic_results", []):
            link = item.get("link", "")
            if not link:
                continue
            results.append(
                SearchResult(
                    title=item.get("title", ""),
                    link=link,
                    snippet=item.get("snippet", ""),
                    displayed_link=item.get("displayed_link", ""),
                    source_platform=infer_platform(link),
                )
            )
        return results


class GoogleCseSearchProvider(SearchProvider):
    def __init__(self, api_key: str, cse_id: str, timeout_seconds: int) -> None:
        self.api_key = api_key
        self.cse_id = cse_id
        self.timeout_seconds = timeout_seconds

    def search(self, query: str, limit: int) -> list[SearchResult]:
        results: list[SearchResult] = []
        start = 1
        while len(results) < limit and start <= 91:
            params = {
                "key": self.api_key,
                "cx": self.cse_id,
                "q": query,
                "num": min(10, limit - len(results)),
                "start": start,
                "dateRestrict": "d3",
            }
            response = requests.get("https://www.googleapis.com/customsearch/v1", params=params, timeout=self.timeout_seconds)
            response.raise_for_status()
            payload = response.json()
            items = payload.get("items", [])
            if not items:
                break
            for item in items:
                link = item.get("link", "")
                if not link:
                    continue
                results.append(
                    SearchResult(
                        title=item.get("title", ""),
                        link=link,
                        snippet=item.get("snippet", ""),
                        displayed_link=item.get("displayLink", ""),
                        source_platform=infer_platform(link),
                    )
                )
            start += 10
            time.sleep(0.2)
        return results


def build_provider(config: AgentConfig) -> SearchProvider:
    if config.search_provider == "serpapi":
        if not config.serpapi_api_key:
            raise RuntimeError("SERPAPI_API_KEY is required when SEARCH_PROVIDER=serpapi.")
        return SerpApiSearchProvider(config.serpapi_api_key, config.request_timeout_seconds)

    if config.search_provider == "google_cse":
        if not config.google_api_key or not config.google_cse_id:
            raise RuntimeError("GOOGLE_API_KEY and GOOGLE_CSE_ID are required when SEARCH_PROVIDER=google_cse.")
        return GoogleCseSearchProvider(config.google_api_key, config.google_cse_id, config.request_timeout_seconds)

    raise RuntimeError(f"Unsupported SEARCH_PROVIDER: {config.search_provider}")


def infer_platform(url: str) -> str:
    host = urlparse(url).netloc.lower()
    if "linkedin." in host:
        return "LinkedIn Jobs"
    if "internshala." in host:
        return "Internshala"
    if "wellfound." in host or "angel.co" in host:
        return "Wellfound"
    if "indeed." in host:
        return "Indeed"
    if "glassdoor." in host:
        return "Glassdoor"
    if "naukri." in host:
        return "Naukri"
    return "Company Careers"


def build_queries(config: AgentConfig) -> list[str]:
    role_group = "(" + " OR ".join(f'"{role}"' for role in config.roles) + ")"
    junior_terms = '("entry level" OR fresher OR "0-1 years" OR "0-2 years" OR "1 year" OR "2 years" OR junior)'
    mode_terms = '(remote OR hybrid OR onsite OR "work from home" OR India)'
    age_terms = '("posted" OR "hiring" OR "apply")'

    priority_platforms = ["naukri", "linkedin", "indeed", "internshala", "wellfound", "glassdoor"]
    queries: list[str] = [
        f"site:{config.platform_sites[key]} {role_group} {junior_terms} {mode_terms} {age_terms}"
        for key in priority_platforms
        if key in config.platform_sites
    ]

    naukri_priority_roles = ["AI Engineer", "Gen AI Developer", "Python Backend Developer", "Data Scientist"]
    for role in naukri_priority_roles:
        queries.append(f'site:naukri.com "{role}" "0-2 years" India ("posted" OR "apply")')

    for career_term in config.company_career_terms:
        queries.append(f"{career_term} {role_group} {junior_terms} {mode_terms} {config.country}")

    return dedupe_preserve_order(queries)[: config.max_search_queries]


def dedupe_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        deduped.append(value)
    return deduped
