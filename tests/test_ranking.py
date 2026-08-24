from __future__ import annotations

from job_agent.agent import sample_jobs
from job_agent.filtering import filter_jobs
from job_agent.ranker import rank_jobs


def test_heuristic_ranking_prioritizes_relevant_jobs() -> None:
    filtered = filter_jobs(sample_jobs(), days_back=3)
    ranked = rank_jobs(filtered, openai_api_key=None, model="unused")
    assert ranked
    assert ranked[0].match_score >= ranked[-1].match_score
    assert all(job.match_score > 0 for job in ranked)
