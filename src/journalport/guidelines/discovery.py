"""Minimal official navigation adapter; it proposes URLs, never rules."""

from __future__ import annotations

from datetime import UTC, datetime

from .models import DiscoveredSource
from .sources import validate_officiality

NATURE_NAVIGATION = {
    "nature-communications": (
        ("https://www.nature.com/ncomms/submit/article", "OFFICIAL_ARTICLE_TYPE_GUIDELINE", 1),
        ("https://www.nature.com/ncomms/submit/how-to-submit", "OFFICIAL_JOURNAL_GUIDELINE", 2),
    ),
    "nature-computational-science": (
        ("https://www.nature.com/natcomputsci/content", "OFFICIAL_ARTICLE_TYPE_GUIDELINE", 1),
        (
            "https://www.nature.com/natcomputsci/submission-guidelines/preparing-your-submission",
            "OFFICIAL_JOURNAL_GUIDELINE",
            2,
        ),
    ),
    "nature-machine-intelligence": (
        ("https://www.nature.com/natmachintell/content", "OFFICIAL_ARTICLE_TYPE_GUIDELINE", 1),
        (
            "https://www.nature.com/natmachintell/submission-guidelines/preparing-your-submission",
            "OFFICIAL_JOURNAL_GUIDELINE",
            2,
        ),
    ),
}


def discover_sources(
    journal: str, article_type: str, *, discovered_at: str | None = None
) -> tuple[DiscoveredSource, ...]:
    now = discovered_at or datetime.now(UTC).isoformat()
    found: list[DiscoveredSource] = []
    for index, (url, source_type, authority) in enumerate(NATURE_NAVIGATION.get(journal, ())):
        official = validate_officiality(url)
        found.append(
            DiscoveredSource(
                "1.0.0",
                f"source:{journal}:{index + 1}",
                url,
                source_type,
                journal,
                "Nature Portfolio",
                article_type,
                now,
                "NOT_RETRIEVED" if official else "BLOCKED",
                authority if official else 99,
                "JOURNAL_OWNED",
            )
        )
    return tuple(found)
