"""Typed transformation, approval, log, and candidate contracts."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from journalport.profiles.models import JSONValue, ProvenanceRef


@dataclass(frozen=True, slots=True)
class TransformationAction:
    schema_version: str
    action_id: str
    rule_id: str
    finding_id: str
    transformation_type: str
    transformation_status: str
    classification: str
    target_object_ids: tuple[str, ...]
    source_state: JSONValue
    target_state: JSONValue
    operation: str
    parameters: dict[str, JSONValue]
    reason: str
    journal_rule_reference: str
    journal_provenance: tuple[ProvenanceRef, ...]
    requires_approval: bool
    approval_status: str
    preconditions: tuple[str, ...]
    expected_postconditions: tuple[str, ...]
    risk_flags: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class TransformationPlan:
    schema_version: str
    plan_version: str
    journalport_version: str
    input_artifact_path: str
    input_artifact_hash: str
    canonical_manuscript_hash: str
    profile_id: str
    profile_version: str
    resolved_profile_hash: str
    compliance_report_hash: str
    created_at: str
    actions: tuple[TransformationAction, ...]
    automatic_action_count: int
    approval_required_action_count: int
    forbidden_action_count: int
    plan_status: str
    plan_hash: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def transformation_plan_from_dict(value: dict[str, Any]) -> TransformationPlan:
    actions = tuple(
        TransformationAction(
            **(
                item
                | {
                    "target_object_ids": tuple(item["target_object_ids"]),
                    "journal_provenance": tuple(
                        ProvenanceRef(**ref) for ref in item["journal_provenance"]
                    ),
                    "preconditions": tuple(item["preconditions"]),
                    "expected_postconditions": tuple(item["expected_postconditions"]),
                    "risk_flags": tuple(item["risk_flags"]),
                }
            )
        )
        for item in value["actions"]
    )
    return TransformationPlan(**(value | {"actions": actions}))


@dataclass(frozen=True, slots=True)
class Approval:
    schema_version: str
    action_id: str
    plan_hash: str
    proposed_content_hash: str
    status: str
    approved_by: str
    approved_at: str
    expires_at: str | None = None


@dataclass(frozen=True, slots=True)
class ActionLog:
    action_id: str
    finding_id: str
    rule_id: str
    input_object_ids: tuple[str, ...]
    classification: str
    approval_state: str
    execution_status: str
    before_hash: str
    after_hash: str
    executor_version: str
    timestamp: str
    errors: tuple[str, ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CandidateManifest:
    schema_version: str
    source_hash: str
    candidate_hash: str
    logical_source_hash: str
    logical_candidate_hash: str
    profile_hash: str
    compliance_report_hash: str
    transformation_plan_hash: str
    applied_action_ids: tuple[str, ...]
    pending_manual_action_ids: tuple[str, ...]
    failed_action_ids: tuple[str, ...]
    preliminary_preservation_checks: dict[str, bool]
    status: str = "TRANSFORMED_CANDIDATE"


@dataclass(frozen=True, slots=True)
class ExecutionResult:
    candidate_path: str
    logs: tuple[ActionLog, ...]
    manifest: CandidateManifest
