"""Strict M2 domain records; untrusted files are schema-validated before construction."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

JSONValue = None | bool | int | float | str | list["JSONValue"] | dict[str, "JSONValue"]


@dataclass(frozen=True, slots=True)
class ProfileRef:
    profile_id: str
    profile_version: str


@dataclass(frozen=True, slots=True)
class SourceRecord:
    source_id: str
    source_url: str
    source_type: str
    retrieved_at: str
    source_title: str
    owner: str
    snapshot_hash: str
    snapshot_scope: str
    content_stored: bool
    verification_status: str


@dataclass(frozen=True, slots=True)
class EvidenceRecord:
    evidence_id: str
    source_id: str
    locator: str
    evidence_text: str
    evidence_hash: str


@dataclass(frozen=True, slots=True)
class ProvenanceRef:
    source_id: str
    evidence_id: str


@dataclass(frozen=True, slots=True)
class ProfileRule:
    rule_id: str
    rule_version: str
    category: str
    target: str
    operator: str
    value: JSONValue
    unit: str | None
    severity: str
    applicability: str
    machine_checkable: bool
    autofix_class: str
    provenance: tuple[ProvenanceRef, ...]
    confidence: str
    status: str
    override_of: str | None = None
    override_reason: str | None = None
    applicability_mode: str = "UNKNOWN"
    critical_for_readiness: bool = False
    evaluation_scope: str = "UNSPECIFIED"
    submission_stages: tuple[str, ...] = (
        "INITIAL_SUBMISSION",
        "REVISION",
        "FINAL_SUBMISSION",
        "ACCEPTED",
    )


@dataclass(frozen=True, slots=True)
class JournalIdentity:
    name: str
    publisher: str
    issn: tuple[str, ...]
    journal_url: str


@dataclass(frozen=True, slots=True)
class Profile:
    schema_version: str
    profile_id: str
    display_name: str
    profile_version: str
    source_snapshot_version: str
    profile_kind: str
    precedence: int
    parents: tuple[ProfileRef, ...]
    journal: JournalIdentity | None
    article_type: str | None
    sources: tuple[SourceRecord, ...]
    evidence: tuple[EvidenceRecord, ...]
    rules: tuple[ProfileRule, ...]
    last_verified_at: str
    freshness_window_days: int
    status: str
    transformation_targets: tuple[dict[str, Any], ...] = ()


@dataclass(frozen=True, slots=True)
class RuleCandidate:
    rule: ProfileRule
    profile_id: str
    profile_version: str
    precedence: int


@dataclass(frozen=True, slots=True)
class ResolutionTrace:
    rule_id: str
    candidates: tuple[RuleCandidate, ...]
    selected_profile_id: str | None
    selected_profile_version: str | None
    selected_rule_version: str | None
    classification: str
    override_reason: str | None
    conflicts: tuple[str, ...]
    provenance_chain: tuple[ProvenanceRef, ...]


@dataclass(frozen=True, slots=True)
class ProfileConflict:
    rule_id: str
    candidate_values: tuple[JSONValue, ...]
    source_evidence: tuple[ProvenanceRef, ...]
    source_dates: tuple[str, ...]
    precedence: int
    impact: str
    resolution_status: str = "UNRESOLVED"


@dataclass(frozen=True, slots=True)
class ResolvedJournalProfile:
    schema_version: str
    resolved_profile_version: str
    root_profile_id: str
    pinned_profiles: tuple[ProfileRef, ...]
    effective_rules: tuple[ProfileRule, ...]
    resolution_trace: tuple[ResolutionTrace, ...]
    conflicts: tuple[ProfileConflict, ...]
    status: str
    resolved_profile_hash: str = field(default="")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def profile_from_dict(value: dict[str, Any]) -> Profile:
    journal_value = value.get("journal")
    journal = None
    if journal_value is not None:
        journal = JournalIdentity(
            journal_value["name"],
            journal_value["publisher"],
            tuple(journal_value["issn"]),
            journal_value["journal_url"],
        )
    return Profile(
        schema_version=value["schema_version"],
        profile_id=value["profile_id"],
        display_name=value["display_name"],
        profile_version=value["profile_version"],
        source_snapshot_version=value["source_snapshot_version"],
        profile_kind=value["profile_kind"],
        precedence=value["precedence"],
        parents=tuple(ProfileRef(**item) for item in value["parents"]),
        journal=journal,
        article_type=value.get("article_type"),
        sources=tuple(SourceRecord(**item) for item in value["sources"]),
        evidence=tuple(EvidenceRecord(**item) for item in value["evidence"]),
        rules=tuple(
            ProfileRule(
                **(
                    item
                    | {
                        "provenance": tuple(ProvenanceRef(**ref) for ref in item["provenance"]),
                        "submission_stages": tuple(
                            item.get(
                                "submission_stages",
                                ("INITIAL_SUBMISSION", "REVISION", "FINAL_SUBMISSION", "ACCEPTED"),
                            )
                        ),
                    }
                )
            )
            for item in value["rules"]
        ),
        last_verified_at=value["last_verified_at"],
        freshness_window_days=value["freshness_window_days"],
        status=value["status"],
        transformation_targets=tuple(value.get("transformation_targets", [])),
    )
