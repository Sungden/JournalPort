"""Before/after compliance classification under one pinned profile."""

from __future__ import annotations

from journalport.compliance.models import ComplianceFinding, ComplianceReport

from .models import ComplianceDelta, ComplianceDeltaItem

_RANK = {
    "PASS": 0,
    "NOT_APPLICABLE": 0,
    "WARNING": 1,
    "UNKNOWN": 2,
    "BLOCKED": 3,
    "EVALUATION_ERROR": 3,
    "FAIL": 3,
}


def _change(old: ComplianceFinding | None, new: ComplianceFinding | None) -> str:
    if old is None:
        return "NEW_FINDING"
    if new is None or (old.status not in {"PASS", "NOT_APPLICABLE"} and new.status == "PASS"):
        return "RESOLVED_FINDING"
    if old.status == new.status:
        return "UNCHANGED_FINDING"
    if _RANK.get(new.status, 2) > _RANK.get(old.status, 2):
        return "WORSENED_FINDING"
    return "IMPROVED_FINDING"


def compare_compliance(before: ComplianceReport, after: ComplianceReport) -> ComplianceDelta:
    old = {item.rule_id: item for item in before.findings}
    new = {item.rule_id: item for item in after.findings}
    items: list[ComplianceDeltaItem] = []
    blockers: list[str] = []
    for rule_id in sorted(set(old) | set(new)):
        left, right = old.get(rule_id), new.get(rule_id)
        change = _change(left, right)
        item = right or left
        assert item is not None
        identity = right.finding_id if right else left.finding_id  # type: ignore[union-attr]
        severity = item.severity
        items.append(
            ComplianceDeltaItem(
                identity,
                rule_id,
                change,
                None if left is None else left.status,
                None if right is None else right.status,
                severity,
            )
        )
        if (
            right
            and severity == "BLOCKING"
            and right.status in {"FAIL", "BLOCKED", "EVALUATION_ERROR"}
            and (left is None or left.status not in {"FAIL", "BLOCKED", "EVALUATION_ERROR"})
        ):
            blockers.append(identity)
    return ComplianceDelta(
        "1.0.0",
        before.resolved_profile_hash == after.resolved_profile_hash,
        before.readiness_status,
        after.readiness_status,
        tuple(items),
        tuple(blockers),
    )
