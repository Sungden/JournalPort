"""Logical package, plan, and manifest hashing."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any

from .models import SubmissionManifest, SubmissionPackagePlan


def digest_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def file_hash(path: Path) -> str:
    return digest_bytes(path.read_bytes())


def canonical_hash(value: Any) -> str:
    return digest_bytes(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    )


def package_plan_hash(plan: SubmissionPackagePlan) -> str:
    return canonical_hash(asdict(replace(plan, created_at="", plan_hash="")))


def logical_package_hash(manifest: SubmissionManifest) -> str:
    value = asdict(replace(manifest, created_at="", logical_package_hash=""))
    return canonical_hash(value)
