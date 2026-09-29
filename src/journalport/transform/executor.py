"""Safe-copy M4 executor with approval and tamper gates."""

from __future__ import annotations

import json
import shutil
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from journalport.compliance.hashing import report_hash
from journalport.compliance.models import ComplianceReport
from journalport.manuscript.fingerprints import fingerprint
from journalport.manuscript.model import CanonicalManuscript
from journalport.manuscript.serialization import logical_hash
from journalport.profiles.hashing import resolved_hash
from journalport.profiles.models import ResolvedJournalProfile

from .approvals import approval_is_valid
from .hashing import file_hash, logical_package_hash, plan_hash
from .models import (
    ActionLog,
    Approval,
    CandidateManifest,
    ExecutionResult,
    TransformationPlan,
)
from .safety import confined_output

EXECUTOR_VERSION = "1.0.0"


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
    if blocking_unsupported and safe_actions:
        raise TransformationBlocked("transformation blocked by unsupported manuscript content")
    desired_name = f"manuscript_transformed{source.suffix.lower()}"
    for action in safe_actions:
        if action.operation == "NORMALIZE_OUTPUT_FILENAME":
            value = action.parameters.get("output_filename")
            if not isinstance(value, str):
                raise TransformationBlocked("filename action lacks a string target")
            desired_name = value
        else:
            raise TransformationBlocked(f"unknown automatic action {action.operation}")
    root = Path(output_root)
    candidate = confined_output(root, desired_name, source)
    root.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, candidate)
    candidate_hash = file_hash(candidate)
    now = timestamp or datetime.now(UTC).isoformat()
    approval_map = {item.action_id: item for item in approvals}
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
        elif action.requires_approval:
            approval = approval_map.get(action.action_id)
            if approval is None or not approval_is_valid(approval, plan, action):
                status = "BLOCKED_APPROVAL"
                pending.append(action.action_id)
            else:
                # Approval is valid, but M4 deliberately has no semantic executor.
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
                action.approval_status,
                status,
                original_before,
                candidate_hash,
                EXECUTOR_VERSION,
                now,
                errors,
                (),
            )
        )
    if file_hash(source) != original_before:
        raise TransformationBlocked("original source changed during execution")
    before_fp = fingerprint(manuscript)
    after_fp = fingerprint(manuscript)
    checks = {
        "numeric_preserved": before_fp.numeric == after_fp.numeric,
        "equation_preserved": before_fp.equation == after_fp.equation,
        "citation_preserved": before_fp.citation == after_fp.citation,
        "reference_preserved": before_fp.reference == after_fp.reference,
        "asset_identity_preserved": before_fp.asset == after_fp.asset,
        "original_source_preserved": file_hash(source) == original_before,
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
