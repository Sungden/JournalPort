"""Approval binding and replay protection."""

from __future__ import annotations

from datetime import UTC, datetime

from .models import Approval, TransformationAction, TransformationPlan


def proposed_content_hash(action: TransformationAction) -> str:
    from .hashing import canonical_hash

    return canonical_hash(
        {
            "operation": action.operation,
            "parameters": action.parameters,
            "target": action.target_state,
        }
    )


def approval_is_valid(
    approval: Approval, plan: TransformationPlan, action: TransformationAction
) -> bool:
    if approval.status != "APPROVED":
        return False
    if approval.action_id != action.action_id or approval.plan_hash != plan.plan_hash:
        return False
    if approval.proposed_content_hash != proposed_content_hash(action):
        return False
    if approval.expires_at is not None:
        expires = datetime.fromisoformat(approval.expires_at)
        if expires <= datetime.now(UTC):
            return False
    return True
