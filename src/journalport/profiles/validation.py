"""Semantic validation beyond JSON Schema."""

from __future__ import annotations

from dataclasses import dataclass

from .freshness import is_stale
from .models import Profile
from .provenance import validate_profile_provenance


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    code: str
    message: str
    blocking: bool


def validate_profile(
    profile: Profile, *, check_freshness: bool = True
) -> tuple[ValidationIssue, ...]:
    issues: list[ValidationIssue] = []
    expected_precedence = {"PUBLISHER": 100, "JOURNAL": 200, "ARTICLE_TYPE": 300}
    if profile.precedence != expected_precedence[profile.profile_kind]:
        issues.append(
            ValidationIssue("INVALID_PRECEDENCE", "profile precedence must match its kind", True)
        )
    if len({source.source_id for source in profile.sources}) != len(profile.sources):
        issues.append(ValidationIssue("DUPLICATE_SOURCE_ID", "source IDs must be unique", True))
    if len({item.evidence_id for item in profile.evidence}) != len(profile.evidence):
        issues.append(ValidationIssue("DUPLICATE_EVIDENCE_ID", "evidence IDs must be unique", True))
    seen: dict[str, object] = {}
    for rule in profile.rules:
        if rule.rule_id in seen:
            code = "DUPLICATE_RULE" if seen[rule.rule_id] == rule.value else "EQUAL_LEVEL_CONFLICT"
            issues.append(ValidationIssue(code, f"duplicate definition of {rule.rule_id}", True))
        seen[rule.rule_id] = rule.value
    issues.extend(
        ValidationIssue(item.code, f"{item.rule_id}: {item.message}", True)
        for item in validate_profile_provenance(profile)
    )
    if check_freshness and is_stale(profile):
        issues.append(ValidationIssue("STALE_PROFILE", "freshness window has expired", False))
    if profile.status == "VERIFIED" and any(rule.status != "VERIFIED" for rule in profile.rules):
        issues.append(
            ValidationIssue(
                "INFLATED_PROFILE_STATUS", "VERIFIED profile contains non-VERIFIED rules", True
            )
        )
    return tuple(issues)
