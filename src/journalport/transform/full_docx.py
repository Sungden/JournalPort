"""Namespace-preserving generic M12 structure and layout execution."""

from __future__ import annotations

import copy
import re
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

from lxml import etree

from .format_models import (
    FormatArtifact,
    FormatExecutionResult,
    FormatTransformationPlan,
    FormatVerificationReport,
    OperationVerification,
)
from .front_matter import identify_front_matter, restructure_inline
from .hashing import file_hash
from .layout import apply_alignment, apply_columns, apply_line_spacing, page_footer, property_node
from .references import inspect_linkage, reference_nodes, render_reference_nodes
from .structure import (
    CAPTION,
    TABLE_TITLE,
    A,
    R,
    StructureBlocked,
    W,
    collect_legends,
    conditional_block_hashes,
    conditional_blocks,
    detect_blocks,
    digest,
    order_conditional_sections,
    rebuild_structure,
    relocate_tables,
    text,
)

REL = "{http://schemas.openxmlformats.org/package/2006/relationships}"
CT = "{http://schemas.openxmlformats.org/package/2006/content-types}"
FULL_OPERATIONS = {
    "ORDER_CONDITIONAL_SECTIONS",
    "RENDER_REFERENCES",
    "REBUILD_MANUSCRIPT_STRUCTURE",
    "COLLECT_FIGURE_LEGENDS",
    "RELOCATE_TABLES",
    "SET_COLUMNS",
    "SET_PAGE_NUMBERING",
    "SET_LINE_SPACING",
    "SET_ALIGNMENT",
}


def parse_xml(payload: bytes) -> etree._Element:
    if b"<!DOCTYPE" in payload.upper() or b"<!ENTITY" in payload.upper():
        raise StructureBlocked("DTD/entity declarations are forbidden")
    return etree.fromstring(payload, etree.XMLParser(resolve_entities=False, no_network=True))


def read_document(path: Path) -> tuple[dict[str, bytes], etree._Element, etree._Element]:
    with zipfile.ZipFile(path) as archive:
        if len(archive.namelist()) != len(set(archive.namelist())):
            raise StructureBlocked("duplicate ZIP package members")
        if sum(info.file_size for info in archive.infolist()) > 200_000_000:
            raise StructureBlocked("DOCX exceeds decompressed size limit")
        parts = {name: archive.read(name) for name in archive.namelist()}
    relationships = parse_xml(parts["word/_rels/document.xml.rels"])
    identifiers = [node.get("Id") for node in relationships]
    if None in identifiers or len(identifiers) != len(set(identifiers)):
        raise StructureBlocked("ambiguous DOCX relationship identities")
    document = parse_xml(parts["word/document.xml"])
    body = document.find(W + "body")
    if body is None:
        raise StructureBlocked("document body missing")
    targets = {node.get("Id"): node for node in relationships}
    for blip in body.iter(A + "blip"):
        relation = targets.get(blip.get(R + "embed"))
        if (
            relation is None
            or relation.get("TargetMode") == "External"
            or relation.get("Type") != R[1:-1] + "/image"
        ):
            raise StructureBlocked("invalid or external embedded image relationship")
        member = relation.get("Target", "")
        if member.startswith("/") or ".." in Path(member).parts or "word/" + member not in parts:
            raise StructureBlocked("invalid embedded image target")
    return parts, document, body


def serialize(document: etree._Element) -> bytes:
    return etree.tostring(document, encoding="UTF-8", xml_declaration=True, standalone=True)


def ensure_page_numbers(parts: dict[str, bytes], body: etree._Element) -> set[str]:
    sections = list(body.iter(W + "sectPr"))
    if not sections:
        sections = [etree.SubElement(body, W + "sectPr")]
    relationships = parse_xml(parts["word/_rels/document.xml.rels"])
    content_types = parse_xml(parts["[Content_Types].xml"])
    relation_id = "rIdJournalPortPageFooter"
    member = "word/journalport-page-footer.xml"
    footer_type = R[1:-1] + "/footer"
    existing = next((node for node in relationships if node.get("Id") == relation_id), None)
    if existing is not None and (
        existing.get("Target") != "journalport-page-footer.xml"
        or existing.get("Type") != footer_type
    ):
        raise StructureBlocked("reserved page footer relationship collision")
    for section in sections:
        references = list(section.findall(W + "footerReference"))
        if any(node.get(R + "id") != relation_id for node in references):
            raise StructureBlocked("existing footer requires manual composition")
        if not references:
            reference = etree.Element(W + "footerReference")
            reference.set(W + "type", "default")
            reference.set(R + "id", relation_id)
            section.insert(0, reference)
        for node in (W + "titlePg", W + "pgNumType"):
            if section.find(node) is not None and node == W + "titlePg":
                raise StructureBlocked("first-page footer semantics require manual review")
        property_node(section, "pgNumType").set(W + "fmt", "decimal")
    if existing is None:
        relationship = etree.SubElement(relationships, REL + "Relationship")
        relationship.set("Id", relation_id)
        relationship.set("Type", footer_type)
        relationship.set("Target", "journalport-page-footer.xml")
    if not any(node.get("PartName") == "/" + member for node in content_types):
        override = etree.SubElement(content_types, CT + "Override")
        override.set("PartName", "/" + member)
        override.set(
            "ContentType",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml",
        )
    parts[member] = page_footer()
    parts["word/_rels/document.xml.rels"] = serialize(relationships)
    parts["[Content_Types].xml"] = serialize(content_types)
    return {member, "word/_rels/document.xml.rels", "[Content_Types].xml"}


def execute_full_operations(
    source: Path, plan: FormatTransformationPlan, output: Path
) -> FormatExecutionResult:
    from .format_engine import _copy_docx_exact, _extract_figures

    if file_hash(source) != plan.source_hash:
        raise StructureBlocked("source changed after planning")
    parts, document, body = read_document(source)
    if any(list(body.iter(W + tag)) for tag in ("ins", "del", "altChunk", "sdt")):
        raise StructureBlocked("tracked changes or unsupported block wrappers")
    by_id = {operation.operation_id: operation for operation in plan.operations}
    if len(by_id) != len(plan.operations) or set(by_id) != set(plan.execution_order):
        raise StructureBlocked("execution order does not match plan")
    output.mkdir(parents=True, exist_ok=True)
    candidate = output / "manuscript_transformed.docx"
    artifacts: list[FormatArtifact] = []
    mutated = False
    records = []
    for operation_id in plan.execution_order:
        operation = by_id[operation_id]
        if operation.profile_status != "VERIFIED" or operation.executor_support != "SUPPORTED":
            raise StructureBlocked("unverified operation in executor")
        target = operation.parameters["target"]
        name = operation.operation
        if name == "ORDER_CONDITIONAL_SECTIONS":
            if operation.parameters.get("condition_confirmed") is not True:
                raise StructureBlocked("conditional_applicability_not_confirmed")
            before_hashes = conditional_block_hashes(body, target)
            before_order = [
                block.label
                for block in sorted(conditional_blocks(body, target), key=lambda b: b.start)
            ]
            order_conditional_sections(body, target)
            after_hashes = conditional_block_hashes(body, target)
            if before_hashes != after_hashes:
                raise StructureBlocked("conditional_block_content_changed")
            records.append(
                {
                    "operation_id": operation_id,
                    "before_body_hashes": before_hashes,
                    "after_body_hashes": after_hashes,
                    "before_order": before_order,
                    "after_order": [block.label for block in conditional_blocks(body, target)],
                }
            )
        elif name == "COLLECT_FIGURE_LEGENDS":
            if target != "AFTER_REFERENCES":
                raise StructureBlocked("unsupported legend placement")
            collect_legends(body)
            if "word/styles.xml" in parts:
                styles = parse_xml(parts["word/styles.xml"])
                if not any(node.get(W + "styleId") == "JP_ADMIN_HEADING" for node in styles):
                    style = etree.SubElement(styles, W + "style")
                    style.set(W + "type", "paragraph")
                    style.set(W + "styleId", "JP_ADMIN_HEADING")
                    etree.SubElement(style, W + "name").set(
                        W + "val", "JournalPort administrative heading"
                    )
                    props = etree.SubElement(style, W + "pPr")
                    etree.SubElement(props, W + "outlineLvl").set(W + "val", "0")
                    parts["word/styles.xml"] = serialize(styles)
        elif name == "RELOCATE_TABLES":
            if target != "END_OF_MANUSCRIPT":
                raise StructureBlocked("unsupported table placement")
            relocate_tables(body)
        elif name == "REBUILD_MANUSCRIPT_STRUCTURE":
            rebuild_structure(body, target)
        elif name == "SET_LINE_SPACING":
            apply_line_spacing(body, target)
        elif name == "SET_ALIGNMENT":
            apply_alignment(body, target)
        elif name == "SET_COLUMNS":
            apply_columns(body, target)
        elif name == "SET_PAGE_NUMBERING":
            if target != "ARABIC_FOOTER":
                raise StructureBlocked("unsupported page numbering target")
            ensure_page_numbers(parts, body)
        elif name == "TITLE_PAGE_RESTRUCTURE" and target == "INLINE_TITLE_PAGE":
            restructure_inline(body)
        elif name == "RENDER_REFERENCES":
            render_reference_nodes(body, target)
        elif name == "EXTRACT_FIGURES_TO_SEPARATE_FILES":
            if target is not True:
                raise StructureBlocked("invalid extraction target")
            with zipfile.ZipFile(source) as archive:
                artifacts.extend(
                    _extract_figures(archive, ET.fromstring(parts["word/document.xml"]), output)
                )
            continue
        else:
            raise StructureBlocked("unsupported full-format operation")
        mutated = True
    if mutated:
        parts["word/document.xml"] = serialize(document)
        temporary = output / ".candidate.tmp.docx"
        try:
            with (
                zipfile.ZipFile(source) as original,
                zipfile.ZipFile(temporary, "w") as destination,
            ):
                for info in original.infolist():
                    destination.writestr(copy.copy(info), parts[info.filename])
                for name in sorted(set(parts) - set(original.namelist())):
                    info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
                    info.compress_type = zipfile.ZIP_DEFLATED
                    destination.writestr(info, parts[name])
            temporary.replace(candidate)
        finally:
            temporary.unlink(missing_ok=True)
    else:
        _copy_docx_exact(source, candidate)
    if file_hash(source) != plan.source_hash:
        raise StructureBlocked("source changed during execution")
    return FormatExecutionResult(
        str(source.resolve()),
        str(candidate.resolve()),
        plan.source_hash,
        file_hash(candidate),
        plan.execution_order,
        tuple(artifacts),
        tuple(records),
    )


def fingerprint(path: Path) -> dict[str, Any]:
    parts, document, body = read_document(path)
    refs = [
        text(node)
        for block in detect_blocks(body)
        if block.label == "References"
        for node in list(body)[block.start + 1 : block.end]
        if text(node)
    ]
    linkage = inspect_linkage(body, refs)
    citations = linkage["citations"]
    # Layout properties are the only text-related XML permitted to change.
    run_hashes = Counter(digest(node) for node in body.iter(W + "r"))
    tables = sorted(digest(node) for node in body.iter(W + "tbl"))
    # Ignore paragraph layout inside tables when testing logical cell identity.
    table_contents = []
    for node in body.iter(W + "tbl"):
        clone = copy.deepcopy(node)
        for props in list(clone.iter(W + "pPr")):
            parent = props.getparent()
            if parent is not None:
                parent.remove(props)
        table_contents.append(digest(clone))
    return {
        "parts": parts,
        "run_hashes": run_hashes,
        "equations": sorted(
            digest(node)
            for node in body.iter(
                "{http://schemas.openxmlformats.org/officeDocument/2006/math}oMath"
            )
        ),
        "numbers": sorted(re.findall(r"(?<![\w.])-?\d+(?:\.\d+)?", text(body))),
        "tables": sorted(table_contents),
        "raw_tables": tables,
        "references": refs,
        "reference_identities": [ref.identity() for ref in linkage["references"]],
        "citations": sorted((item.raw_marker, item.linked_reference_ids) for item in citations),
        "media": {
            name: payload for name, payload in parts.items() if name.startswith("word/media/")
        },
        "namespaces": document.nsmap,
        "root_attributes": dict(document.attrib),
        "scientific_section_sequence": [
            block.label for block in detect_blocks(body) if block.role == "ScientificSectionBlock"
        ],
        "scientific_paragraph_sequence": [
            text(node)
            for block in detect_blocks(body)
            if block.role == "ScientificSectionBlock"
            for node in list(body)[block.start : block.end]
            if node.tag == W + "p"
            and not CAPTION.fullmatch(text(node).strip())
            and not TABLE_TITLE.fullmatch(text(node).strip())
        ],
        "administrative": {
            block.label: [text(node) for node in list(body)[block.start : block.end]]
            for block in detect_blocks(body)
            if block.role == "AdministrativeSectionBlock"
        },
        "front": [
            text(node)
            for block in detect_blocks(body)
            if block.role == "FrontMatterBlock"
            for node in list(body)[block.start : block.end]
        ],
    }


def observe_rule(path: Path, rule_id: str, target: Any) -> bool:
    parts, _, body = read_document(path)
    if isinstance(target, dict) and "conditional_order" in target:
        try:
            selected = conditional_blocks(body, target)
        except ValueError:
            return False
        return [block.start for block in selected] == sorted(block.start for block in selected)
    if rule_id == "references.style" and isinstance(target, dict):
        simulated = copy.deepcopy(body)
        try:
            render_reference_nodes(simulated, target)
        except ValueError:
            return False
        return [
            etree.tostring(node, method="c14n", exclusive=True) for node in reference_nodes(body)
        ] == [
            etree.tostring(node, method="c14n", exclusive=True)
            for node in reference_nodes(simulated)
        ]
    if rule_id == "manuscript_structure.block_order":
        labels = [block.label for block in detect_blocks(body) if block.label in target]
        return labels == [label for label in target if label in labels]
    if rule_id == "figures.legend_location":
        blocks = detect_blocks(body)
        indices = {block.label: block.start for block in blocks}
        captions = [
            node for node in body if re.match(r"^(?:Fig(?:ure)?\.?|FIGURE)\s+\d+", text(node))
        ]
        if not captions:
            return True
        legend_block = next((block for block in blocks if block.label == "Figure Legends"), None)
        return (
            legend_block is not None
            and indices.get("References", len(body)) < legend_block.start
            and all(
                legend_block.start < list(body).index(node) < legend_block.end for node in captions
            )
        )
    if rule_id == "tables.placement":
        table_indices = [index for index, node in enumerate(body) if node.tag == W + "tbl"]
        block = next((block for block in detect_blocks(body) if block.label == "Tables"), None)
        return (
            not table_indices
            or block is not None
            and all(block.start < index < block.end for index in table_indices)
        )
    if rule_id == "typography.line_spacing":
        return all(
            (spacing := node.find(W + "pPr/" + W + "spacing")) is not None
            and spacing.get(W + "line") == "480"
            and spacing.get(W + "lineRule") == "auto"
            for node in body.iter(W + "p")
        )
    if rule_id == "typography.alignment":
        return all(
            node.find(W + "pPr/" + W + "jc") is not None
            and node.find(W + "pPr/" + W + "jc").get(W + "val") == "left"  # type: ignore[union-attr]
            for node in body.iter(W + "p")
        )
    if rule_id == "document.columns":
        return bool(list(body.iter(W + "sectPr"))) and all(
            node.find(W + "cols") is not None and node.find(W + "cols").get(W + "num") == "1"  # type: ignore[union-attr]
            for node in body.iter(W + "sectPr")
        )
    if rule_id == "document.page_numbering":
        return parts.get("word/journalport-page-footer.xml") == page_footer()
    if rule_id == "title_page.mode":
        try:
            identity = identify_front_matter(body)
        except ValueError:
            return False
        order = {"title": 0, "authors": 1, "affiliations": 2, "correspondence": 3}
        values = [order[role] for _, role in identity.paragraph_roles]
        return values == sorted(values)
    return False


def verify_full_operations(
    source: Path, result: FormatExecutionResult, plan: FormatTransformationPlan
) -> FormatVerificationReport:
    before, after = fingerprint(source), fingerprint(Path(result.candidate_path))
    added = after["run_hashes"] - before["run_hashes"]
    removed = before["run_hashes"] - after["run_hashes"]
    reference_operations = [
        item for item in plan.operations if item.operation == "RENDER_REFERENCES"
    ]
    reference_render_exact = True
    if reference_operations:
        original_body = read_document(source)[2]
        expected_body = copy.deepcopy(original_body)
        try:
            render_reference_nodes(expected_body, reference_operations[0].parameters["target"])
            actual_nodes = reference_nodes(read_document(Path(result.candidate_path))[2])
            expected_nodes = reference_nodes(expected_body)
            # Paragraph layout is independently verified; reference run content/presentation is exact.
            actual_runs = Counter(
                digest(run) for node in actual_nodes for run in node.iter(W + "r")
            )
            original_runs = Counter(
                digest(run) for node in reference_nodes(original_body) for run in node.iter(W + "r")
            )
            reference_render_exact = [
                [etree.tostring(run, method="c14n", exclusive=True) for run in node.iter(W + "r")]
                for node in actual_nodes
            ] == [
                [etree.tostring(run, method="c14n", exclusive=True) for run in node.iter(W + "r")]
                for node in expected_nodes
            ]
            added = (after["run_hashes"] - actual_runs) - (before["run_hashes"] - original_runs)
            removed = (before["run_hashes"] - original_runs) - (after["run_hashes"] - actual_runs)
        except ValueError:
            reference_render_exact = False
    allowed_heading_texts = {"Figure Legends", "Tables"}
    _, _, body = read_document(Path(result.candidate_path))
    heading_runs = Counter(
        digest(node)
        for paragraph in body
        if text(paragraph) in allowed_heading_texts
        for node in paragraph.iter(W + "r")
    )
    permitted_parts = {"word/document.xml"}
    if any(item.operation == "COLLECT_FIGURE_LEGENDS" for item in plan.operations):
        permitted_parts.add("word/styles.xml")
    if any(item.operation == "SET_PAGE_NUMBERING" for item in plan.operations):
        permitted_parts |= {
            "word/_rels/document.xml.rels",
            "[Content_Types].xml",
            "word/journalport-page-footer.xml",
        }
    preservation = {
        "source_byte_identical": file_hash(source) == plan.source_hash,
        "execution_source_hash_matches": result.source_hash == plan.source_hash,
        "execution_candidate_hash_matches": file_hash(Path(result.candidate_path))
        == result.candidate_hash,
        "original_runs_preserved": not removed and not (added - heading_runs),
        "equations_preserved": before["equations"] == after["equations"],
        "numbers_preserved": before["numbers"] == after["numbers"],
        "tables_preserved": before["tables"] == after["tables"],
        "references_preserved": before["reference_identities"] == after["reference_identities"]
        if reference_operations
        else before["references"] == after["references"],
        "reference_render_exact": reference_render_exact,
        "citations_preserved": before["citations"] == after["citations"],
        "figures_preserved": before["media"] == after["media"],
        "namespace_prefixes_preserved": before["namespaces"] == after["namespaces"],
        "document_root_attributes_preserved": before["root_attributes"] == after["root_attributes"],
        "scientific_section_order_preserved": before["scientific_section_sequence"]
        == after["scientific_section_sequence"],
        "scientific_paragraph_order_preserved": before["scientific_paragraph_sequence"]
        == after["scientific_paragraph_sequence"],
        "administrative_bodies_preserved": before["administrative"] == after["administrative"],
        "title_author_affiliation_contact_preserved": sorted(before["front"])
        == sorted(after["front"]),
        "untouched_parts_preserved": all(
            before["parts"].get(name) == after["parts"].get(name)
            for name in set(before["parts"]) | set(after["parts"])
            if name not in permitted_parts
        ),
    }
    operations = []
    if "word/_rels/document.xml.rels" in permitted_parts:
        prior_relations = parse_xml(before["parts"]["word/_rels/document.xml.rels"])
        new_relations = parse_xml(after["parts"]["word/_rels/document.xml.rels"])
        old_ids = {node.get("Id") for node in prior_relations}
        new_by_id = {node.get("Id"): node for node in new_relations}
        preservation["existing_relationships_preserved"] = all(
            node.get("Id") in new_by_id and digest(node) == digest(new_by_id[node.get("Id")])
            for node in prior_relations
        ) and set(new_by_id) - old_ids <= {"rIdJournalPortPageFooter"}
        prior_types = parse_xml(before["parts"]["[Content_Types].xml"])
        new_types = parse_xml(after["parts"]["[Content_Types].xml"])
        source_types = [digest(node) for node in prior_types]
        preserved_types = [
            digest(node)
            for node in new_types
            if node.get("PartName") != "/word/journalport-page-footer.xml"
        ]
        preservation["existing_content_types_preserved"] = source_types == preserved_types
    if "word/styles.xml" in permitted_parts and "word/styles.xml" in before["parts"]:
        before_styles = parse_xml(before["parts"]["word/styles.xml"])
        after_styles = parse_xml(after["parts"]["word/styles.xml"])
        prior_ids = {node.get(W + "styleId") for node in before_styles}
        prior_children = [digest(node) for node in before_styles]
        remaining_children = [
            digest(node)
            for node in after_styles
            if node.get(W + "styleId") != "JP_ADMIN_HEADING" or "JP_ADMIN_HEADING" in prior_ids
        ]
        preservation["existing_styles_preserved"] = prior_children == remaining_children
    for operation in plan.operations:
        passed = operation.operation_id in result.applied_operations and (
            operation.operation == "EXTRACT_FIGURES_TO_SEPARATE_FILES"
            or observe_rule(
                Path(result.candidate_path), operation.rule_id, operation.parameters["target"]
            )
        )
        checks = {"executed_and_target_observed": passed}
        if operation.operation == "ORDER_CONDITIONAL_SECTIONS":
            original_body = read_document(source)[2]
            try:
                original_hashes = conditional_block_hashes(
                    original_body, operation.parameters["target"]
                )
                final_hashes = conditional_block_hashes(body, operation.parameters["target"])
                checks["section_body_hashes_unchanged"] = original_hashes == final_hashes
                checks["references_body_hash_unchanged"] = original_hashes.get(
                    "References"
                ) == final_hashes.get("References")
                checks["condition_confirmed"] = (
                    operation.parameters.get("condition_confirmed") is True
                )
                if len(plan.operations) == 1:
                    # Independent expected sequence: only the three authorised block slots change.
                    selected = conditional_blocks(original_body, operation.parameters["target"])
                    source_nodes = list(original_body)
                    desired_chunks = iter([source_nodes[b.start : b.end] for b in selected])
                    starts = {b.start: b for b in selected}
                    expected_nodes_in_order = []
                    index = 0
                    while index < len(source_nodes):
                        if index in starts:
                            expected_nodes_in_order.extend(next(desired_chunks))
                            index = starts[index].end
                        else:
                            expected_nodes_in_order.append(source_nodes[index])
                            index += 1
                    checks["only_authorized_block_ordering_changed"] = [
                        digest(n) for n in expected_nodes_in_order
                    ] == [digest(n) for n in body]
            except ValueError:
                checks["section_body_hashes_unchanged"] = False
        if operation.operation == "EXTRACT_FIGURES_TO_SEPARATE_FILES":
            with zipfile.ZipFile(source) as archive:
                relations = parse_xml(archive.read("word/_rels/document.xml.rels"))
                targets = {node.get("Id"): node.get("Target") for node in relations}
                assets = [item for item in result.artifacts if item.artifact_type == "FIGURE"]
                expected = [node.get(R + "embed") for node in body.iter(A + "blip")]
                checks["relationship_count_matches"] = len(assets) == len(expected)
                original_body = read_document(source)[2]
                checks["relationship_identity_matches"] = [
                    asset.source_relationship for asset in assets
                ] == [node.get(R + "embed") for node in original_body.iter(A + "blip")]
                checks["artifact_binary_identity"] = all(
                    item.source_relationship in targets
                    and targets[item.source_relationship] is not None
                    and (Path(result.candidate_path).parent / item.relative_path).read_bytes()
                    == archive.read("word/" + str(targets[item.source_relationship]))
                    and file_hash(Path(result.candidate_path).parent / item.relative_path)
                    == item.sha256
                    for item in assets
                )
        reasons = tuple(key for key, value in checks.items() if not value)
        operations.append(
            OperationVerification(
                operation.operation_id,
                operation.operation,
                "FAIL" if reasons else "PASS",
                checks,
                reasons,
            )
        )
    failures = tuple(key for key, passed in preservation.items() if not passed) + tuple(
        reason for operation in operations for reason in operation.failure_reasons
    )
    return FormatVerificationReport(
        "1.0.0",
        "VERIFICATION_FAILED" if failures else "VERIFIED_CANDIDATE",
        file_hash(source),
        file_hash(Path(result.candidate_path)),
        tuple(operations),
        preservation,
        failures,
        failures,
        tuple(
            row.rule_id for row in plan.transfer_matrix if row.status in {"BLOCKED", "UNSUPPORTED"}
        ),
    )
