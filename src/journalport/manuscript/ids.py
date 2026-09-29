"""Deterministic document-local object identifiers."""

from __future__ import annotations

import hashlib
import re
import unicodedata
from collections import defaultdict

_PREFIXES = {
    "document": "doc",
    "section": "sec",
    "subsection": "subsec",
    "paragraph": "para",
    "figure": "fig",
    "figure_legend": "figleg",
    "table": "table",
    "table_legend": "tableleg",
    "equation": "eq",
    "citation": "cite",
    "reference": "ref",
    "footnote": "foot",
    "endnote": "end",
    "supplement": "supp",
    "unsupported": "unsupported",
    "author": "author",
    "affiliation": "aff",
}


def content_fingerprint(value: str) -> str:
    normalized = unicodedata.normalize("NFC", value).replace("\r\n", "\n").replace("\r", "\n")
    normalized = re.sub(r"[ \t]+", " ", normalized).strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


class StableIdFactory:
    """Build IDs from type, stable source anchor, content, and collision ordinal."""

    def __init__(self) -> None:
        self._seen: dict[str, int] = defaultdict(int)

    def make(self, object_type: str, source_anchor: str, content: str = "") -> str:
        prefix = _PREFIXES[object_type]
        digest = hashlib.sha256(
            f"{object_type}\0{source_anchor}\0{content_fingerprint(content)}".encode()
        ).hexdigest()[:16]
        base = f"{prefix}_{digest}"
        ordinal = self._seen[base]
        self._seen[base] += 1
        return base if ordinal == 0 else f"{base}.{ordinal + 1}"
