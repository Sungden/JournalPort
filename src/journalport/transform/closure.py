"""Explicit formatting coverage and conjunctive closure gates, not acceptance scores."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .format_models import TransferMatrixRow

FORMAT_CRITICAL = frozenset(
    {
        "title_page.mode",
        "front_matter.identity",
        "manuscript_structure.block_order",
        "figures.legend_location",
        "tables.placement",
        "references.style",
        "references.citation_system",
        "document.columns",
        "document.page_numbering",
        "typography.line_spacing",
        "typography.alignment",
        "availability.placement",
    }
)
PACKAGE_CRITICAL = frozenset({"figures.separate_files", "supplement.packaging"})


def target_category(rule_id: str) -> tuple[str, bool]:
    if rule_id in FORMAT_CRITICAL:
        return "closure-critical", True
    if rule_id in PACKAGE_CRITICAL:
        return "package-only", True
    if rule_id in {
        "figures.technical_requirements",
        "figures.caption_format",
        "abstract.requirements",
    }:
        return "article-content-specific", False
    if rule_id.startswith("statements."):
        return "non-formatting", False
    if rule_id in {
        "document.margins",
        "document.page_size",
        "typography.body_font",
        "typography.body_size",
    }:
        # The official Word instructions do not prescribe an exact value for these fields.
        return "informational", False
    # New/unknown targets are critical until explicitly audited; never silently excluded.
    return "closure-critical", True


def formatting_coverage(
    rows: tuple[TransferMatrixRow, ...], applied_rules: set[str]
) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    for row in rows:
        category, critical = target_category(row.rule_id)
        resolved = row.profile_status == "VERIFIED" and (
            row.rule_id in applied_rules or row.status == "SATISFIED"
        )
        state = (
            "NON_FORMATTING"
            if category == "non-formatting"
            else "PROFILE_UNKNOWN"
            if row.profile_status != "VERIFIED"
            else "VERIFIED_EXECUTABLE"
            if row.rule_id in applied_rules
            else "VERIFIED_SATISFIED_WITHOUT_CHANGE"
            if resolved
            else "VERIFIED_MANUAL"
        )
        items.append(
            {
                "blocker_id": "target:" + row.rule_id,
                "rule_id": row.rule_id,
                "category": category,
                "current_status": state,
                "closure_critical": critical,
                "resolved": resolved,
                "reason": "verified_target_observed" if resolved else "target_not_proven",
                "required_resolution": "none"
                if resolved
                else "verified_provenance_and_target_validation",
            }
        )
    formatting = [item for item in items if item["category"] == "closure-critical"]
    resolved_count = sum(item["resolved"] for item in formatting)
    unresolved = [item for item in items if item["closure_critical"] and not item["resolved"]]
    return {
        "formatting_target_count": len(formatting),
        "resolved_formatting_target_count": resolved_count,
        "formatting_target_coverage": 100 * resolved_count / len(formatting) if formatting else 0,
        "overall_profile_coverage": 100 * sum(item["resolved"] for item in items) / len(items)
        if items
        else 0,
        "unresolved_closure_critical_blockers": len(unresolved),
        "target_format_status": "FORMAT_TARGET_PARTIAL" if unresolved else "FORMAT_TARGET_VERIFIED",
        "blockers": items,
    }


def closure_status(
    *,
    unresolved_closure_critical_blockers: int,
    formatting_target_coverage: float,
    content_preservation: str,
    target_format: str,
    render_validation: str,
    visual_validation: str,
    package_integrity: str,
) -> str:
    passed = (
        unresolved_closure_critical_blockers == 0
        and formatting_target_coverage == 100
        and content_preservation == "VERIFIED_CANDIDATE"
        and target_format == "FORMAT_TARGET_VERIFIED"
        and render_validation == "RENDER_PASS"
        and visual_validation in {"VISUAL_PASS", "VISUAL_PASS_WITH_NOTES"}
        and package_integrity == "PASS"
    )
    return "NC_DOCX_CLOSED" if passed else "NC_DOCX_NOT_CLOSED"


def finalize_visual_validation(output: Path, receipt: dict[str, Any]) -> dict[str, Any]:
    """Bind an actual page-review receipt to current artifacts; never synthesize visual approval."""
    from journalport.package.format_adapter import verify_format_package

    from .hashing import file_hash

    metadata = output / "metadata"

    def read(name: str) -> dict[str, Any]:
        value: dict[str, Any] = json.loads((metadata / name).read_text(encoding="utf-8"))
        return value

    rendered = read("render_validation_report.json")
    verified = read("verification_report.json")
    coverage = read("format_coverage_report.json")
    blockers = read("nc_closure_blockers.json")
    candidate = output / "manuscript/manuscript_transformed.docx"
    execution = read("execution_result.json")
    if (
        receipt.get("status") not in {"VISUAL_PASS", "VISUAL_PASS_WITH_NOTES"}
        or receipt.get("candidate_hash") != file_hash(candidate)
        or verified["candidate_hash"] != file_hash(candidate)
        or file_hash(Path(execution["source_path"])) != verified["source_hash"]
        or receipt.get("render_pdf_hash") != rendered["output_pdf_hash"]
        or rendered["input_hash"] != file_hash(candidate)
        or file_hash(output / "render/manuscript_rendered.pdf") != rendered["output_pdf_hash"]
        or verified["transformation_verification_status"] != "VERIFIED_CANDIDATE"
        or verified["unexpected_changes"]
        or verified["failure_reasons"]
    ):
        raise ValueError("visual receipt/artifact/preservation binding invalid")
    pages = receipt.get("reviewed_pages", [])
    if [item["page"] for item in pages] != list(range(1, rendered["page_count"] + 1)) or not pages:
        raise ValueError("every rendered page must be visually reviewed")
    if any(
        file_hash(output / f"visual/page-{item['page']}.png") != item["sha256"] for item in pages
    ):
        raise ValueError("reviewed page image changed")
    required = {
        "front_matter_readable",
        "pagination_readable",
        "headings_readable",
        "figures_rendered",
        "legends_complete_in_order",
        "tables_intact",
        "equation_visible",
        "references_intact",
        "no_unexpected_blank_pages",
        "no_clipped_or_overlapping_elements",
    }
    if not required <= receipt.get("checks", {}).keys() or any(
        receipt["checks"][key] is not True for key in required
    ):
        raise ValueError("visual checklist incomplete or failed")
    integrity = verify_format_package(output / "package")
    for item in blockers["items"]:
        if item["blocker_id"] == "gate:visual":
            item.update(
                current_status=receipt["status"],
                resolved=True,
                reason="hash_bound_page_review_receipt",
                required_resolution="VISUAL_PASS or VISUAL_PASS_WITH_NOTES",
            )
        if item["blocker_id"] == "gate:package_integrity":
            item.update(
                current_status=integrity["package_integrity"],
                resolved=integrity["package_integrity"] == "PASS",
            )
    count = sum(item["closure_critical"] and not item["resolved"] for item in blockers["items"])
    blockers["unresolved_closure_critical_blockers"] = count
    status = closure_status(
        unresolved_closure_critical_blockers=count,
        formatting_target_coverage=coverage["formatting_target_coverage"],
        content_preservation=verified["transformation_verification_status"],
        target_format=coverage["target_format_status"],
        render_validation=rendered["status"],
        visual_validation=receipt["status"],
        package_integrity=integrity["package_integrity"],
    )
    result = {
        "closure_status": status,
        "unresolved_closure_critical_blockers": count,
        "formatting_target_coverage": coverage["formatting_target_coverage"],
        "content_preservation": verified["transformation_verification_status"],
        "target_format": coverage["target_format_status"],
        "render_validation": rendered["status"],
        "visual_validation": receipt["status"],
        "package_integrity": integrity["package_integrity"],
    }
    coverage["visual_status"] = receipt["status"]
    coverage["full_format_verified"] = status == "NC_DOCX_CLOSED"
    for name, value in (
        ("visual_validation_report.json", receipt),
        ("nc_closure_blockers_after_visual.json", blockers),
        ("closure_status_after_visual.json", result),
        ("format_coverage_report_after_visual.json", coverage),
    ):
        (metadata / name).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    return result
