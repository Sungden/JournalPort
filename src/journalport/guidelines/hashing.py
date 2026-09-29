"""Canonical extraction hashing."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, replace
from typing import Any

from .models import CandidateProfile


def digest_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def canonical_hash(value: Any) -> str:
    return digest_text(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")))


def candidate_profile_hash(profile: CandidateProfile) -> str:
    return canonical_hash(asdict(replace(profile, candidate_profile_hash="")))
