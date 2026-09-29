"""Hashing owned by the verifier, independent of executor self-checks."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any

from .models import VerificationReport


def digest_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def artifact_hash(path: Path) -> str:
    return digest_bytes(path.read_bytes())


def canonical_value_hash(value: Any) -> str:
    return digest_bytes(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    )


def verification_report_hash(report: VerificationReport) -> str:
    value = asdict(replace(report, verification_timestamp="", verification_report_hash=""))
    return canonical_value_hash(value)
