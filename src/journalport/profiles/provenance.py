"""Deterministic provenance-chain validation."""

from __future__ import annotations

from dataclasses import dataclass

from .evidence import OFFICIAL_SOURCE_TYPES, evidence_hash
from .models import Profile, ProfileRule


@dataclass(frozen=True, slots=True)
class ProvenanceIssue:
    profile_id: str
    rule_id: str
    code: str
    message: str


def validate_rule_provenance(profile: Profile, rule: ProfileRule) -> tuple[ProvenanceIssue, ...]:
    issues: list[ProvenanceIssue] = []
    sources = {item.source_id: item for item in profile.sources}
    evidence = {item.evidence_id: item for item in profile.evidence}
    if rule.status == "VERIFIED" and not rule.provenance:
        issues.append(
            ProvenanceIssue(
                profile.profile_id,
                rule.rule_id,
                "MISSING_PROVENANCE",
                "VERIFIED rule has no provenance",
            )
        )
    for reference in rule.provenance:
        source = sources.get(reference.source_id)
        item = evidence.get(reference.evidence_id)
        if source is None:
            issues.append(
                ProvenanceIssue(
                    profile.profile_id, rule.rule_id, "UNKNOWN_SOURCE", reference.source_id
                )
            )
            continue
        if item is None:
            issues.append(
                ProvenanceIssue(
                    profile.profile_id, rule.rule_id, "UNKNOWN_EVIDENCE", reference.evidence_id
                )
            )
            continue
        if item.source_id != source.source_id:
            issues.append(
                ProvenanceIssue(
                    profile.profile_id,
                    rule.rule_id,
                    "EVIDENCE_SOURCE_MISMATCH",
                    reference.evidence_id,
                )
            )
        if item.evidence_hash != evidence_hash(item.evidence_text):
            issues.append(
                ProvenanceIssue(
                    profile.profile_id,
                    rule.rule_id,
                    "EVIDENCE_HASH_MISMATCH",
                    reference.evidence_id,
                )
            )
        if rule.status == "VERIFIED" and source.source_type not in OFFICIAL_SOURCE_TYPES:
            issues.append(
                ProvenanceIssue(
                    profile.profile_id,
                    rule.rule_id,
                    "NON_OFFICIAL_VERIFIED_SOURCE",
                    source.source_type,
                )
            )
        if rule.status == "VERIFIED" and source.verification_status != "VERIFIED":
            issues.append(
                ProvenanceIssue(
                    profile.profile_id, rule.rule_id, "UNVERIFIED_SOURCE", source.source_id
                )
            )
        if rule.status == "VERIFIED" and rule.confidence not in {"HIGH", "MEDIUM"}:
            issues.append(
                ProvenanceIssue(
                    profile.profile_id, rule.rule_id, "INVALID_VERIFIED_CONFIDENCE", rule.confidence
                )
            )
    return tuple(issues)


def validate_profile_provenance(profile: Profile) -> tuple[ProvenanceIssue, ...]:
    return tuple(
        issue for rule in profile.rules for issue in validate_rule_provenance(profile, rule)
    )
