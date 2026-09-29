"""Minimal evidence segmentation from untrusted source content."""

from __future__ import annotations

import html
import re

from .hashing import digest_text
from .models import EvidenceUnit
from .retrieval import RetrievalSnapshot

SCRIPT_STYLE = re.compile(r"(?is)<(script|style|noscript|nav|aside)[^>]*>.*?</\1>")
HIDDEN = re.compile(r"(?is)<[^>]*(?:hidden|display\s*:\s*none)[^>]*>.*?</[^>]+>")
TAGS = re.compile(r"<[^>]+>")
SPACE = re.compile(r"\s+")


def visible_text(content: str) -> str:
    cleaned = SCRIPT_STYLE.sub(" ", content)
    cleaned = HIDDEN.sub(" ", cleaned)
    cleaned = TAGS.sub("\n", cleaned)
    return SPACE.sub(" ", html.unescape(cleaned)).strip()


def segment_evidence(snapshot: RetrievalSnapshot) -> tuple[EvidenceUnit, ...]:
    if snapshot.retrieval_status != "RETRIEVED":
        return ()
    text = visible_text(snapshot.content)
    paragraphs = [
        part.strip() for part in re.split(r"\n{2,}|(?<=[.!?])\s+(?=[A-Z])", text) if part.strip()
    ]
    units: list[EvidenceUnit] = []
    for index, paragraph in enumerate(paragraphs):
        if len(paragraph) < 12:
            continue
        digest = digest_text(paragraph)
        units.append(
            EvidenceUnit(
                "1.0.0",
                f"evidence:{digest.split(':', 1)[1][:24]}",
                snapshot.source.source_id,
                snapshot.source.source_url,
                snapshot.source.source_type,
                snapshot.retrieved_at,
                snapshot.page_title,
                index + 1,
                "document",
                None,
                paragraph,
                digest,
                "Untrusted external text; interpretation is stored only in candidate rules.",
                snapshot.source.authority_level,
            )
        )
    return tuple(units)
