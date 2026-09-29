"""Typed M3 finding and report contracts."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from journalport.profiles.models import JSONValue, ProvenanceRef


@dataclass(frozen=True, slots=True)
class Selection:
    target_type: str
    object_ids: tuple[str, ...]
    value: JSONValue
    method: str
    error: str | None = None


@dataclass(frozen=True, slots=True)
class ComplianceFinding:
    schema_version: str
    finding_id: str
    rule_id: str
    rule_version: str
    profile_id: str
    resolved_profile_hash: str
    status: str
    severity: str
    target_type: str
    affected_object_ids: tuple[str, ...]
    current_value: JSONValue
    expected_value: JSONValue
    operator: str
    unit: str | None
    message: str
    recommended_action: str
    machine_checkable: bool
    autofix_class: str
    automatic_fix_available: bool
    rule_status: str
    critical_for_readiness: bool
    source_provenance: tuple[ProvenanceRef, ...]
    resolution_trace_reference: str
    evaluation_method: str
    evaluator_version: str


@dataclass(frozen=True, slots=True)
class Coverage:
    total_rules: int
    verified_rules: int
    partial_rules: int
    unknown_rules: int
    machine_checkable_rules: int
    machine_evaluated_rules: int
    manual_review_rules: int
    unsupported_evaluator_rules: int


@dataclass(frozen=True, slots=True)
class ComplianceReport:
    schema_version: str
    journalport_version: str
    engine_version: str
    input_manuscript_hash: str
    canonical_manuscript_hash: str
    profile_id: str
    profile_version: str
    resolved_profile_hash: str
    evaluation_timestamp: str
    readiness_status: str
    summary: dict[str, int]
    coverage: Coverage
    findings: tuple[ComplianceFinding, ...]
    profile_caveats: tuple[str, ...]
    unsupported_manuscript_content: tuple[str, ...]
    manual_review_requirements: tuple[str, ...]
    disclaimer: str
    report_hash: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def compliance_report_from_dict(value: dict[str, Any]) -> ComplianceReport:
    findings = tuple(
        ComplianceFinding(
            **(
                item
                | {
                    "affected_object_ids": tuple(item["affected_object_ids"]),
                    "source_provenance": tuple(
                        ProvenanceRef(**ref) for ref in item["source_provenance"]
                    ),
                }
            )
        )
        for item in value["findings"]
    )
    return ComplianceReport(
        **(
            value
            | {
                "coverage": Coverage(**value["coverage"]),
                "findings": findings,
                "profile_caveats": tuple(value["profile_caveats"]),
                "unsupported_manuscript_content": tuple(value["unsupported_manuscript_content"]),
                "manual_review_requirements": tuple(value["manual_review_requirements"]),
            }
        )
    )
