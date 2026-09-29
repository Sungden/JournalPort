"""Evidence hashing and discrete confidence policy."""

from __future__ import annotations

import hashlib

OFFICIAL_SOURCE_TYPES = {
    "OFFICIAL_JOURNAL_GUIDELINE",
    "OFFICIAL_PUBLISHER_GUIDELINE",
    "OFFICIAL_ARTICLE_TYPE_GUIDELINE",
    "OFFICIAL_SUBMISSION_PORTAL",
    "OFFICIAL_TEMPLATE",
    "OFFICIAL_POLICY",
}


def evidence_hash(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def expected_confidence(source_type: str, *, requires_interpretation: bool = False) -> str:
    if source_type in OFFICIAL_SOURCE_TYPES:
        return "MEDIUM" if requires_interpretation else "HIGH"
    if source_type == "SECONDARY_SOURCE":
        return "LOW"
    return "UNKNOWN"
