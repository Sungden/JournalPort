"""Stage-aware document targets resolved from pinned publisher/journal/article layers."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .evidence import OFFICIAL_SOURCE_TYPES, evidence_hash
from .freshness import is_stale
from .loader import ProfileRegistry
from .models import ResolvedJournalProfile

STAGES = ("INITIAL_SUBMISSION", "REVISION", "FINAL_SUBMISSION", "ACCEPTED")

EXECUTORS = {
    "availability.placement": "ORDER_CONDITIONAL_SECTIONS",
    "references.style": "RENDER_REFERENCES",
    "manuscript_structure.block_order": "REBUILD_MANUSCRIPT_STRUCTURE",
    "title_page.mode": "TITLE_PAGE_RESTRUCTURE",
    "figures.legend_location": "COLLECT_FIGURE_LEGENDS",
    "figures.separate_files": "EXTRACT_FIGURES_TO_SEPARATE_FILES",
    "tables.placement": "RELOCATE_TABLES",
    "document.columns": "SET_COLUMNS",
    "document.page_numbering": "SET_PAGE_NUMBERING",
    "typography.line_spacing": "SET_LINE_SPACING",
    "typography.alignment": "SET_ALIGNMENT",
    "supplement.packaging": "PACKAGE_SUPPLEMENT",
}


@dataclass(frozen=True, slots=True)
class ResolvedFormatField:
    rule_id: str
    value: Any
    status: str
    classification: str
    provenance: tuple[dict[str, str], ...]
    submission_stage: str
    article_type: str
    source: str | None
    retrieved_at: str | None
    profile_id: str
    operation: str | None


@dataclass(frozen=True, slots=True)
class ResolvedDocumentFormat:
    journal: str
    article_type: str
    submission_stage: str
    profile_version: str
    fields: tuple[ResolvedFormatField, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def resolve_document_format(
    registry: ProfileRegistry,
    resolved: ResolvedJournalProfile,
    *,
    journal: str,
    article_type: str,
    submission_stage: str,
) -> ResolvedDocumentFormat:
    if submission_stage not in STAGES:
        raise ValueError("submission stage must be explicit and valid")
    layers = sorted(
        (registry.get(pin.profile_id, pin.profile_version) for pin in resolved.pinned_profiles),
        key=lambda profile: profile.precedence,
    )
    selected: dict[str, ResolvedFormatField] = {}
    conflicts = {conflict.rule_id for conflict in resolved.conflicts}
    effective_rules = {rule.rule_id: rule for rule in resolved.effective_rules}
    for profile in layers:
        sources = {item.source_id: item for item in profile.sources}
        evidence = {item.evidence_id: item for item in profile.evidence}
        seen: set[tuple[str, tuple[str, ...]]] = set()
        for target in profile.transformation_targets:
            stages = tuple(target.get("submission_stages", STAGES))
            key = (str(target["rule_id"]), stages)
            if key in seen:
                raise ValueError("duplicate transformation target at equal precedence")
            seen.add(key)
            if submission_stage not in stages:
                continue
            rule_id = str(target["rule_id"])
            status = str(target["status"])
            if rule_id in effective_rules and effective_rules[rule_id].status != "VERIFIED":
                status = effective_rules[rule_id].status
            refs = tuple(target["provenance"])
            valid = bool(refs) and all(
                ref["source_id"] in sources
                and ref["evidence_id"] in evidence
                and evidence[ref["evidence_id"]].source_id == ref["source_id"]
                and sources[ref["source_id"]].verification_status == "VERIFIED"
                and sources[ref["source_id"]].source_type in OFFICIAL_SOURCE_TYPES
                and evidence[ref["evidence_id"]].evidence_hash
                == evidence_hash(evidence[ref["evidence_id"]].evidence_text)
                for ref in refs
            )
            if rule_id in conflicts:
                status = "CONFLICTED"
            elif is_stale(profile):
                status = "STALE"
            elif status == "VERIFIED" and not valid:
                status = "UNKNOWN"
            operation = EXECUTORS.get(rule_id)
            classification = (
                ("VERIFIED_EXECUTABLE" if operation else "VERIFIED_NONEXECUTABLE")
                if status == "VERIFIED"
                else status
            )
            previous = selected.get(rule_id)
            if (
                previous
                and previous.value != target["target_state"]
                and not any(
                    trace.rule_id == rule_id and trace.classification == "VALID_OVERRIDE"
                    for trace in resolved.resolution_trace
                )
            ):
                # Journal/article overrides remain explicit in the resolved target provenance.
                status = classification = "CONFLICTED"
            selected[rule_id] = ResolvedFormatField(
                rule_id,
                target["target_state"],
                status,
                classification,
                refs,
                submission_stage,
                article_type,
                target.get("source"),
                target.get("retrieved_at"),
                profile.profile_id,
                operation,
            )
    return ResolvedDocumentFormat(
        journal,
        article_type,
        submission_stage,
        layers[-1].profile_version,
        tuple(selected[key] for key in sorted(selected)),
    )
