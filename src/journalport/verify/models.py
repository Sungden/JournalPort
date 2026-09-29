"""Typed contracts for independent M5 verification."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class VerificationFinding:
    schema_version: str
    finding_id: str
    category: str
    check: str
    status: str
    severity: str
    message: str
    object_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ComplianceDeltaItem:
    finding_id: str
    rule_id: str
    change: str
    before_status: str | None
    after_status: str | None
    severity: str


@dataclass(frozen=True, slots=True)
class ComplianceDelta:
    schema_version: str
    profile_unchanged: bool
    readiness_before: str
    readiness_after: str
    items: tuple[ComplianceDeltaItem, ...]
    new_blocking_findings: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class VerificationReport:
    schema_version: str
    verification_version: str
    journalport_version: str
    source_artifact_hash: str
    candidate_artifact_hash: str
    original_canonical_hash: str
    candidate_canonical_hash: str
    profile_id: str
    profile_version: str
    resolved_profile_hash: str
    compliance_report_before_hash: str
    compliance_report_after_hash: str
    transformation_plan_hash: str
    transformation_log_hash: str
    verification_timestamp: str
    verification_status: str
    transformation_verification_status: str
    compliance_readiness_status: str
    preservation_checks: dict[str, str]
    compliance_checks: dict[str, str]
    postcondition_checks: dict[str, str]
    manifest_checks: dict[str, str]
    tamper_checks: dict[str, str]
    allowed_changes: tuple[str, ...]
    observed_changes: tuple[str, ...]
    unexpected_changes: tuple[str, ...]
    findings: tuple[VerificationFinding, ...]
    manual_review_requirements: tuple[str, ...]
    failure_reasons: tuple[str, ...]
    verification_report_hash: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def verification_report_from_dict(value: dict[str, Any]) -> VerificationReport:
    findings = tuple(
        VerificationFinding(**(item | {"object_ids": tuple(item["object_ids"])}))
        for item in value["findings"]
    )
    return VerificationReport(
        **(
            value
            | {
                "allowed_changes": tuple(value["allowed_changes"]),
                "observed_changes": tuple(value["observed_changes"]),
                "unexpected_changes": tuple(value["unexpected_changes"]),
                "findings": findings,
                "manual_review_requirements": tuple(value["manual_review_requirements"]),
                "failure_reasons": tuple(value["failure_reasons"]),
            }
        )
    )
