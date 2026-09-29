"""Provider-neutral M7 extraction contracts."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from journalport.profiles.models import JSONValue


@dataclass(frozen=True, slots=True)
class DiscoveredSource:
    schema_version: str
    source_id: str
    source_url: str
    source_type: str
    journal: str
    publisher: str
    article_type: str
    discovered_at: str
    retrieval_status: str
    authority_level: int
    official_relationship: str


@dataclass(frozen=True, slots=True)
class EvidenceUnit:
    schema_version: str
    evidence_id: str
    source_id: str
    source_url: str
    source_type: str
    retrieved_at: str
    heading: str
    paragraph: int
    section: str
    anchor: str | None
    evidence_text: str
    evidence_hash: str
    interpretation_notes: str
    authority_level: int


@dataclass(frozen=True, slots=True)
class CandidateRule:
    schema_version: str
    candidate_rule_id: str
    proposed_rule_id: str
    category: str
    target: str
    operator: str
    value: JSONValue
    unit: str | None
    scope: str
    applicability_mode: str
    condition_text: str | None
    machine_checkable: bool
    critical_for_readiness: bool
    severity: str
    autofix_class: str
    evidence_ids: tuple[str, ...]
    confidence: str
    extraction_notes: str


@dataclass(frozen=True, slots=True)
class CandidateConflict:
    proposed_rule_id: str
    candidate_rule_ids: tuple[str, ...]
    values: tuple[JSONValue, ...]
    evidence_ids: tuple[str, ...]
    status: str = "CONFLICTED"


@dataclass(frozen=True, slots=True)
class CandidateProfile:
    schema_version: str
    profile_id: str
    journal: str
    article_type: str
    status: str
    candidate_rules: tuple[CandidateRule, ...]
    conflicts: tuple[CandidateConflict, ...]
    missing_evidence_topics: tuple[str, ...]
    candidate_profile_hash: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ExtractionRun:
    schema_version: str
    run_id: str
    journalport_version: str
    extractor_version: str
    prompt_version: str
    provider: str
    model: str
    settings: dict[str, JSONValue]
    source_urls: tuple[str, ...]
    source_hashes: tuple[str, ...]
    retrieval_timestamps: tuple[str, ...]
    candidate_profile_hash: str
    reviewer_version: str
    created_at: str


@dataclass(frozen=True, slots=True)
class ReviewItem:
    candidate_rule_id: str
    evidence_ids: tuple[str, ...]
    review_status: str
    difference_from_existing: str
    recommended_action: str
    reasons: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ProfileDiffItem:
    rule_id: str
    classification: str
    candidate_rule_id: str | None
    existing_rule_id: str | None
    details: str
