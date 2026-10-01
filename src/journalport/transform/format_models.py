"""M12 source-to-target format transformation contracts."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

FormatSafetyClass = Literal[
    "SAFE_FORMAT_AUTOMATIC",
    "CONTENT_PRESERVING_AUTOMATIC",
    "AUTHOR_APPROVAL_REQUIRED",
    "AUTHOR_INPUT_REQUIRED",
    "MANUAL_REVIEW_REQUIRED",
    "FORBIDDEN_AUTOMATIC",
    "PROFILE_UNCERTAIN",
]


@dataclass(frozen=True, slots=True)
class FormatRuleTarget:
    rule_id: str
    target_state: Any
    profile_status: str
    evidence: tuple[dict[str, str], ...] = ()
    confidence: str = "HIGH"
    submission_stages: tuple[str, ...] = (
        "INITIAL_SUBMISSION",
        "REVISION",
        "FINAL_SUBMISSION",
        "ACCEPTED",
    )


@dataclass(frozen=True, slots=True)
class FormatOperation:
    operation_id: str
    rule_id: str
    operation: str
    target_object: str
    parameters: dict[str, Any]
    evidence: tuple[dict[str, str], ...]
    classification: FormatSafetyClass
    executor_support: str
    approval_requirement: str
    confidence: str
    profile_status: str
    preconditions: tuple[str, ...]
    expected_delta: dict[str, Any]
    depends_on: tuple[str, ...] = ()
    conflicts_with: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class TransferMatrixRow:
    rule_id: str
    source_state: Any
    target_state: Any
    current_state: Any
    action: str
    operation: str
    executor_support: str
    risk: FormatSafetyClass
    approval: str
    status: str
    profile_status: str
    confidence: str
    evidence: tuple[dict[str, str], ...] = ()


@dataclass(frozen=True, slots=True)
class FormatTransformationPlan:
    schema_version: str
    source_mode: str
    source_journal: str | None
    target_journal: str
    profile_version: str
    source_hash: str
    operations: tuple[FormatOperation, ...]
    transfer_matrix: tuple[TransferMatrixRow, ...]
    execution_order: tuple[str, ...]
    submission_stage: str = "INITIAL_SUBMISSION"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class FormatArtifact:
    relative_path: str
    artifact_type: str
    sha256: str
    source_relationship: str | None = None


@dataclass(frozen=True, slots=True)
class FormatExecutionResult:
    source_path: str
    candidate_path: str
    source_hash: str
    candidate_hash: str
    applied_operations: tuple[str, ...]
    artifacts: tuple[FormatArtifact, ...] = ()
    operation_records: tuple[dict[str, Any], ...] = ()


@dataclass(frozen=True, slots=True)
class OperationVerification:
    operation_id: str
    operation: str
    status: str
    checks: dict[str, bool]
    failure_reasons: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class FormatVerificationReport:
    schema_version: str
    transformation_verification_status: str
    source_hash: str
    candidate_hash: str
    operations: tuple[OperationVerification, ...]
    preservation_checks: dict[str, bool]
    unexpected_changes: tuple[str, ...] = ()
    failure_reasons: tuple[str, ...] = ()
    remaining_target_requirements: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
