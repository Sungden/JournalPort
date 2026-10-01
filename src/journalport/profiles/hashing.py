"""Deterministic profile and resolution hashing."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from typing import Any

from .models import ResolvedJournalProfile


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def resolved_hash(profile: ResolvedJournalProfile) -> str:
    value = asdict(profile)
    value.pop("resolved_profile_hash", None)

    # M3 added optional policy fields. Omitting their fail-closed defaults preserves
    # every M2 hash; explicit behavior-changing values remain hash-significant.
    def strip_defaults(item: Any) -> None:
        if isinstance(item, dict):
            if item.get("applicability_mode") == "UNKNOWN":
                item.pop("applicability_mode")
            if item.get("critical_for_readiness") is False:
                item.pop("critical_for_readiness")
            if item.get("evaluation_scope") == "UNSPECIFIED":
                item.pop("evaluation_scope")
            if item.get("submission_stages") == (
                "INITIAL_SUBMISSION",
                "REVISION",
                "FINAL_SUBMISSION",
                "ACCEPTED",
            ):
                item.pop("submission_stages")
            for child in item.values():
                strip_defaults(child)
        elif isinstance(item, (list, tuple)):
            for child in item:
                strip_defaults(child)

    strip_defaults(value)
    return "sha256:" + hashlib.sha256(canonical_json(value)).hexdigest()
