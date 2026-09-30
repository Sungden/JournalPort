"""Deterministic transformation planner; never executes actions."""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

from journalport import __version__
from journalport.compliance.hashing import report_hash
from journalport.compliance.models import ComplianceFinding, ComplianceReport
from journalport.manuscript.model import CanonicalManuscript
from journalport.manuscript.serialization import logical_hash
from journalport.profiles.hashing import resolved_hash
from journalport.profiles.models import JSONValue, ResolvedJournalProfile

from .hashing import canonical_hash, file_hash, plan_hash
from .models import TransformationAction, TransformationPlan
from .registry import transformation_for


class TransformationInputError(ValueError):
    pass


def _action_id(finding: ComplianceFinding, operation: str, profile_hash: str) -> str:
    payload = json.dumps(
        [finding.finding_id, operation, sorted(finding.affected_object_ids), profile_hash],
        separators=(",", ":"),
    ).encode()
    return "action:" + hashlib.sha256(payload).hexdigest()[:24]


def _action(finding: ComplianceFinding, profile_hash: str) -> TransformationAction:
    operation, classification, support = transformation_for(finding)
    automatic = classification in {"SAFE_AUTOMATIC", "CONTENT_PRESERVING_AUTOMATIC"}
    if operation == "NORMALIZE_OUTPUT_FILENAME":
        parameters: dict[str, JSONValue] = {"output_filename": finding.expected_value}
    elif operation == "REPLACE_ABSTRACT":
        parameters = {
            "target_key": "abstract",
            "expected_precondition_hash": canonical_hash(finding.current_value),
            "payload_transport": "LOCAL_SIDECAR",
        }
    elif operation == "INSERT_REQUIRED_SECTION":
        target_key = finding.rule_id.removeprefix("statements.").rsplit(".", 1)[0]
        parameters = {
            "target_key": target_key,
            "expected_precondition_hash": canonical_hash(finding.current_value),
            "payload_transport": "LOCAL_SIDECAR",
        }
    else:
        parameters = {"proposal_available": False, "manual_revision_required": True}
    return TransformationAction(
        "1.0.0",
        _action_id(finding, operation, profile_hash),
        finding.rule_id,
        finding.finding_id,
        operation,
        support,
        classification,
        finding.affected_object_ids,
        finding.current_value,
        finding.expected_value,
        operation,
        parameters,
        finding.message,
        finding.resolution_trace_reference,
        finding.source_provenance,
        not automatic,
        "NOT_REQUIRED" if automatic else "PENDING",
        (
            "input_artifact_hash_matches",
            "canonical_manuscript_hash_matches",
            "resolved_profile_hash_matches",
            "finding_still_applicable",
        ),
        ("original_source_unchanged", "scientific_fingerprints_preserved"),
        () if automatic else ("MANUAL_OR_SEMANTIC_CHANGE",),
    )


def create_plan(
    manuscript: CanonicalManuscript,
    profile: ResolvedJournalProfile,
    report: ComplianceReport,
    input_artifact: str | Path,
    *,
    created_at: str | None = None,
) -> TransformationPlan:
    artifact = Path(input_artifact)
    canonical = logical_hash(manuscript)
    if canonical != report.canonical_manuscript_hash:
        raise TransformationInputError("canonical manuscript hash mismatch")
    if (
        resolved_hash(profile) != profile.resolved_profile_hash
        or profile.resolved_profile_hash != report.resolved_profile_hash
    ):
        raise TransformationInputError("resolved profile hash mismatch")
    if report_hash(report) != report.report_hash:
        raise TransformationInputError("compliance report hash mismatch")
    artifact_hash = file_hash(artifact)
    if artifact_hash != report.input_manuscript_hash:
        raise TransformationInputError("input artifact hash mismatch")
    actions = tuple(
        _action(finding, profile.resolved_profile_hash)
        for finding in report.findings
        if finding.status not in {"PASS", "NOT_APPLICABLE"}
    )
    automatic = sum(
        not item.requires_approval and item.transformation_status == "SUPPORTED" for item in actions
    )
    approval = sum(item.requires_approval for item in actions)
    forbidden = sum(item.classification == "FORBIDDEN_AUTOMATIC" for item in actions)
    if not actions:
        status = "NO_CHANGES_REQUIRED"
    elif approval:
        status = "APPROVAL_REQUIRED"
    elif automatic:
        status = "READY_FOR_SAFE_EXECUTION"
    else:
        status = "BLOCKED"
    root_version = next(
        item.profile_version
        for item in profile.pinned_profiles
        if item.profile_id == profile.root_profile_id
    )
    plan = TransformationPlan(
        "2.0.0",
        "1.0.0",
        __version__,
        str(artifact.resolve()),
        artifact_hash,
        canonical,
        profile.root_profile_id,
        root_version,
        profile.resolved_profile_hash,
        report.report_hash,
        created_at or datetime.now(UTC).isoformat(),
        actions,
        automatic,
        approval,
        forbidden,
        status,
    )
    return replace(plan, plan_hash=plan_hash(plan))
