"""Deterministic readiness policy."""

from __future__ import annotations

from .models import ComplianceFinding


def derive_readiness(findings: tuple[ComplianceFinding, ...], profile_status: str) -> str:
    if any(x.status == "EVALUATION_ERROR" and x.critical_for_readiness for x in findings):
        return "EVALUATION_FAILED"
    if any(x.status == "BLOCKED" for x in findings):
        return "BLOCKED"
    if profile_status == "CONFLICTED" or any(
        x.rule_status == "CONFLICTED" and x.critical_for_readiness for x in findings
    ):
        return "PROFILE_NOT_VERIFIABLE"
    if profile_status == "STALE":
        return "PROFILE_NOT_VERIFIABLE"
    if profile_status != "VERIFIED" or any(
        x.status == "UNKNOWN" and x.critical_for_readiness for x in findings
    ):
        return "REQUIRES_MANUAL_REVIEW"
    if any(x.status in {"WARNING", "UNKNOWN"} for x in findings):
        return "READY_WITH_WARNINGS"
    return "SUBMISSION_READY"
