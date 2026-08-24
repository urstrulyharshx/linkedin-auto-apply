from __future__ import annotations

from dataclasses import replace

from job_agent.config import load_config
from job_agent.search import build_queries


def test_query_builder_respects_free_tier_budget() -> None:
    config = replace(load_config(), max_search_queries=8)
    queries = build_queries(config)
    assert len(queries) == 8
    assert queries[0].startswith("site:naukri.com")
    assert any("site:linkedin.com/jobs" in query for query in queries)
    assert any("site:indeed.com" in query for query in queries)


def test_query_builder_can_expand_when_budget_is_higher() -> None:
    config = replace(load_config(), max_search_queries=20)
    queries = build_queries(config)
    assert len(queries) > 8
    assert any("site:jobs.lever.co" in query for query in queries)
