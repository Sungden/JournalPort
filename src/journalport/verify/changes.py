"""Allowed, expected, and observed change modelling."""

from __future__ import annotations

from pathlib import Path

from journalport.manuscript.model import CanonicalManuscript
from journalport.transform.models import TransformationPlan


def allowed_change_set(
    plan: TransformationPlan, applied_action_ids: tuple[str, ...] = ()
) -> tuple[str, ...]:
    # Candidate isolation has always included a nonsemantic output-container filename.
    # A NORMALIZE_OUTPUT_FILENAME action can additionally prescribe its exact value.
    allowed: set[str] = {"filename"}
    for action in plan.actions:
        if action.operation in {"REPLACE_ABSTRACT", "INSERT_REQUIRED_SECTION"} and (
            action.action_id not in applied_action_ids
        ):
            continue
        if action.operation == "NORMALIZE_OUTPUT_FILENAME" and action.classification in {
            "SAFE_AUTOMATIC",
            "CONTENT_PRESERVING_AUTOMATIC",
        }:
            allowed.add("filename")
        elif action.operation == "REPLACE_ABSTRACT":
            allowed.add("abstract")
        elif action.operation == "INSERT_REQUIRED_SECTION":
            target = action.parameters.get("target_key")
            if isinstance(target, str):
                allowed.add(f"statement:{target}")
        elif action.operation == "NORMALIZE_SECTION_HEADING":
            target = action.parameters.get("target_key")
            if isinstance(target, str):
                allowed.add(f"heading:{target}")
        elif action.operation == "SET_MANUSCRIPT_METADATA":
            field = action.parameters.get("metadata_field")
            if field == "article_type":
                allowed.add("submission_metadata:article_type")
    return tuple(sorted(allowed))


def observed_non_scientific_changes(source: Path, candidate: Path) -> tuple[str, ...]:
    changes: list[str] = []
    if source.name != candidate.name:
        changes.append("filename")
    return tuple(changes)


def observed_authorized_changes(
    original: CanonicalManuscript, candidate: CanonicalManuscript
) -> tuple[str, ...]:
    changes: set[str] = set()
    original_abstract = tuple(
        paragraph.text for section in original.abstract for paragraph in section.paragraphs
    )
    candidate_abstract = tuple(
        paragraph.text for section in candidate.abstract for paragraph in section.paragraphs
    )
    if original_abstract != candidate_abstract:
        changes.add("abstract")
    for key in original.statements:
        if original.statements.get(key) != candidate.statements.get(key):
            changes.add(f"statement:{key}")
    aliases = {
        "author_contributions": {"author contributions", "author contribution statement"},
        "competing_interests": {
            "competing interests",
            "conflict of interest",
            "conflicts of interest",
        },
        "data_availability": {"data availability", "availability of data"},
        "code_availability": {"code availability", "availability of code"},
    }
    for key, values in aliases.items():
        before = [item.title for item in original.main_body if item.title.casefold() in values]
        after = [item.title for item in candidate.main_body if item.title.casefold() in values]
        if before != after and before and after:
            changes.add(f"heading:{key}")
    return tuple(sorted(changes))
