"""Canonical report hashing excluding time and the hash field itself."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, replace

from .models import ComplianceReport


def report_hash(report: ComplianceReport) -> str:
    value = asdict(replace(report, evaluation_timestamp="", report_hash=""))
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return "sha256:" + hashlib.sha256(payload).hexdigest()
