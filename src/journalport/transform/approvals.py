"""Approval binding and replay protection."""

from __future__ import annotations

from datetime import UTC, datetime

from .hashing import canonical_hash, digest_bytes
from .models import Approval, TransformationAction, TransformationPlan


def proposed_content_hash(action: TransformationAction, payload: str | None = None) -> str:
    return canonical_hash(
        {
            "operation": action.operation,
            "parameters": action.parameters,
            "target": action.target_state,
            "source_artifact_hash_bound_by_plan": True,
            "target_object_ids": action.target_object_ids,
            "payload_hash": None if payload is None else digest_bytes(payload.encode("utf-8")),
        }
    )


def approval_is_valid(
    approval: Approval,
    plan: TransformationPlan,
    action: TransformationAction,
    payload: str | None = None,
) -> bool:
    if approval.status != "APPROVED":
        return False
    if approval.action_id != action.action_id or approval.plan_hash != plan.plan_hash:
        return False
    if approval.proposed_content_hash != proposed_content_hash(action, payload):
        return False
    if approval.expires_at is not None:
        expires = datetime.fromisoformat(approval.expires_at)
        if expires <= datetime.now(UTC):
            return False
    return True
