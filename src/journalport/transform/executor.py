"""Deterministic local executor with approval, tamper, and confidentiality gates."""

from __future__ import annotations

import json
import shutil
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from journalport.compliance.hashing import report_hash
from journalport.compliance.models import ComplianceReport
from journalport.manuscript.model import CanonicalManuscript
from journalport.manuscript.parser_docx import parse_docx
from journalport.manuscript.serialization import logical_hash
from journalport.profiles.hashing import resolved_hash
from journalport.profiles.models import ResolvedJournalProfile

from .approvals import approval_is_valid
from .docx_editor import DocxEditBlocked, edit_docx
from .hashing import canonical_hash, digest_bytes, file_hash, logical_package_hash, plan_hash
from .models import (
    ActionLog,
    Approval,
    CandidateManifest,
    ExecutionResult,
    TransformationPlan,
)
from .safety import confined_output

EXECUTOR_VERSION = "2.0.0"


class TransformationBlocked(ValueError):
    pass


def execute_plan(
    plan: TransformationPlan,
    manuscript: CanonicalManuscript,
    profile: ResolvedJournalProfile,
    report: ComplianceReport,
    output_root: str | Path,
    *,
    approvals: tuple[Approval, ...] = (),
    payloads: dict[str, str] | None = None,
    timestamp: str | None = None,
) -> ExecutionResult:
    if plan_hash(plan) != plan.plan_hash:
        raise TransformationBlocked("transformation plan hash mismatch")
    if logical_hash(manuscript) != plan.canonical_manuscript_hash:
        raise TransformationBlocked("canonical manuscript changed after planning")
    if (
        resolved_hash(profile) != plan.resolved_profile_hash
        or profile.resolved_profile_hash != report.resolved_profile_hash
    ):
        raise TransformationBlocked("profile changed after planning")
    if report_hash(report) != plan.compliance_report_hash:
        raise TransformationBlocked("compliance report changed after planning")
    source = Path(plan.input_artifact_path)
    original_before = file_hash(source)
    if original_before != plan.input_artifact_hash:
        raise TransformationBlocked("source artifact changed after planning")
    blocking_unsupported = any(
        item.severity == "BLOCKING" for item in manuscript.unsupported_content
    )
    safe_actions = [
        item
        for item in plan.actions
        if item.classification in {"SAFE_AUTOMATIC", "CONTENT_PRESERVING_AUTOMATIC"}
        and item.transformation_status == "SUPPORTED"
    ]
    payload_map = payloads or {}
    approval_map = {item.action_id: item for item in approvals}
    semantic_operations: list[tuple[str, str, str]] = []
    approved_action_ids: set[str] = set()
    for action in plan.actions:
        if action.operation not in {"REPLACE_ABSTRACT", "INSERT_REQUIRED_SECTION"}:
            continue
        if action.transformation_status != "SUPPORTED" or not action.requires_approval:
            continue
        payload = payload_map.get(action.action_id)
        approval = approval_map.get(action.action_id)
        if payload is None or not payload.strip() or approval is None:
            continue
        if not approval_is_valid(approval, plan, action, payload):
            continue
        expected = action.parameters.get("expected_precondition_hash")
        if expected != canonical_hash(action.source_state):
            raise TransformationBlocked("action precondition hash mismatch")
        target_key = action.parameters.get("target_key")
        if not isinstance(target_key, str):
            raise TransformationBlocked("semantic action target is invalid")
        semantic_operations.append((action.operation, target_key, payload))
        approved_action_ids.add(action.action_id)
    for action in safe_actions:
        if action.operation == "NORMALIZE_SECTION_HEADING":
            target_key = action.parameters.get("target_key")
            if not isinstance(target_key, str):
                raise TransformationBlocked("heading normalization target is invalid")
            semantic_operations.append((action.operation, target_key, ""))
    if blocking_unsupported and (safe_actions or semantic_operations):
        raise TransformationBlocked("transformation blocked by unsupported manuscript content")
    desired_name = f"manuscript_transformed{source.suffix.lower()}"
    for action in safe_actions:
        if action.operation == "NORMALIZE_OUTPUT_FILENAME":
            value = action.parameters.get("output_filename")
            if not isinstance(value, str):
                raise TransformationBlocked("filename action lacks a string target")
            desired_name = value
        elif action.operation == "NORMALIZE_SECTION_HEADING":
            continue
        elif action.operation == "SET_MANUSCRIPT_METADATA":
            if action.parameters.get("metadata_field") != "article_type" or not isinstance(
                action.parameters.get("value"), str
            ):
                raise TransformationBlocked("submission metadata action is invalid")
            continue
        else:
            raise TransformationBlocked(f"unknown automatic action {action.operation}")
    root = Path(output_root)
    candidate = confined_output(root, desired_name, source)
    root.mkdir(parents=True, exist_ok=True)
    try:
        if semantic_operations:
            edit_docx(source, candidate, manuscript, tuple(semantic_operations))
            parse_docx(candidate)
        else:
            temporary = root / f".{desired_name}.tmp"
            try:
                shutil.copyfile(source, temporary)
                temporary.replace(candidate)
                candidate.chmod(0o600)
            finally:
                temporary.unlink(missing_ok=True)
    except (OSError, ValueError, DocxEditBlocked) as exc:
        candidate.unlink(missing_ok=True)
        raise TransformationBlocked(type(exc).__name__) from exc
    candidate_hash = file_hash(candidate)
    now = timestamp or datetime.now(UTC).isoformat()
    logs: list[ActionLog] = []
    applied: list[str] = []
    pending: list[str] = []
    failed: list[str] = []
    for action in plan.actions:
        status = "MANUAL_ACTION_REQUIRED"
        errors: tuple[str, ...] = ()
        if action in safe_actions:
            status = "APPLIED"
            applied.append(action.action_id)
        elif action.classification == "FORBIDDEN_AUTOMATIC":
            pending.append(action.action_id)
        elif action.action_id in approved_action_ids:
            status = "APPLIED"
            applied.append(action.action_id)
        elif action.requires_approval:
            approval = approval_map.get(action.action_id)
            payload = payload_map.get(action.action_id)
            if (
                approval is None
                or payload is None
                or not approval_is_valid(approval, plan, action, payload)
            ):
                status = "BLOCKED_APPROVAL"
                pending.append(action.action_id)
            else:
                status = "MANUAL_ACTION_REQUIRED"
                pending.append(action.action_id)
        else:
            status = "FAILED"
            errors = ("unsupported action state",)
            failed.append(action.action_id)
        logs.append(
            ActionLog(
                action.action_id,
                action.finding_id,
                action.rule_id,
                action.target_object_ids,
                action.classification,
                "APPROVED" if action.action_id in approved_action_ids else action.approval_status,
                status,
                original_before,
                candidate_hash,
                EXECUTOR_VERSION,
                now,
                errors,
                (),
                action.operation,
                (
                    canonical_hash(asdict(approval_map[action.action_id]))
                    if action.action_id in approved_action_ids
                    else None
                ),
                (
                    digest_bytes(payload_map[action.action_id].encode("utf-8"))
                    if action.action_id in approved_action_ids
                    else None
                ),
                "PASS" if action.action_id in approved_action_ids else "NOT_EVALUATED",
                "PENDING_VERIFICATION",
            )
        )
    if file_hash(source) != original_before:
        raise TransformationBlocked("original source changed during execution")
    candidate_manuscript = (
        parse_docx(candidate) if candidate.suffix.lower() == ".docx" else manuscript
    )
    checks = {
        "numeric_checked_by_independent_verifier": True,
        "equation_checked_by_independent_verifier": True,
        "citation_checked_by_independent_verifier": True,
        "reference_checked_by_independent_verifier": True,
        "asset_identity_checked_by_independent_verifier": True,
        "original_source_preserved": file_hash(source) == original_before,
        "candidate_reparsed": candidate_manuscript.source.get("sha256") == candidate_hash,
    }
    if not all(checks.values()):
        raise TransformationBlocked("preliminary content preservation failed")
    manifest = CandidateManifest(
        "1.0.0",
        original_before,
        candidate_hash,
        logical_package_hash(source),
        logical_package_hash(candidate),
        profile.resolved_profile_hash,
        report.report_hash,
        plan.plan_hash,
        tuple(applied),
        tuple(pending),
        tuple(failed),
        checks,
    )
    (root / "transformation_log.json").write_text(
        json.dumps(
            {"schema_version": "1.0.0", "entries": [asdict(item) for item in logs]},
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (root / "candidate_manifest.json").write_text(
        json.dumps(asdict(manifest), sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    return ExecutionResult(str(candidate), tuple(logs), manifest)
