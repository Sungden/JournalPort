"""Independent deterministic evidence-attribution review."""

from __future__ import annotations

from collections import defaultdict

from .models import CandidateConflict, CandidateRule, EvidenceUnit, ReviewItem

REVIEWER_VERSION = "1.0.0"


def detect_conflicts(rules: tuple[CandidateRule, ...]) -> tuple[CandidateConflict, ...]:
    grouped: dict[str, list[CandidateRule]] = defaultdict(list)
    for rule in rules:
        grouped[rule.proposed_rule_id].append(rule)
    conflicts: list[CandidateConflict] = []
    for rule_id, candidates in grouped.items():
        values = {repr(item.value) for item in candidates}
        if len(values) > 1:
            conflicts.append(
                CandidateConflict(
                    rule_id,
                    tuple(item.candidate_rule_id for item in candidates),
                    tuple(item.value for item in candidates),
                    tuple(sorted({x for item in candidates for x in item.evidence_ids})),
                )
            )
    return tuple(sorted(conflicts, key=lambda item: item.proposed_rule_id))


def review_rules(
    rules: tuple[CandidateRule, ...],
    evidence_units: tuple[EvidenceUnit, ...],
    conflicts: tuple[CandidateConflict, ...],
) -> tuple[ReviewItem, ...]:
    evidence = {item.evidence_id: item for item in evidence_units}
    conflicted = {item.proposed_rule_id for item in conflicts}
    reviewed: list[ReviewItem] = []
    for rule in rules:
        reasons: list[str] = []
        cited = [evidence.get(item) for item in rule.evidence_ids]
        if not cited or any(item is None for item in cited):
            status = "UNSUPPORTED"
            reasons.append("missing cited evidence")
        elif any(item.authority_level > 5 for item in cited if item):
            status = "UNSUPPORTED"
            reasons.append("source is not authoritative")
        elif rule.proposed_rule_id in conflicted:
            status = "CONFLICTED"
            reasons.append("equal-authority evidence proposes different values")
        elif (
            isinstance(rule.value, int)
            and not isinstance(rule.value, bool)
            and not any(
                str(rule.value) in item.evidence_text.replace(",", "") for item in cited if item
            )
        ):
            status = "UNSUPPORTED"
            reasons.append("numeric value is absent from cited evidence")
        else:
            status = "SUPPORTED"
            reasons.append("official evidence attribution and literal value check passed")
        reviewed.append(
            ReviewItem(
                rule.candidate_rule_id,
                rule.evidence_ids,
                status,
                "NOT_COMPARED",
                "MAINTAINER_REVIEW" if status == "SUPPORTED" else "DO_NOT_ADVANCE",
                tuple(reasons),
            )
        )
    return tuple(reviewed)
