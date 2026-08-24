from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(frozen=True)
class SearchResult:
    title: str
    link: str
    snippet: str = ""
    source_platform: str = "unknown"
    displayed_link: str = ""


@dataclass
class JobLead:
    title: str
    company: str
    location: str
    experience: str
    work_mode: str
    apply_link: str
    source_platform: str
    posted_date: str
    short_summary: str
    description: str = ""
    match_score: float = 0.0
    source_url: str = ""
    auto_apply_eligible: bool = False
    auto_apply_reason: str = ""
    application_status: str = "Not submitted"
    tailored_pitch: str = ""
    cover_note: str = ""
    suggested_answers: str = ""
    collected_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat(timespec="seconds"))

    def ranking_text(self) -> str:
        return " ".join(
            [
                self.title,
                self.company,
                self.location,
                self.experience,
                self.work_mode,
                self.short_summary,
                self.description[:2500],
            ]
        )
