"""Stable action/plan/content hashing."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any

from .models import TransformationPlan


def digest_bytes(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def file_hash(path: Path) -> str:
    return digest_bytes(path.read_bytes())


def canonical_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return digest_bytes(payload)


def plan_hash(plan: TransformationPlan) -> str:
    return canonical_hash(asdict(replace(plan, created_at="", plan_hash="")))


def logical_package_hash(path: Path) -> str:
    # M4 only performs byte-preserving copies; container-aware canonical ZIP hashing is deferred.
    return file_hash(path)
