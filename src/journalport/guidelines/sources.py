"""Official-source authority policy."""

from __future__ import annotations

from urllib.parse import urlparse

OFFICIAL_DOMAINS = {"nature.com", "www.nature.com", "submission.nature.com"}


def validate_officiality(url: str, *, relationship: str = "PUBLISHER_OWNED") -> bool:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.username or parsed.password:
        return False
    host = (parsed.hostname or "").lower()
    return host in OFFICIAL_DOMAINS and relationship in {
        "PUBLISHER_OWNED",
        "JOURNAL_OWNED",
        "OFFICIAL_SUBMISSION_PORTAL",
    }
