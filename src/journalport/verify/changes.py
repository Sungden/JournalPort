"""Allowed, expected, and observed change modelling."""

from __future__ import annotations

from pathlib import Path

from journalport.transform.models import TransformationPlan


def allowed_change_set(plan: TransformationPlan) -> tuple[str, ...]:
    # Candidate isolation has always included a nonsemantic output-container filename.
    # A NORMALIZE_OUTPUT_FILENAME action can additionally prescribe its exact value.
    allowed: set[str] = {"filename"}
    for action in plan.actions:
        if action.operation == "NORMALIZE_OUTPUT_FILENAME" and action.classification in {
            "SAFE_AUTOMATIC",
            "CONTENT_PRESERVING_AUTOMATIC",
        }:
            allowed.add("filename")
    return tuple(sorted(allowed))


def observed_non_scientific_changes(source: Path, candidate: Path) -> tuple[str, ...]:
    changes: list[str] = []
    if source.name != candidate.name:
        changes.append("filename")
    return tuple(changes)
