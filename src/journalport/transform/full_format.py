"""Authoritative full-format plan and local workflow built on the M10/M12 contracts."""

from __future__ import annotations

import copy
import json
import shutil
import tempfile
from dataclasses import asdict, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from journalport.agents.transfer import TransferSession, save_session
from journalport.compliance.engine import audit_manuscript
from journalport.manuscript.parser_docx import parse_docx
from journalport.package.format_adapter import build_format_package, verify_format_package
from journalport.profiles.document_format import ResolvedDocumentFormat, resolve_document_format
from journalport.profiles.loader import ProfileRegistry
from journalport.profiles.models import ResolvedJournalProfile
from journalport.verify.assets import figure_technical_metadata
from journalport.verify.render import LibreOfficeRenderBackend

from .closure import closure_status, formatting_coverage
from .format_engine import (
    apply_format_transformations,
    verify_format_transformations,
    write_format_reports,
)
from .format_models import FormatOperation, FormatTransformationPlan, TransferMatrixRow
from .format_planner import _operation_id
from .front_matter import identify_front_matter, restructure_inline
from .full_docx import ensure_page_numbers, observe_rule, read_document
from .hashing import canonical_hash, file_hash
from .layout import apply_alignment, apply_columns, apply_line_spacing
from .references import inspect_linkage, reference_nodes, render_reference_nodes
from .structure import (
    W,
    collect_legends,
    conditional_blocks,
    detect_blocks,
    figure_legends,
    order_conditional_sections,
    rebuild_structure,
    relocate_tables,
    semantic_roles,
    text,
)
from .supplements import package_supplements, supplement_inventory

PRIORITY = {
    "ORDER_CONDITIONAL_SECTIONS": 3,
    "RENDER_REFERENCES": 9,
    "TITLE_PAGE_RESTRUCTURE": 0,
    "COLLECT_FIGURE_LEGENDS": 1,
    "RELOCATE_TABLES": 2,
    "REBUILD_MANUSCRIPT_STRUCTURE": 3,
    "SET_COLUMNS": 4,
    "SET_LINE_SPACING": 5,
    "SET_ALIGNMENT": 6,
    "SET_PAGE_NUMBERING": 7,
    "EXTRACT_FIGURES_TO_SEPARATE_FILES": 8,
}


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def plan_full_format(
    source: Path,
    target: ResolvedDocumentFormat,
    supplements: tuple[Path, ...] = (),
    *,
    conditional_applicability: dict[str, bool] | None = None,
) -> dict[str, Any]:
    if source.suffix.lower() != ".docx":
        raise ValueError("full-format execution supports DOCX only")
    parts, _, body = read_document(source)
    manuscript = parse_docx(source)
    inventory = supplement_inventory(supplements)
    blocks = detect_blocks(body)
    legends = figure_legends(body)
    references = [
        text(node)
        for block in blocks
        if block.label == "References"
        for node in list(body)[block.start + 1 : block.end]
        if text(node)
    ]
    linkage = inspect_linkage(body, references)
    unsafe = any(list(body.iter(W + tag)) for tag in ("ins", "del", "altChunk", "sdt"))
    operations: list[FormatOperation] = []
    rows: list[TransferMatrixRow] = []
    requirements: list[dict[str, str]] = []
    simulated = copy.deepcopy(body)
    simulated_parts = dict(parts)
    facts = dict(conditional_applicability or {})
    valid_conditions = {
        field.rule_id for field in target.fields if field.operation == "ORDER_CONDITIONAL_SECTIONS"
    }
    if set(facts) - valid_conditions or any(type(value) is not bool for value in facts.values()):
        raise ValueError("unknown_or_invalid_conditional_applicability")
    for field in sorted(target.fields, key=lambda item: PRIORITY.get(str(item.operation), 20)):
        if field.operation == "REBUILD_MANUSCRIPT_STRUCTURE" and isinstance(field.value, list):
            # Compose only explicit, verified, author-confirmed ordering constraints.
            for constraint in target.fields:
                if (
                    constraint.operation != "ORDER_CONDITIONAL_SECTIONS"
                    or constraint.status != "VERIFIED"
                    or facts.get(constraint.rule_id) is not True
                ):
                    continue
                try:
                    selected = conditional_blocks(simulated, constraint.value)
                except ValueError:
                    continue
                labels = [block.label for block in selected]
                anchors = [label for label in labels if label in field.value]
                if len(anchors) != 1 or labels[-1] != anchors[0]:
                    continue
                anchor = field.value.index(anchors[0])
                expanded = field.value[:anchor] + labels[:-1] + field.value[anchor:]
                field = replace(
                    field, value=expanded, provenance=field.provenance + constraint.provenance
                )
        reason = ""
        status = "PLANNED"
        if field.rule_id.startswith("statements.") and field.status == "VERIFIED":
            statement_key = field.rule_id.split(".")[1]
            if manuscript.statements.get(statement_key):
                status = "SATISFIED"
            else:
                reason, status = "author_input_required_statement", "BLOCKED"
        elif field.rule_id == "front_matter.identity" and field.status == "VERIFIED":
            try:
                identify_front_matter(body)
                status = "SATISFIED"
            except ValueError as exc:
                reason, status = str(exc), "BLOCKED"
        elif field.rule_id == "references.citation_system" and field.status == "VERIFIED":
            if linkage["linkage_confidence"] == "HIGH" and not linkage["live_fields"]:
                status = "SATISFIED"
            else:
                reason, status = "citation_linkage_requires_manual_review", "UNSUPPORTED"
        elif field.classification != "VERIFIED_EXECUTABLE":
            reason = "profile_uncertain" if field.status != "VERIFIED" else "executor_not_supported"
            status = "BLOCKED" if field.status != "VERIFIED" else "UNSUPPORTED"
        elif unsafe:
            reason, status = "unsupported_document_objects", "BLOCKED"
        elif field.operation == "PACKAGE_SUPPLEMENT":
            if manuscript.supplementary_materials and not inventory:
                reason, status = "explicit_supplement_inventory_required", "UNSUPPORTED"
            else:
                status = "SATISFIED"
        elif field.rule_id == "title_page.mode":
            try:
                identify_front_matter(body)
                if observe_rule(source, field.rule_id, field.value):
                    status = "SATISFIED"
                else:
                    restructure_inline(simulated)
            except ValueError as exc:
                reason, status = str(exc), "BLOCKED"
        elif field.operation == "ORDER_CONDITIONAL_SECTIONS":
            if facts.get(field.rule_id) is not True:
                reason, status = "author_input_required_conditional_applicability", "BLOCKED"
            else:
                try:
                    selected = conditional_blocks(simulated, field.value)
                    if [block.start for block in selected] == sorted(
                        block.start for block in selected
                    ):
                        status = "SATISFIED"
                    else:
                        order_conditional_sections(simulated, field.value)
                except ValueError as exc:
                    reason, status = str(exc), "BLOCKED"
        elif field.operation != "EXTRACT_FIGURES_TO_SEPARATE_FILES" and observe_rule(
            source, field.rule_id, field.value
        ):
            status = "SATISFIED"
        else:
            try:
                if field.operation == "COLLECT_FIGURE_LEGENDS":
                    collect_legends(simulated)
                    if not legends and manuscript.figures:
                        raise ValueError("missing_reliable_figure_legends")
                elif field.operation == "RELOCATE_TABLES":
                    relocate_tables(simulated)
                elif field.operation == "REBUILD_MANUSCRIPT_STRUCTURE":
                    rebuild_structure(simulated, field.value)
                elif field.operation == "SET_COLUMNS":
                    apply_columns(simulated, field.value)
                elif field.operation == "SET_LINE_SPACING":
                    apply_line_spacing(simulated, field.value)
                elif field.operation == "SET_ALIGNMENT":
                    apply_alignment(simulated, field.value)
                elif field.operation == "SET_PAGE_NUMBERING":
                    ensure_page_numbers(simulated_parts, simulated)
                elif field.operation == "RENDER_REFERENCES":
                    if any(op.operation == "ORDER_CONDITIONAL_SECTIONS" for op in operations):
                        raise ValueError("conditional_order_requires_reference_body_unchanged")
                    if not isinstance(field.value, dict):
                        raise ValueError("verified_reference_presentation_attributes_required")
                    render_reference_nodes(simulated, field.value)
            except ValueError as exc:
                reason, status = str(exc), "BLOCKED"
        if status == "PLANNED":
            operation_id = _operation_id(field.rule_id, str(field.operation), field.value)
            dependency = (operations[-1].operation_id,) if operations else ()
            operations.append(
                FormatOperation(
                    operation_id,
                    field.rule_id,
                    str(field.operation),
                    field.rule_id,
                    {"target": field.value, "condition_confirmed": True}
                    if field.operation == "ORDER_CONDITIONAL_SECTIONS"
                    else {"target": field.value},
                    field.provenance,
                    "CONTENT_PRESERVING_AUTOMATIC",
                    "SUPPORTED",
                    "NOT_REQUIRED",
                    "HIGH",
                    "VERIFIED",
                    ("source_hash_matches", "target_rule_verified", "high_confidence_blocks"),
                    {"target": field.value, "scientific_content_preserved": True},
                    dependency,
                )
            )
        if reason:
            requirements.append(
                {
                    "rule_id": field.rule_id,
                    "reason": reason,
                    "classification": "AUTHOR_INPUT_REQUIRED"
                    if "author_input" in reason
                    else "PROFILE_UNCERTAIN"
                    if field.status != "VERIFIED"
                    else "MANUAL_REVIEW_REQUIRED",
                }
            )
        rows.append(
            TransferMatrixRow(
                field.rule_id,
                "OBSERVED_LOCALLY",
                field.value,
                "OBSERVED_LOCALLY",
                "KEEP" if status == "SATISFIED" else "MODIFY" if status == "PLANNED" else "MANUAL",
                str(field.operation or "UNSUPPORTED"),
                "SUPPORTED" if status in {"SATISFIED", "PLANNED"} else "UNSUPPORTED",
                "CONTENT_PRESERVING_AUTOMATIC"
                if status in {"SATISFIED", "PLANNED"}
                else "PROFILE_UNCERTAIN"
                if field.status != "VERIFIED"
                else "MANUAL_REVIEW_REQUIRED",
                "NOT_REQUIRED" if status in {"SATISFIED", "PLANNED"} else "MANUAL_REVIEW_REQUIRED",
                status,
                field.status,
                "HIGH" if field.status == "VERIFIED" else "UNKNOWN",
                field.provenance,
            )
        )
    if len([legend for legend in legends if legend.confidence == "HIGH"]) < len(manuscript.figures):
        requirements.append(
            {
                "rule_id": "figures.caption_mapping",
                "reason": "missing_or_uncertain_captions",
                "classification": "MANUAL_REVIEW_REQUIRED",
            }
        )
    m12 = FormatTransformationPlan(
        "1.0.0",
        "TARGET_ONLY",
        None,
        target.journal,
        target.profile_version,
        file_hash(source),
        tuple(operations),
        tuple(rows),
        tuple(item.operation_id for item in operations),
        target.submission_stage,
    )
    result = {
        "schema_version": "1.0.0",
        "source_hash": file_hash(source),
        "conditional_applicability": facts,
        "target_journal": target.journal,
        "article_type": target.article_type,
        "submission_stage": target.submission_stage,
        "profile_version": target.profile_version,
        "document_target": target.to_dict(),
        "m12_plan": m12.to_dict(),
        "structural_operations": [
            item.operation for item in operations if PRIORITY[item.operation] <= 3
        ],
        "style_operations": [
            item.operation
            for item in operations
            if 4 <= PRIORITY[item.operation] <= 7 or PRIORITY[item.operation] == 9
        ],
        "artifact_operations": [
            item.operation for item in operations if PRIORITY[item.operation] == 8
        ],
        "content_proposals": [],
        "supplement_inventory": [asdict(item) for item in inventory],
        "manual_requirements": requirements,
        "unsupported_targets": [row.rule_id for row in rows if row.status == "UNSUPPORTED"],
        "profile_uncertainties": [row.rule_id for row in rows if row.profile_status != "VERIFIED"],
        "block_confidence": [
            {"role": block.role, "confidence": block.confidence} for block in blocks
        ],
        "semantic_roles": {str(index): role for index, role in semantic_roles(body).items()},
        "citation_linkage": {
            "citation_count": len(linkage["citations"]),
            "linkage_confidence": linkage["linkage_confidence"],
            "reference_parse_confidence": linkage["reference_parse_confidence"],
            "live_fields": linkage["live_fields"],
        },
    }
    result["plan_hash"] = canonical_hash(json.dumps(result, sort_keys=True))
    return result


def m12_from_full_plan(value: dict[str, Any]) -> FormatTransformationPlan:
    m12 = value["m12_plan"]
    return FormatTransformationPlan(
        m12["schema_version"],
        m12["source_mode"],
        m12["source_journal"],
        m12["target_journal"],
        m12["profile_version"],
        m12["source_hash"],
        tuple(
            FormatOperation(
                **(
                    item
                    | {
                        "evidence": tuple(item["evidence"]),
                        "preconditions": tuple(item["preconditions"]),
                        "depends_on": tuple(item["depends_on"]),
                        "conflicts_with": tuple(item["conflicts_with"]),
                    }
                )
            )
            for item in m12["operations"]
        ),
        tuple(
            TransferMatrixRow(**(item | {"evidence": tuple(item["evidence"])}))
            for item in m12["transfer_matrix"]
        ),
        tuple(m12["execution_order"]),
        m12["submission_stage"],
    )


def run_full_format(
    source: Path,
    output: Path,
    registry: ProfileRegistry,
    profile: ResolvedJournalProfile,
    *,
    journal: str,
    article_type: str,
    stage: str,
    plan_only: bool = False,
    approved_plan: Path | None = None,
    render_executable: str | None = None,
    supplements: tuple[Path, ...] = (),
    conditional_applicability: dict[str, bool] | None = None,
) -> dict[str, Any]:
    target = resolve_document_format(
        registry, profile, journal=journal, article_type=article_type, submission_stage=stage
    )
    authoritative = plan_full_format(
        source, target, supplements, conditional_applicability=conditional_applicability
    )
    if approved_plan is not None:
        previous = json.loads(approved_plan.read_text(encoding="utf-8"))
        if previous != authoritative:
            raise ValueError("plan/source/profile binding changed; regenerate and review the plan")
    if output.exists() and any(output.iterdir()):
        raise ValueError("output must be a fresh directory")
    metadata = output / "metadata"
    session = TransferSession(
        "1.0.0",
        "format-session:" + authoritative["plan_hash"].split(":")[-1][:24],
        datetime.now(UTC).isoformat(),
        str(source.resolve()),
        file_hash(source),
        None,
        journal,
        article_type,
        "CODEX_HOSTED",
        target.profile_version,
        disclosure_ledger_path=str(metadata / "disclosure_ledger.json"),
    )
    save_session(session, metadata / "session.json")
    write_json(metadata / "full_format_plan.json", authoritative)
    write_json(
        metadata / "transfer_matrix.json", {"rows": authoritative["m12_plan"]["transfer_matrix"]}
    )
    compliance = audit_manuscript(parse_docx(source), profile)
    # Keep findings in local metadata; no manuscript excerpts are copied to public audit documentation.
    write_json(
        metadata / "compliance_summary.json",
        {
            "finding_count": len(compliance.findings),
            "findings": [{"rule_id": item.rule_id} for item in compliance.findings],
        },
    )
    write_json(
        metadata / "disclosure_ledger.json",
        {
            "privacy_mode": "CODEX_HOSTED",
            "model_processed_manuscript_objects": [],
            "full_text_exposed": False,
            "local_processing": ["parse", "audit", "plan", "apply", "verify", "render"],
            "source_hash": file_hash(source),
        },
    )
    session = replace(
        session.transition("AUDITED"),
        compliance_report_path=str(metadata / "compliance_summary.json"),
    )
    session = replace(
        session.transition("PLAN_READY"),
        transformation_plan_path=str(metadata / "full_format_plan.json"),
    )
    save_session(session, metadata / "session.json")
    if plan_only:
        return {
            "status": "PLAN_READY",
            "planned_operations": authoritative["m12_plan"]["execution_order"],
            "manual_requirements": authoritative["manual_requirements"],
        }
    plan = m12_from_full_plan(authoritative)
    if any(operation.approval_requirement != "NOT_REQUIRED" for operation in plan.operations):
        raise ValueError("author approval must use M10 before full-format execution")
    # This transition is restricted here to deterministic operations requiring no author approval.
    session = session.transition("APPROVED")
    try:
        result = apply_format_transformations(source, plan, output / "manuscript")
    except ValueError:
        save_session(session.transition("BLOCKED"), metadata / "session.json")
        raise
    session = replace(
        session.transition("APPLIED"), execution_result=str(metadata / "execution_result.json")
    )
    save_session(session, metadata / "session.json")
    verification = verify_format_transformations(source, result, plan)
    write_json(metadata / "execution_result.json", asdict(result))
    write_json(metadata / "verification_report.json", verification.to_dict())
    reference_linkages = []
    for path in (source, Path(result.candidate_path)):
        body = read_document(path)[2]
        reference_linkages.append(
            inspect_linkage(body, [text(node) for node in reference_nodes(body)])
        )
    before_refs, after_refs = reference_linkages
    reference_applied = any(
        operation.operation == "RENDER_REFERENCES" for operation in plan.operations
    )
    write_json(
        metadata / "reference_citation_validation_report.json",
        {
            "reference_count": len(after_refs["references"]),
            "citation_count": len(after_refs["citations"]),
            "linkage_confidence": after_refs["linkage_confidence"],
            "reference_transformation_count": len(after_refs["references"])
            if reference_applied
            else 0,
            "reference_identity_roundtrip": [ref.identity() for ref in before_refs["references"]]
            == [ref.identity() for ref in after_refs["references"]],
            "citation_identity_roundtrip": sorted(
                (c.raw_marker, c.linked_reference_ids) for c in before_refs["citations"]
            )
            == sorted((c.raw_marker, c.linked_reference_ids) for c in after_refs["citations"]),
            "live_fields": after_refs["live_fields"],
            "status": "REFERENCE_CITATION_VERIFIED"
            if reference_applied
            and verification.transformation_verification_status == "VERIFIED_CANDIDATE"
            else "MANUAL_REVIEW_REQUIRED",
        },
    )
    write_format_reports(metadata, plan, result, verification)
    if (
        verification.transformation_verification_status != "VERIFIED_CANDIDATE"
        or verification.unexpected_changes
        or verification.failure_reasons
    ):
        save_session(session.transition("BLOCKED"), metadata / "session.json")
        return {"status": "VERIFICATION_FAILED", "failure_reasons": verification.failure_reasons}
    session = replace(
        session.transition("VERIFIED"),
        verification_result=str(metadata / "verification_report.json"),
    )
    save_session(session, metadata / "session.json")
    # Re-run from the original into a private temporary directory to prove repeatability.
    with tempfile.TemporaryDirectory(prefix="journalport-idempotence-") as temporary:
        repeat = apply_format_transformations(source, plan, Path(temporary))
        if repeat.candidate_hash != result.candidate_hash:
            raise ValueError("repeat execution is not byte-idempotent")
    headings = tuple(
        block.label
        for block in detect_blocks(read_document(Path(result.candidate_path))[2])
        if block.label
        in {
            "Abstract",
            "References",
            "Author Contributions",
            "Competing Interests",
            "Figure Legends",
            "Tables",
        }
    )
    rendered = LibreOfficeRenderBackend(render_executable).render(
        Path(result.candidate_path), output / "render", headings
    )
    write_json(metadata / "render_validation_report.json", rendered.to_dict())
    rows = plan.transfer_matrix
    applied_rules = {operation.rule_id for operation in plan.operations}
    satisfied = {row.rule_id for row in rows if row.status == "SATISFIED"}
    independent = formatting_coverage(rows, applied_rules)
    target_status = independent["target_format_status"]
    coverage = {
        "schema_version": "1.0.0",
        "target_rule_count": len(rows),
        "verified_rule_count": sum(row.profile_status == "VERIFIED" for row in rows),
        "executable_rule_count": sum(
            field.classification == "VERIFIED_EXECUTABLE" for field in target.fields
        ),
        "applied_rule_count": len(applied_rules),
        "satisfied_without_change": len(satisfied),
        "manual_rule_count": len(authoritative["manual_requirements"]),
        "unknown_rule_count": sum(row.profile_status != "VERIFIED" for row in rows),
        "unsupported_rule_count": sum(row.status == "UNSUPPORTED" for row in rows),
        "supported_target_coverage": (len(applied_rules) + len(satisfied)) / len(rows)
        if rows
        else 0,
        "target_format_status": target_status,
        "render_status": rendered.status,
        "visual_status": "NOT_PERFORMED",
        "full_format_verified": False,
        "repeat_execution_byte_idempotent": True,
        "formatting_target_count": independent["formatting_target_count"],
        "resolved_formatting_target_count": independent["resolved_formatting_target_count"],
        "formatting_target_coverage": independent["formatting_target_coverage"],
        "overall_profile_coverage": independent["overall_profile_coverage"],
    }
    write_json(metadata / "format_coverage_report.json", coverage)
    from .full_docx import REL, parse_xml

    original_parts = read_document(source)[0]
    relationship_targets = {
        node.get("Id"): node.get("Target")
        for node in parse_xml(original_parts["word/_rels/document.xml.rels"]).findall(
            REL + "Relationship"
        )
    }
    write_json(
        metadata / "figure_artifact_manifest.json",
        {
            "figures": [
                {
                    "source_relationship": artifact.source_relationship,
                    "source_embedded_object": "word/"
                    + str(relationship_targets.get(artifact.source_relationship)),
                    "output_filename": artifact.relative_path,
                    "file_type": Path(artifact.relative_path).suffix.lower().lstrip("."),
                    "sha256": artifact.sha256,
                }
                for artifact in result.artifacts
                if artifact.artifact_type == "FIGURE"
            ]
        },
    )
    write_json(
        metadata / "figure_technical_validation_report.json",
        {
            "figures": [
                {
                    "filename": artifact.relative_path,
                    **figure_technical_metadata(
                        Path(result.candidate_path).parent / artifact.relative_path
                    ),
                }
                for artifact in result.artifacts
                if artifact.artifact_type == "FIGURE"
            ]
        },
    )
    for artifact in result.artifacts:
        if artifact.artifact_type == "FIGURE":
            destination = output / artifact.relative_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(
                Path(result.candidate_path).parent / artifact.relative_path, destination
            )
    inventory = supplement_inventory(supplements)
    supplemental_files = package_supplements(inventory, output / "supplements")
    write_json(metadata / "supplement_manifest.json", {"files": supplemental_files})
    package = build_format_package(result, verification, output / "package")
    packaged_supplements = package_supplements(inventory, output / "package/supplements")
    package["files"].extend(
        {
            "relative_path": "supplements/" + item["filename"],
            "artifact_type": "SUPPLEMENT",
            "sha256": item["sha256"],
        }
        for item in packaged_supplements
    )
    # A content-preserving package with unresolved format/visual rules is not submission-ready.
    package["package_status"] = (
        "PACKAGE_REQUIRES_MANUAL_REVIEW"
        if not coverage["full_format_verified"]
        else package["package_status"]
    )
    package["target_format_status"] = target_status
    package["render_status"] = rendered.status
    package["visual_status"] = "NOT_PERFORMED"
    write_json(output / "package/format_package_manifest.json", package)
    integrity = verify_format_package(output / "package")
    write_json(
        metadata / "package_integrity_report.json",
        integrity | {"package_status": package["package_status"]},
    )
    blockers = independent["blockers"] + [
        {
            "blocker_id": "gate:" + gate,
            "rule_id": gate,
            "category": "validation",
            "current_status": status,
            "closure_critical": True,
            "reason": "independent_validation_required",
            "required_resolution": expected,
            "resolved": status == expected,
        }
        for gate, status, expected in (
            ("render", rendered.status, "RENDER_PASS"),
            ("visual", "NOT_PERFORMED", "VISUAL_PASS"),
            ("preservation", verification.transformation_verification_status, "VERIFIED_CANDIDATE"),
            ("package_integrity", integrity["package_integrity"], "PASS"),
        )
    ]
    unresolved_count = sum(item["closure_critical"] and not item["resolved"] for item in blockers)
    write_json(
        metadata / "nc_closure_blockers.json",
        {
            "schema_version": "1.0.0",
            "items": blockers,
            "unresolved_closure_critical_blockers": unresolved_count,
        },
    )
    closure = closure_status(
        unresolved_closure_critical_blockers=unresolved_count,
        formatting_target_coverage=independent["formatting_target_coverage"],
        content_preservation=verification.transformation_verification_status,
        target_format=target_status,
        render_validation=rendered.status,
        visual_validation="NOT_PERFORMED",
        package_integrity=integrity["package_integrity"],
    )
    write_json(
        metadata / "closure_status.json",
        {
            "closure_status": closure,
            "unresolved_closure_critical_blockers": unresolved_count,
            "formatting_target_coverage": independent["formatting_target_coverage"],
            "content_preservation": verification.transformation_verification_status,
            "target_format": target_status,
            "render_validation": rendered.status,
            "visual_validation": "NOT_PERFORMED",
            "package_integrity": integrity["package_integrity"],
        },
    )
    return {
        "status": verification.transformation_verification_status,
        "source_hash": result.source_hash,
        "candidate_hash": result.candidate_hash,
        "coverage": coverage,
        "package_status": package["package_status"],
        "closure_status": closure,
        "unresolved_closure_critical_blockers": unresolved_count,
    }
