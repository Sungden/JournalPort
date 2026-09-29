"""Frozen M3 counting semantics."""

from __future__ import annotations

import re
import unicodedata

WORD_PATTERN = re.compile(r"[^\W_]+(?:[-\u2019'][^\W_]+)*", re.UNICODE)


def word_count(text: str) -> int:
    return len(WORD_PATTERN.findall(unicodedata.normalize("NFC", text)))


def character_count(text: str) -> int:
    return len(unicodedata.normalize("NFC", text))
