from __future__ import annotations

import json
import re
from dataclasses import asdict

from .models import JobLead


TARGET_PROFILE = """
Target roles: AI Engineer, AI Developer, Machine Learning Engineer, Gen AI Developer,
Python Backend Developer, Data Scientist. Country: India. Experience: entry level,
freshers, internships converted to jobs, junior roles, and 0 to 2 years only.
Work modes: remote, hybrid, or onsite.
Prefer: Python, APIs, FastAPI/Django, machine learning, LLMs, RAG, LangChain,
vector databases, data science, SQL, cloud, MLOps, model deployment.
Reject: senior, lead, principal, manager, unrelated sales/recruiting/training roles.
"""


def rank_jobs(jobs: list[JobLead], openai_api_key: str | None, model: str) -> list[JobLead]:
    if openai_api_key:
        try:
            return rank_with_openai(jobs, model)
        except Exception:
            pass
    for job in jobs:
        job.match_score = heuristic_score(job)
    return sorted(jobs, key=lambda item: item.match_score, reverse=True)


def rank_with_openai(jobs: list[JobLead], model: str) -> list[JobLead]:
    from openai import OpenAI

    client = OpenAI()
    compact_jobs = [
        {
            "index": index,
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "experience": job.experience,
            "work_mode": job.work_mode,
            "posted_date": job.posted_date,
            "summary": job.short_summary,
        }
        for index, job in enumerate(jobs)
    ]

    prompt = {
        "target_profile": TARGET_PROFILE,
        "instruction": "Score each job from 0 to 100 for relevance. Return only JSON: [{\"index\":0,\"score\":87,\"reason\":\"short reason\"}].",
        "jobs": compact_jobs,
    }
    response = client.responses.create(
        model=model,
        input=json.dumps(prompt),
    )
    raw_text = response.output_text
    scored = json.loads(extract_json_array(raw_text))
    score_by_index = {int(item["index"]): float(item["score"]) for item in scored}

    for index, job in enumerate(jobs):
        job.match_score = max(0.0, min(100.0, score_by_index.get(index, heuristic_score(job))))
    return sorted(jobs, key=lambda item: item.match_score, reverse=True)


def heuristic_score(job: JobLead) -> float:
    text = job.ranking_text().lower()
    score = 35.0

    weighted_terms = {
        "ai engineer": 14,
        "ai developer": 14,
        "machine learning": 14,
        "generative ai": 14,
        "gen ai": 14,
        "python": 12,
        "backend": 9,
        "fastapi": 8,
        "django": 6,
        "data scientist": 13,
        "llm": 10,
        "rag": 9,
        "langchain": 8,
        "sql": 5,
        "remote": 4,
        "hybrid": 3,
        "entry level": 8,
        "fresher": 8,
        "0-2": 8,
    }
    for term, weight in weighted_terms.items():
        if term in text:
            score += weight

    penalties = {
        "senior": 35,
        "lead": 28,
        "principal": 35,
        "manager": 25,
        "recruiter": 30,
        "sales": 20,
        "trainer": 25,
    }
    for term, penalty in penalties.items():
        if re.search(rf"\b{re.escape(term)}\b", text):
            score -= penalty

    return round(max(0.0, min(100.0, score)), 1)


def extract_json_array(value: str) -> str:
    start = value.find("[")
    end = value.rfind("]")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("OpenAI response did not contain a JSON array.")
    return value[start : end + 1]
