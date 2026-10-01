"""M12 deterministic rule-to-operation mapping and dependency planning."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, cast

from .format_models import (
    FormatOperation,
    FormatRuleTarget,
    FormatSafetyClass,
    FormatTransformationPlan,
    TransferMatrixRow,
)
from .hashing import file_hash

RULE_OPERATIONS: dict[str, tuple[str, str, str]] = {
    "manuscript_structure.admin_section_order": (
        "REORDER_ADMIN_SECTIONS",
        "CONTENT_PRESERVING_AUTOMATIC",
        "MODIFY",
    ),
    "title_page.mode": (
        "TITLE_PAGE_RESTRUCTURE",
        "CONTENT_PRESERVING_AUTOMATIC",
        "SPLIT",
    ),
    "figures.caption_format": (
        "FIGURE_CAPTION_NORMALIZATION",
        "SAFE_FORMAT_AUTOMATIC",
        "MODIFY",
    ),
    "figures.separate_files": (
        "EXTRACT_FIGURES_TO_SEPARATE_FILES",
        "CONTENT_PRESERVING_AUTOMATIC",
        "SPLIT",
    ),
}


class FormatPlanBlocked(ValueError):
    """The rule set cannot produce an unambiguous, acyclic format plan."""


def targets_from_profile_document(value: dict[str, Any]) -> tuple[FormatRuleTarget, ...]:
    """Load optional M12 targets from an already schema-validated profile document."""
    targets: list[FormatRuleTarget] = []
    for item in value.get("transformation_targets", []):
        targets.append(
            FormatRuleTarget(
                item["rule_id"],
                item["target_state"],
                item["status"],
                tuple(item["provenance"]),
                item["confidence"],
                tuple(
                    item.get(
                        "submission_stages",
                        ("INITIAL_SUBMISSION", "REVISION", "FINAL_SUBMISSION", "ACCEPTED"),
                    )
                ),
            )
        )
    return tuple(targets)


def _operation_id(rule_id: str, operation: str, target: Any) -> str:
    raw = json.dumps([rule_id, operation, target], sort_keys=True, separators=(",", ":"))
    return "format:" + hashlib.sha256(raw.encode()).hexdigest()[:24]


def _topological_order(operations: tuple[FormatOperation, ...]) -> tuple[str, ...]:
    by_id = {item.operation_id: item for item in operations}
    if len(by_id) != len(operations):
        raise FormatPlanBlocked("duplicate operation identity")
    incoming = {key: set(value.depends_on) for key, value in by_id.items()}
    if any(dep not in by_id for deps in incoming.values() for dep in deps):
        raise FormatPlanBlocked("unknown transformation dependency")
    order: list[str] = []
    ready = sorted(key for key, deps in incoming.items() if not deps)
    while ready:
        current = ready.pop(0)
        order.append(current)
        for key in sorted(incoming):
            if current in incoming[key]:
                incoming[key].remove(current)
                if not incoming[key] and key not in order and key not in ready:
                    ready.append(key)
                    ready.sort()
    if len(order) != len(operations):
        raise FormatPlanBlocked("transformation dependency cycle")
    return tuple(order)


def plan_format_transformations(
    source: str | Path,
    *,
    current_state: dict[str, Any],
    targets: tuple[FormatRuleTarget, ...],
    target_journal: str,
    profile_version: str,
    source_journal: str | None = None,
    submission_stage: str = "INITIAL_SUBMISSION",
) -> FormatTransformationPlan:
    """Create an explicit transfer matrix and executable plan from verified target rules."""
    rows: list[TransferMatrixRow] = []
    operations: list[FormatOperation] = []
    for target in targets:
        if submission_stage not in target.submission_stages:
            continue
        mapping = RULE_OPERATIONS.get(target.rule_id)
        source_value = current_state.get(target.rule_id)
        if source_value == target.target_state:
            rows.append(
                TransferMatrixRow(
                    target.rule_id,
                    source_value,
                    target.target_state,
                    source_value,
                    "KEEP",
                    "NONE",
                    "NOT_REQUIRED",
                    "SAFE_FORMAT_AUTOMATIC",
                    "NOT_REQUIRED",
                    "SATISFIED",
                    target.profile_status,
                    target.confidence,
                    target.evidence,
                )
            )
            continue
        if target.profile_status != "VERIFIED":
            rows.append(
                TransferMatrixRow(
                    target.rule_id,
                    source_value,
                    target.target_state,
                    source_value,
                    "UNKNOWN",
                    mapping[0] if mapping else "UNSUPPORTED",
                    "UNSUPPORTED",
                    "PROFILE_UNCERTAIN",
                    "MANUAL_REVIEW_REQUIRED",
                    "BLOCKED",
                    target.profile_status,
                    target.confidence,
                    target.evidence,
                )
            )
            continue
        if mapping is None:
            rows.append(
                TransferMatrixRow(
                    target.rule_id,
                    source_value,
                    target.target_state,
                    source_value,
                    "MANUAL",
                    "UNSUPPORTED",
                    "UNSUPPORTED",
                    "FORBIDDEN_AUTOMATIC",
                    "MANUAL_REVIEW_REQUIRED",
                    "UNSUPPORTED",
                    target.profile_status,
                    target.confidence,
                    target.evidence,
                )
            )
            continue
        operation, safety, matrix_action = mapping
        supported_admin_sections = {
            "Acknowledgements",
            "Author Contributions",
            "Competing Interests",
            "Data Availability",
            "Code Availability",
        }
        if operation == "REORDER_ADMIN_SECTIONS" and (
            not isinstance(target.target_state, list)
            or any(item not in supported_admin_sections for item in target.target_state)
        ):
            rows.append(
                TransferMatrixRow(
                    target.rule_id,
                    source_value,
                    target.target_state,
                    source_value,
                    "MANUAL",
                    operation,
                    "UNSUPPORTED",
                    "FORBIDDEN_AUTOMATIC",
                    "MANUAL_REVIEW_REQUIRED",
                    "UNSUPPORTED",
                    target.profile_status,
                    target.confidence,
                    target.evidence,
                )
            )
            continue
        if operation == "TITLE_PAGE_RESTRUCTURE" and target.target_state != "SEPARATE_TITLE_PAGE":
            rows.append(
                TransferMatrixRow(
                    target.rule_id,
                    source_value,
                    target.target_state,
                    source_value,
                    "MANUAL",
                    operation,
                    "UNSUPPORTED",
                    "FORBIDDEN_AUTOMATIC",
                    "MANUAL_REVIEW_REQUIRED",
                    "UNSUPPORTED",
                    target.profile_status,
                    target.confidence,
                    target.evidence,
                )
            )
            continue
        operation_id = _operation_id(target.rule_id, operation, target.target_state)
        depends_on: tuple[str, ...] = ()
        if operation == "EXTRACT_FIGURES_TO_SEPARATE_FILES":
            caption = next(
                (
                    item.operation_id
                    for item in operations
                    if item.operation == "FIGURE_CAPTION_NORMALIZATION"
                ),
                None,
            )
            depends_on = (caption,) if caption else ()
        expected_delta = {
            "rule_id": target.rule_id,
            "source_state": source_value,
            "target_state": target.target_state,
            "scientific_content_preserved": True,
        }
        item = FormatOperation(
            operation_id,
            target.rule_id,
            operation,
            target.rule_id,
            {"target": target.target_state},
            target.evidence,
            cast(FormatSafetyClass, safety),
            "SUPPORTED",
            "NOT_REQUIRED",
            target.confidence,
            target.profile_status,
            ("source_hash_matches", "target_rule_verified", "target_unambiguous"),
            expected_delta,
            depends_on,
            (),
        )
        operations.append(item)
        rows.append(
            TransferMatrixRow(
                target.rule_id,
                source_value,
                target.target_state,
                source_value,
                matrix_action,
                operation,
                "SUPPORTED",
                cast(FormatSafetyClass, safety),
                "NOT_REQUIRED",
                "PLANNED",
                target.profile_status,
                target.confidence,
                target.evidence,
            )
        )
    values = tuple(operations)
    return FormatTransformationPlan(
        "1.0.0",
        "SOURCE_TO_TARGET" if source_journal else "TARGET_ONLY",
        source_journal,
        target_journal,
        profile_version,
        file_hash(Path(source)),
        values,
        tuple(rows),
        _topological_order(values),
        submission_stage,
    )


def write_format_plan(plan: FormatTransformationPlan, output: str | Path) -> None:
    root = Path(output)
    root.mkdir(parents=True, exist_ok=True)
    (root / "transfer_matrix.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "submission_stage": plan.submission_stage,
                "rows": [asdict(row) for row in plan.transfer_matrix],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (root / "format_transformation_plan.json").write_text(
        json.dumps(plan.to_dict(), indent=2) + "\n", encoding="utf-8"
    )
