from __future__ import annotations

import re
from datetime import date, datetime, timedelta, timezone

from dateutil import parser


RELATIVE_DATE_PATTERNS = [
    (re.compile(r"\b(today|just posted|few hours ago|hours ago|hour ago)\b", re.I), 0),
    (re.compile(r"\b(yesterday|1 day ago)\b", re.I), 1),
    (re.compile(r"\b(\d+)\s+days?\s+ago\b", re.I), None),
]


def today_utc() -> date:
    return datetime.now(timezone.utc).date()


def parse_posted_date(value: str, today: date | None = None) -> date | None:
    if not value:
        return None

    today = today or today_utc()
    text = value.strip()

    for pattern, fixed_days in RELATIVE_DATE_PATTERNS:
        match = pattern.search(text)
        if not match:
            continue
        if fixed_days is not None:
            return today - timedelta(days=fixed_days)
        return today - timedelta(days=int(match.group(1)))

    try:
        parsed = parser.parse(text, fuzzy=True)
    except (ValueError, OverflowError):
        return None
    return parsed.date()


def is_within_days(value: str, days_back: int, today: date | None = None) -> bool:
    parsed = parse_posted_date(value, today=today)
    if parsed is None:
        return False
    today = today or today_utc()
    return today - timedelta(days=days_back) <= parsed <= today
