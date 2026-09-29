"""Canonical JSON report output."""

from __future__ import annotations

import json

from ..models import ComplianceReport


def render_json(report: ComplianceReport) -> str:
    return json.dumps(report.to_dict(), ensure_ascii=False, sort_keys=True, indent=2) + "\n"
