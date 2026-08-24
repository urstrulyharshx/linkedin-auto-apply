from __future__ import annotations

import json

from .models import JobLead


def enrich_application_materials(
    jobs: list[JobLead],
    applicant_profile: dict,
    openai_api_key: str | None,
    model: str,
) -> list[JobLead]:
    if openai_api_key and applicant_profile:
        try:
            return enrich_with_openai(jobs, applicant_profile, model)
        except Exception:
            pass

    for job in jobs:
        fill_template_materials(job, applicant_profile)
    return jobs


def enrich_with_openai(jobs: list[JobLead], applicant_profile: dict, model: str) -> list[JobLead]:
    from openai import OpenAI

    client = OpenAI()
    prompt = {
        "instruction": (
            "For each job, create concise, truthful application material using only the applicant profile. "
            "Return JSON array with index, tailored_pitch, cover_note, suggested_answers. "
            "Do not invent credentials, employment history, degrees, certifications, salary, or notice period."
        ),
        "applicant_profile": applicant_profile,
        "jobs": [
            {
                "index": index,
                "title": job.title,
                "company": job.company,
                "summary": job.short_summary,
                "description": job.description[:2500],
            }
            for index, job in enumerate(jobs)
        ],
    }
    response = client.responses.create(model=model, input=json.dumps(prompt))
    rows = json.loads(extract_json_array(response.output_text))
    rows_by_index = {int(row["index"]): row for row in rows}

    for index, job in enumerate(jobs):
        row = rows_by_index.get(index, {})
        job.tailored_pitch = clean_cell(row.get("tailored_pitch", ""))
        job.cover_note = clean_cell(row.get("cover_note", ""))
        job.suggested_answers = clean_cell(row.get("suggested_answers", ""))
        if not job.tailored_pitch:
            fill_template_materials(job, applicant_profile)
    return jobs


def fill_template_materials(job: JobLead, applicant_profile: dict) -> None:
    skills = applicant_profile.get("skills") if isinstance(applicant_profile.get("skills"), list) else []
    summary = applicant_profile.get("summary", "I have hands-on interest and experience in Python, AI, and backend engineering.")
    skill_text = ", ".join(str(skill) for skill in skills[:8]) or "Python, machine learning, backend APIs, SQL"

    job.tailored_pitch = (
        f"I am interested in the {job.title} role at {job.company}. "
        f"My background aligns with the role through {skill_text}."
    )
    job.cover_note = (
        f"Hello {job.company} team, I would like to apply for {job.title}. "
        f"{summary} I am especially interested in contributing to this role because it matches my target areas: "
        "AI/ML, GenAI, Python backend systems, and data-driven products."
    )
    job.suggested_answers = (
        "Expected CTC: fill manually | Current CTC: fill manually | Notice period: fill manually | "
        "Work authorization: India | Relocation: open based on role"
    )


def extract_json_array(value: str) -> str:
    start = value.find("[")
    end = value.rfind("]")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("OpenAI response did not contain a JSON array.")
    return value[start : end + 1]


def clean_cell(value: object) -> str:
    return " ".join(str(value or "").split())
