"""Versioned controlled section aliases; no semantic model is used."""

from __future__ import annotations

import re
import unicodedata

ALIAS_REGISTRY_VERSION = "1.0.0"
ALIASES = {
    "abstract": {"abstract"},
    "introduction": {"introduction", "background"},
    "results": {"results"},
    "discussion": {"discussion"},
    "methods": {"methods", "materials and methods", "online methods"},
    "data_availability": {
        "data availability",
        "availability of data",
        "data and materials availability",
    },
    "code_availability": {"code availability", "availability of code"},
    "author_contributions": {"author contributions", "author contribution statement"},
    "competing_interests": {"competing interests", "conflict of interest", "conflicts of interest"},
    "acknowledgements": {"acknowledgements", "acknowledgments"},
    "ethics": {"ethics", "ethical approval"},
    "consent": {"consent", "consent to participate"},
    "funding": {"funding", "funding information"},
}


def normalize_heading(title: str) -> str:
    value = unicodedata.normalize("NFKC", title).casefold().strip()
    return re.sub(r"[^\w]+", " ", value).strip()


def canonical_section(title: str) -> str | None:
    normalized = normalize_heading(title)
    matches = [name for name, aliases in ALIASES.items() if normalized in aliases]
    return matches[0] if len(matches) == 1 else None
