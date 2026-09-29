"""Stable finding-level report comparison."""

from __future__ import annotations

from .models import ComplianceReport


def compare_reports(
    old: ComplianceReport, new: ComplianceReport
) -> dict[str, tuple[str, ...] | bool]:
    old_items = {item.finding_id: item for item in old.findings}
    new_items = {item.finding_id: item for item in new.findings}
    return {
        "new_findings": tuple(sorted(set(new_items) - set(old_items))),
        "resolved_findings": tuple(sorted(set(old_items) - set(new_items))),
        "changed_status": tuple(
            sorted(
                key
                for key in set(old_items) & set(new_items)
                if old_items[key].status != new_items[key].status
            )
        ),
        "profile_changed": old.resolved_profile_hash != new.resolved_profile_hash,
        "manuscript_changed": old.canonical_manuscript_hash != new.canonical_manuscript_hash,
    }
