"""Plan/log/manifest reconciliation without trusting executor conclusions."""

from __future__ import annotations

from journalport.transform.models import ActionLog, CandidateManifest, TransformationPlan

VALID_LOG_STATUSES = {
    "APPLIED",
    "MANUAL_ACTION_REQUIRED",
    "BLOCKED_APPROVAL",
    "FAILED",
    "UNSUPPORTED",
    "NOT_APPLICABLE",
}


def reconcile(
    plan: TransformationPlan, logs: tuple[ActionLog, ...], manifest: CandidateManifest
) -> dict[str, str]:
    planned = [item.action_id for item in plan.actions]
    logged = [item.action_id for item in logs]
    known = set(planned)
    statuses_valid = all(item.execution_status in VALID_LOG_STATUSES for item in logs)
    applied = {item.action_id for item in logs if item.execution_status == "APPLIED"}
    pending = {
        item.action_id
        for item in logs
        if item.execution_status in {"MANUAL_ACTION_REQUIRED", "BLOCKED_APPROVAL", "UNSUPPORTED"}
    }
    failed = {item.action_id for item in logs if item.execution_status == "FAILED"}
    checks = {
        "all_planned_actions_accounted_for": "PASS"
        if set(logged) == known and len(logged) == len(planned)
        else "FAIL",
        "no_duplicate_execution": "PASS" if len(logged) == len(set(logged)) else "FAIL",
        "no_unknown_executed_action": "PASS" if set(logged) <= known else "FAIL",
        "status_transitions_valid": "PASS" if statuses_valid else "FAIL",
        "manifest_applied_action_ids": "PASS"
        if applied == set(manifest.applied_action_ids)
        else "FAIL",
        "manifest_pending_action_ids": "PASS"
        if pending == set(manifest.pending_manual_action_ids)
        else "FAIL",
        "manifest_failed_action_ids": "PASS"
        if failed == set(manifest.failed_action_ids)
        else "FAIL",
    }
    return checks
