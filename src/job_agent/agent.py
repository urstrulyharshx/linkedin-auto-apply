from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

from .application_materials import enrich_application_materials
from .auto_apply import annotate_auto_apply
from .config import AgentConfig, load_config
from .extract import extract_job
from .filtering import filter_jobs
from .models import JobLead, SearchResult
from .notifications import maybe_send_results_email
from .ranker import rank_jobs
from .resume import resolve_resume
from .search import build_provider, build_queries
from .spreadsheet import export_jobs_xlsx


def run(dry_run: bool = False, config: AgentConfig | None = None) -> Path:
    config = config or load_config()
    resume_status = resolve_resume(config, allow_local=dry_run)
    raw_jobs = sample_jobs() if dry_run else collect_jobs(config)
    filtered_jobs = filter_jobs(raw_jobs, days_back=config.days_back)
    ranked_jobs = rank_jobs(filtered_jobs, config.openai_api_key, config.openai_model)
    top_jobs = ranked_jobs[: config.max_results]
    top_jobs = enrich_application_materials(
        top_jobs,
        config.applicant_profile,
        config.openai_api_key,
        config.openai_model,
    )
    top_jobs = annotate_auto_apply(
        top_jobs,
        enabled=config.auto_apply_enabled,
        allowed_domains=config.auto_apply_allowed_domains,
        applicant_profile=config.applicant_profile,
        resume_url=resume_status.reference,
    )
    output_path = export_jobs_xlsx(top_jobs, config.output_dir, resume_status=resume_status)
    maybe_send_results_email(config, output_path, top_jobs, resume_status)
    return output_path


def collect_jobs(config: AgentConfig) -> list[JobLead]:
    provider = build_provider(config)
    queries = build_queries(config)
    search_results: list[SearchResult] = []

    per_query_limit = max(5, min(10, config.max_results))
    for query in queries:
        search_results.extend(provider.search(query, limit=per_query_limit))

    jobs: list[JobLead] = []
    for result in search_results:
        jobs.append(extract_job(result, timeout_seconds=config.request_timeout_seconds))
    return jobs


def sample_jobs() -> list[JobLead]:
    today = date.today()
    return [
        JobLead(
            title="Junior AI Engineer",
            company="Example AI Labs",
            location="Bengaluru, India",
            experience="0-2 years",
            work_mode="Hybrid",
            apply_link="https://example.com/jobs/junior-ai-engineer",
            source_platform="Company Careers",
            posted_date=today.isoformat(),
            short_summary="Build Python services for LLM and RAG product features.",
            description="Python, FastAPI, LLM, RAG, vector database, entry level.",
        ),
        JobLead(
            title="Senior Data Scientist",
            company="Example Analytics",
            location="Mumbai, India",
            experience="5 years",
            work_mode="Onsite",
            apply_link="https://example.com/jobs/senior-data-scientist",
            source_platform="Company Careers",
            posted_date=today.isoformat(),
            short_summary="Senior role requiring 5+ years experience.",
            description="Senior data scientist manager role.",
        ),
        JobLead(
            title="Python Backend Developer",
            company="Example SaaS",
            location="Remote, India",
            experience="1-2 years",
            work_mode="Remote",
            apply_link="https://example.com/jobs/python-backend-developer",
            source_platform="Company Careers",
            posted_date=(today - timedelta(days=1)).isoformat(),
            short_summary="Work on backend APIs using Python and SQL.",
            description="Python backend APIs, Django, SQL, junior developer.",
        ),
        JobLead(
            title="Machine Learning Intern",
            company="Example ML",
            location="Hyderabad, India",
            experience="Entry level",
            work_mode="Onsite",
            apply_link="https://example.com/jobs/ml-intern",
            source_platform="Internshala",
            posted_date=(today - timedelta(days=5)).isoformat(),
            short_summary="Old posting should be filtered out.",
            description="Machine learning internship.",
        ),
    ]
