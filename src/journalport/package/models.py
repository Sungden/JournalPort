"""M6 package contracts."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from journalport.profiles.models import ProvenanceRef

ARTIFACT_TYPES = (
    "MAIN_MANUSCRIPT",
    "TITLE_PAGE",
    "COVER_LETTER",
    "FIGURE",
    "TABLE",
    "SUPPLEMENTARY_INFORMATION",
    "SUPPLEMENTARY_DATA",
    "GRAPHICAL_ABSTRACT",
    "HIGHLIGHTS",
    "REPORTING_CHECKLIST",
    "DATA_AVAILABILITY_DOCUMENT",
    "CODE_AVAILABILITY_DOCUMENT",
    "ETHICS_DOCUMENT",
    "CONSENT_DOCUMENT",
    "AUTHOR_CONTRIBUTION_DOCUMENT",
    "COMPETING_INTERESTS_DOCUMENT",
    "SOURCE_FILES",
    "OTHER_REQUIRED_FILE",
)


@dataclass(frozen=True, slots=True)
class ArtifactRequirement:
    requirement_id: str
    artifact_type: str
    requirement_status: str
    condition: str | None
    allowed_formats: tuple[str, ...]
    min_count: int
    max_count: int | None
    filename_rule: str | None
    separate_file_required: bool
    embedded_allowed: bool
    source_rule_id: str
    provenance: tuple[ProvenanceRef, ...]
    critical_for_readiness: bool


@dataclass(frozen=True, slots=True)
class PlannedArtifact:
    artifact_id: str
    artifact_type: str
    source_path: str
    target_relative_path: str
    origin_type: str
    origin_hash: str
    origin_object_ids: tuple[str, ...]
    requirement_status: str
    validation_result: str
    manual_review_status: str


@dataclass(frozen=True, slots=True)
class SubmissionPackagePlan:
    schema_version: str
    plan_version: str
    journalport_version: str
    package_id: str
    target_journal: str
    article_type: str
    profile_id: str
    profile_version: str
    resolved_profile_hash: str
    candidate_path: str
    candidate_hash: str
    verification_report_path: str
    verification_report_hash: str
    compliance_report_path: str
    compliance_report_hash: str
    requirements: tuple[ArtifactRequirement, ...]
    artifacts: tuple[PlannedArtifact, ...]
    missing_requirements: tuple[str, ...]
    conditional_requirements: tuple[str, ...]
    unknown_requirements: tuple[str, ...]
    manual_actions: tuple[str, ...]
    plan_status: str
    created_at: str
    plan_hash: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ManifestArtifact:
    artifact_id: str
    artifact_type: str
    relative_path: str
    file_hash: str
    file_size: int
    format: str
    origin_type: str
    origin_hash: str
    origin_object_ids: tuple[str, ...]
    requirement_status: str
    validation_result: str
    manual_review_status: str
    generated_by: str | None


@dataclass(frozen=True, slots=True)
class SubmissionManifest:
    schema_version: str
    package_id: str
    journalport_version: str
    target_journal: str
    article_type: str
    profile_id: str
    profile_version: str
    resolved_profile_hash: str
    candidate_hash: str
    verification_report_hash: str
    compliance_report_hash: str
    artifacts: tuple[ManifestArtifact, ...]
    missing_requirements: tuple[str, ...]
    conditional_requirements: tuple[str, ...]
    unknown_requirements: tuple[str, ...]
    manual_review_requirements: tuple[str, ...]
    created_at: str
    logical_package_hash: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class PackageReadinessReport:
    schema_version: str
    package_id: str
    candidate_verification_status: str
    compliance_readiness_status: str
    package_completeness_status: str
    profile_confidence_status: str
    known_required_artifacts: int
    present_required_artifacts: int
    missing_artifacts: tuple[str, ...]
    unknown_requirements: tuple[str, ...]
    conditional_requirements: tuple[str, ...]
    file_format_checks: dict[str, str]
    integrity_checks: dict[str, str]
    manual_review_requirements: tuple[str, ...]
    final_package_status: str
    logical_package_hash: str
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def package_plan_from_dict(value: dict[str, Any]) -> SubmissionPackagePlan:
    requirements = tuple(
        ArtifactRequirement(
            **(
                item
                | {
                    "allowed_formats": tuple(item["allowed_formats"]),
                    "provenance": tuple(ProvenanceRef(**x) for x in item["provenance"]),
                }
            )
        )
        for item in value["requirements"]
    )
    artifacts = tuple(
        PlannedArtifact(**(item | {"origin_object_ids": tuple(item["origin_object_ids"])}))
        for item in value["artifacts"]
    )
    return SubmissionPackagePlan(
        **(
            value
            | {
                "requirements": requirements,
                "artifacts": artifacts,
                "missing_requirements": tuple(value["missing_requirements"]),
                "conditional_requirements": tuple(value["conditional_requirements"]),
                "unknown_requirements": tuple(value["unknown_requirements"]),
                "manual_actions": tuple(value["manual_actions"]),
            }
        )
    )


def manifest_from_dict(value: dict[str, Any]) -> SubmissionManifest:
    artifacts = tuple(
        ManifestArtifact(**(item | {"origin_object_ids": tuple(item["origin_object_ids"])}))
        for item in value["artifacts"]
    )
    return SubmissionManifest(
        **(
            value
            | {
                "artifacts": artifacts,
                "missing_requirements": tuple(value["missing_requirements"]),
                "conditional_requirements": tuple(value["conditional_requirements"]),
                "unknown_requirements": tuple(value["unknown_requirements"]),
                "manual_review_requirements": tuple(value["manual_review_requirements"]),
            }
        )
    )
