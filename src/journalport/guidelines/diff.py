"""Candidate-to-curated profile comparison performed after blind extraction."""

from __future__ import annotations

from journalport.profiles.models import Profile

from .models import CandidateRule, ProfileDiffItem


def compare_to_curated(
    candidates: tuple[CandidateRule, ...], profile: Profile
) -> tuple[ProfileDiffItem, ...]:
    existing = {item.rule_id: item for item in profile.rules if item.status == "VERIFIED"}
    proposed = {item.proposed_rule_id: item for item in candidates}
    rows: list[ProfileDiffItem] = []
    for rule_id in sorted(set(existing) | set(proposed)):
        old, new = existing.get(rule_id), proposed.get(rule_id)
        if old is None and new is not None:
            classification = "NEW_SUPPORTED_CANDIDATE"
            details = "No curated VERIFIED rule has this identifier."
        elif new is None:
            classification = "MISSING_EXISTING_RULE"
            details = "Blind extraction did not produce this curated VERIFIED rule."
        elif old is not None and old.value != new.value:
            classification = "VALUE_CONFLICT"
            details = "Candidate value differs from curated VERIFIED value."
        elif old is not None and old.operator != new.operator:
            classification = "VALUE_CONFLICT"
            details = "Candidate operator differs from curated VERIFIED operator."
        elif old is not None and old.applicability_mode != new.applicability_mode:
            classification = "APPLICABILITY_CONFLICT"
            details = "Candidate applicability differs from curated VERIFIED applicability."
        else:
            classification = "MATCH_EXISTING"
            details = "Rule identifier, value, and operator match."
        rows.append(
            ProfileDiffItem(
                rule_id,
                classification,
                None if new is None else new.candidate_rule_id,
                None if old is None else old.rule_id,
                details,
            )
        )
    return tuple(rows)
