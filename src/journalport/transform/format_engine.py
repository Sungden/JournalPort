"""Surgical M12 DOCX format transformations and operation-aware verification."""

from __future__ import annotations

import copy
import hashlib
import html
import json
import os
import re
import tempfile
import zipfile
from dataclasses import asdict
from pathlib import Path, PurePosixPath
from typing import Any
from xml.etree import ElementTree as ET

from journalport.manuscript.parser_docx import parse_docx

from .format_models import (
    FormatArtifact,
    FormatExecutionResult,
    FormatTransformationPlan,
    FormatVerificationReport,
    OperationVerification,
)
from .hashing import file_hash

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
W = f"{{{W_NS}}}"
A = f"{{{A_NS}}}"
R = f"{{{R_NS}}}"
REL = f"{{{REL_NS}}}"
ET.register_namespace("w", W_NS)
ET.register_namespace("a", A_NS)
ET.register_namespace("r", R_NS)

ADMIN_ALIASES: dict[str, set[str]] = {
    "Author Contributions": {"author contributions", "author contribution statement"},
    "Competing Interests": {
        "competing interests",
        "conflict of interest",
        "conflicts of interest",
    },
    "Data Availability": {"data availability", "availability of data"},
    "Code Availability": {"code availability", "availability of code"},
    "Acknowledgements": {"acknowledgements", "acknowledgments"},
}


class FormatTransformationBlocked(ValueError):
    """A format operation was ambiguous, unsafe, or unsupported."""


def _sha256_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _paragraph_text(paragraph: ET.Element) -> str:
    return "".join(item.text or "" for item in paragraph.iter(W + "t"))


def _replace_text(paragraph: ET.Element, value: str) -> None:
    properties = paragraph.find(W + "pPr")
    for child in list(paragraph):
        if child is not properties:
            paragraph.remove(child)
    run = ET.SubElement(paragraph, W + "r")
    text = ET.SubElement(run, W + "t")
    text.text = value


def _paragraph(value: str, *, style: str | None = None) -> ET.Element:
    paragraph = ET.Element(W + "p")
    if style:
        properties = ET.SubElement(paragraph, W + "pPr")
        node = ET.SubElement(properties, W + "pStyle")
        node.set(W + "val", style)
    run = ET.SubElement(paragraph, W + "r")
    text = ET.SubElement(run, W + "t")
    text.text = value
    return paragraph


def _admin_name(text: str) -> str | None:
    normalized = text.strip().rstrip(":").casefold()
    for canonical, aliases in ADMIN_ALIASES.items():
        if normalized in aliases:
            return canonical
    return None


def _reorder_admin_sections(body: ET.Element, order: list[str]) -> dict[str, Any]:
    if len(order) != len(set(order)) or any(item not in ADMIN_ALIASES for item in order):
        raise FormatTransformationBlocked("administrative target order is invalid")
    children = list(body)
    headings: dict[str, int] = {}
    boundaries: set[int] = set()
    reference_indices: list[int] = []
    for index, node in enumerate(children):
        if node.tag != W + "p":
            continue
        text = _paragraph_text(node)
        admin = _admin_name(text)
        if admin:
            if admin in headings:
                raise FormatTransformationBlocked("duplicate administrative section identity")
            headings[admin] = index
            boundaries.add(index)
        if text.strip().casefold() in {"references", "bibliography"}:
            reference_indices.append(index)
            boundaries.add(index)
    if len(reference_indices) != 1:
        raise FormatTransformationBlocked("ambiguous References location")
    present = [name for name in order if name in headings]
    if not present:
        return {"moved_sections": [], "content_hashes": {}}
    ranges: dict[str, tuple[int, int]] = {}
    sorted_boundaries = sorted(boundaries)
    for name in present:
        start = headings[name]
        end = next((value for value in sorted_boundaries if value > start), len(children))
        ranges[name] = (start, end)
    blocks = {
        name: [copy.deepcopy(node) for node in children[start:end]]
        for name, (start, end) in ranges.items()
    }
    hashes = {
        name: _sha256_bytes(b"".join(ET.tostring(node) for node in blocks[name]))
        for name in present
    }
    remove_indices = {index for start, end in ranges.values() for index in range(start, end)}
    remaining = [node for index, node in enumerate(children) if index not in remove_indices]
    references = [
        index
        for index, node in enumerate(remaining)
        if node.tag == W + "p"
        and _paragraph_text(node).strip().casefold() in {"references", "bibliography"}
    ]
    if len(references) != 1:
        raise FormatTransformationBlocked("References location changed ambiguously")
    insert_at = references[0]
    reordered = [node for name in present for node in blocks[name]]
    final = remaining[:insert_at] + reordered + remaining[insert_at:]
    for node in list(body):
        body.remove(node)
    for node in final:
        body.append(node)
    return {"moved_sections": present, "content_hashes": hashes}


def _caption_target(value: Any) -> tuple[str, str]:
    if not isinstance(value, dict):
        raise FormatTransformationBlocked("caption target must define prefix and separator")
    prefix, separator = value.get("prefix"), value.get("separator")
    if not isinstance(prefix, str) or not isinstance(separator, str):
        raise FormatTransformationBlocked("caption target is incomplete")
    return prefix, separator


def _normalize_figure_captions(body: ET.Element, target: Any) -> dict[str, Any]:
    prefix, separator = _caption_target(target)
    pattern = re.compile(r"^(?:Fig(?:ure)?\.?|FIGURE)\s*(\d+)\s*(?:[.:|]\s*)?(.*)$")
    seen: set[int] = set()
    bodies: dict[str, str] = {}
    changed: list[int] = []
    for node in body:
        if node.tag != W + "p":
            continue
        original = _paragraph_text(node).strip()
        match = pattern.match(original)
        if not match:
            continue
        number = int(match.group(1))
        if number in seen:
            raise FormatTransformationBlocked("duplicate figure number")
        seen.add(number)
        caption_body = match.group(2)
        if not caption_body:
            raise FormatTransformationBlocked("figure caption body is missing")
        bodies[str(number)] = _sha256_bytes(caption_body.encode())
        desired = f"{prefix} {number}{separator}{caption_body}"
        if original != desired:
            _replace_text(node, desired)
            changed.append(number)
    return {"changed_figures": changed, "caption_body_hashes": bodies}


def _write_docx(
    source: Path, destination: Path, archive: zipfile.ZipFile, document_bytes: bytes
) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary_name = tempfile.mkstemp(
        prefix=".journalport-m12-", suffix=".tmp.docx", dir=destination.parent
    )
    os.close(handle)
    temporary = Path(temporary_name)
    try:
        with zipfile.ZipFile(temporary, "w") as output:
            for info in archive.infolist():
                payload = (
                    document_bytes if info.filename == "word/document.xml" else archive.read(info)
                )
                output.writestr(copy.copy(info), payload)
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)


def _copy_docx_exact(source: Path, destination: Path) -> None:
    """Atomically copy a DOCX without rewriting any OPC package member."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary_name = tempfile.mkstemp(
        prefix=".journalport-m12-", suffix=".tmp.docx", dir=destination.parent
    )
    os.close(handle)
    temporary = Path(temporary_name)
    try:
        temporary.write_bytes(source.read_bytes())
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)


def _metadata_lines(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    return [str(value)]


def _write_title_page(
    source: Path, destination: Path, archive: zipfile.ZipFile, metadata: dict[str, Any]
) -> None:
    title = metadata.get("title")
    if not isinstance(title, str) or not title.strip():
        raise FormatTransformationBlocked("title-page title is missing")
    authors = _metadata_lines(metadata.get("authors") or metadata.get("author_order"))
    affiliations = _metadata_lines(metadata.get("affiliations"))
    if not authors:
        raise FormatTransformationBlocked("title-page authors are missing")
    document = ET.Element(W + "document")
    body = ET.SubElement(document, W + "body")
    body.append(_paragraph(title, style="Title"))
    body.append(_paragraph("; ".join(authors)))
    for affiliation in affiliations:
        body.append(_paragraph(affiliation))
    ET.SubElement(body, W + "sectPr")
    _write_docx(
        source, destination, archive, ET.tostring(document, encoding="utf-8", xml_declaration=True)
    )


def _extract_figures(
    archive: zipfile.ZipFile, document: ET.Element, output_root: Path
) -> tuple[FormatArtifact, ...]:
    rels_path = "word/_rels/document.xml.rels"
    if rels_path not in archive.namelist():
        raise FormatTransformationBlocked("DOCX relationships are missing")
    rels = ET.fromstring(archive.read(rels_path))
    targets: dict[str, str] = {}
    for item in rels.findall(REL + "Relationship"):
        rel_id, target = item.get("Id"), item.get("Target")
        if rel_id and target:
            targets[rel_id] = target
    identifiers = [item.get(R + "embed") for item in document.iter(A + "blip")]
    if any(identifier is None for identifier in identifiers):
        raise FormatTransformationBlocked("unresolved figure relationship")
    if len(identifiers) != len(set(identifiers)):
        raise FormatTransformationBlocked("duplicate or ambiguous figure relationship")
    artifacts: list[FormatArtifact] = []
    figures = output_root / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    for number, identifier in enumerate(identifiers, start=1):
        assert identifier is not None
        target = targets.get(identifier)
        if target is None:
            raise FormatTransformationBlocked("malformed DOCX relationship")
        member = str(PurePosixPath("word") / PurePosixPath(target))
        if member not in archive.namelist():
            raise FormatTransformationBlocked("embedded figure asset is missing")
        payload = archive.read(member)
        suffix = PurePosixPath(target).suffix.lower()
        if not suffix or not re.fullmatch(r"\.[a-z0-9]{2,5}", suffix):
            raise FormatTransformationBlocked("figure asset format is unsupported")
        destination = figures / f"Figure_{number}{suffix}"
        destination.write_bytes(payload)
        artifacts.append(
            FormatArtifact(
                str(destination.relative_to(output_root)).replace("\\", "/"),
                "FIGURE",
                _sha256_bytes(payload),
                identifier,
            )
        )
    return tuple(artifacts)


def apply_format_transformations(
    source: str | Path,
    plan: FormatTransformationPlan,
    output_root: str | Path,
) -> FormatExecutionResult:
    """Apply verified, ordered M12 operations without modifying the source DOCX."""
    from .full_docx import FULL_OPERATIONS, execute_full_operations

    if any(
        item.operation in FULL_OPERATIONS
        or item.operation == "TITLE_PAGE_RESTRUCTURE"
        and item.parameters.get("target") == "INLINE_TITLE_PAGE"
        for item in plan.operations
    ):
        return execute_full_operations(Path(source), plan, Path(output_root))
    source_path = Path(source)
    root = Path(output_root)
    if source_path.suffix.lower() != ".docx":
        raise FormatTransformationBlocked("M12 v1 supports DOCX execution only")
    if file_hash(source_path) != plan.source_hash:
        raise FormatTransformationBlocked("source hash changed after planning")
    by_id = {item.operation_id: item for item in plan.operations}
    if set(by_id) != set(plan.execution_order):
        raise FormatTransformationBlocked("execution order does not match operations")
    manuscript = parse_docx(source_path)
    candidate = root / "manuscript_transformed.docx"
    artifacts: list[FormatArtifact] = []
    applied: list[str] = []
    document_changed = False
    with zipfile.ZipFile(source_path) as archive:
        document = ET.fromstring(archive.read("word/document.xml"))
        body = document.find(W + "body")
        if body is None:
            raise FormatTransformationBlocked("DOCX body is missing")
        for operation_id in plan.execution_order:
            item = by_id[operation_id]
            if item.profile_status != "VERIFIED" or item.executor_support != "SUPPORTED":
                raise FormatTransformationBlocked(
                    "uncertain or unsupported operation entered executor"
                )
            target = item.parameters.get("target")
            if item.operation == "REORDER_ADMIN_SECTIONS":
                if not isinstance(target, list) or not all(isinstance(x, str) for x in target):
                    raise FormatTransformationBlocked("administrative order target is invalid")
                _reorder_admin_sections(body, target)
                document_changed = True
            elif item.operation == "FIGURE_CAPTION_NORMALIZATION":
                _normalize_figure_captions(body, target)
                document_changed = True
            elif item.operation == "TITLE_PAGE_RESTRUCTURE":
                if target != "SEPARATE_TITLE_PAGE":
                    raise FormatTransformationBlocked("unsupported title-page mode")
                title_page = root / "title_page.docx"
                _write_title_page(source_path, title_page, archive, manuscript.metadata)
                artifacts.append(
                    FormatArtifact("title_page.docx", "TITLE_PAGE", file_hash(title_page), None)
                )
            elif item.operation == "EXTRACT_FIGURES_TO_SEPARATE_FILES":
                if target is not True:
                    raise FormatTransformationBlocked("figure extraction target is invalid")
                artifacts.extend(_extract_figures(archive, document, root))
            else:
                raise FormatTransformationBlocked(f"unsupported M12 operation: {item.operation}")
            applied.append(operation_id)
        if document_changed:
            _write_docx(
                source_path,
                candidate,
                archive,
                ET.tostring(document, encoding="utf-8", xml_declaration=True),
            )
        else:
            _copy_docx_exact(source_path, candidate)
    parse_docx(candidate)
    if file_hash(source_path) != plan.source_hash:
        raise FormatTransformationBlocked("source changed during format execution")
    return FormatExecutionResult(
        str(source_path.resolve()),
        str(candidate.resolve()),
        plan.source_hash,
        file_hash(candidate),
        tuple(applied),
        tuple(artifacts),
    )


def _zip_hashes(path: Path) -> dict[str, str]:
    with zipfile.ZipFile(path) as archive:
        return {name: _sha256_bytes(archive.read(name)) for name in archive.namelist()}


def _scientific_numbers(path: Path) -> list[str]:
    """Return numeric tokens outside the caption prefixes an operation may rewrite."""
    with zipfile.ZipFile(path) as archive:
        document = ET.fromstring(archive.read("word/document.xml"))
    values: list[str] = []
    caption = re.compile(r"^(?:Fig(?:ure)?\.?|FIGURE)\s*\d+\s*(?:[.:|]\s*)?.*$")
    for paragraph in document.iter(W + "p"):
        text = _paragraph_text(paragraph)
        if caption.match(text.strip()):
            continue
        values.extend(re.findall(r"(?<![\w.])-?\d+(?:\.\d+)?", text))
    return sorted(values)


def _docx_paragraph_texts(path: Path) -> list[str]:
    with zipfile.ZipFile(path) as archive:
        document = ET.fromstring(archive.read("word/document.xml"))
    return [_paragraph_text(item) for item in document.iter(W + "p")]


def verify_format_transformations(
    source: str | Path,
    result: FormatExecutionResult,
    plan: FormatTransformationPlan,
) -> FormatVerificationReport:
    """Verify expected operation deltas and preservation invariants independently."""
    from .full_docx import FULL_OPERATIONS, verify_full_operations

    if any(
        item.operation in FULL_OPERATIONS
        or item.operation == "TITLE_PAGE_RESTRUCTURE"
        and item.parameters.get("target") == "INLINE_TITLE_PAGE"
        for item in plan.operations
    ):
        return verify_full_operations(Path(source), result, plan)
    source_path, candidate = Path(source), Path(result.candidate_path)
    failures: list[str] = []
    unexpected: list[str] = []
    source_doc, candidate_doc = parse_docx(source_path), parse_docx(candidate)
    source_parts, candidate_parts = _zip_hashes(source_path), _zip_hashes(candidate)
    preserved_parts = {
        name: digest == candidate_parts.get(name)
        for name, digest in source_parts.items()
        if name != "word/document.xml"
    }
    preservation = {
        "source_byte_identical": file_hash(source_path) == plan.source_hash,
        "artifact_only_candidate_byte_identical": not all(
            item.operation in {"EXTRACT_FIGURES_TO_SEPARATE_FILES", "TITLE_PAGE_RESTRUCTURE"}
            for item in plan.operations
        )
        or file_hash(source_path) == file_hash(candidate),
        "equations_preserved": [item.value for item in source_doc.equations]
        == [item.value for item in candidate_doc.equations],
        "numbers_preserved": _scientific_numbers(source_path) == _scientific_numbers(candidate),
        "tables_preserved": [
            (item.label, item.legend, item.content_text) for item in source_doc.tables
        ]
        == [(item.label, item.legend, item.content_text) for item in candidate_doc.tables],
        "references_preserved": [item.raw_text for item in source_doc.references]
        == [item.raw_text for item in candidate_doc.references],
        "citations_preserved": [item.reference_ids for item in source_doc.citations]
        == [item.reference_ids for item in candidate_doc.citations],
        "non_document_parts_preserved": all(preserved_parts.values()),
    }
    operations: list[OperationVerification] = []
    for item in plan.operations:
        checks: dict[str, bool] = {"executed": item.operation_id in result.applied_operations}
        if item.operation == "EXTRACT_FIGURES_TO_SEPARATE_FILES":
            checks["figure_count_matches"] = len(
                [artifact for artifact in result.artifacts if artifact.artifact_type == "FIGURE"]
            ) == len(source_doc.figures)
            checks["figure_hashes_match"] = all(
                (Path(result.candidate_path).parent / artifact.relative_path).is_file()
                and file_hash(Path(result.candidate_path).parent / artifact.relative_path)
                == artifact.sha256
                for artifact in result.artifacts
                if artifact.artifact_type == "FIGURE"
            )
        elif item.operation == "TITLE_PAGE_RESTRUCTURE":
            pages = [
                artifact for artifact in result.artifacts if artifact.artifact_type == "TITLE_PAGE"
            ]
            checks["separate_title_page_exists"] = len(pages) == 1
            title_page_path = (
                Path(result.candidate_path).parent / pages[0].relative_path if pages else None
            )
            if title_page_path is None:
                title_page_text: list[str] = []
                checks["title_identity_preserved"] = False
            else:
                title_page = parse_docx(title_page_path)
                title_page_text = _docx_paragraph_texts(title_page_path)
                checks["title_identity_preserved"] = title_page.metadata.get(
                    "title"
                ) == source_doc.metadata.get("title")
            authors = _metadata_lines(
                source_doc.metadata.get("authors") or source_doc.metadata.get("author_order")
            )
            affiliations = _metadata_lines(source_doc.metadata.get("affiliations"))
            checks["author_identity_preserved"] = (
                not authors or "; ".join(authors) in title_page_text
            )
            checks["affiliation_identity_preserved"] = all(
                value in title_page_text for value in affiliations
            )
        elif item.operation == "FIGURE_CAPTION_NORMALIZATION":
            prefix, separator = _caption_target(item.parameters.get("target"))
            checks["caption_prefix_matches"] = all(
                asset.legend.startswith(f"{prefix} {index}{separator}")
                for index, asset in enumerate(candidate_doc.figures, start=1)
                if asset.legend
            )
            checks["figure_identity_preserved"] = [
                asset.content_hash for asset in source_doc.figures
            ] == [asset.content_hash for asset in candidate_doc.figures]
        elif item.operation == "REORDER_ADMIN_SECTIONS":
            target = item.parameters.get("target")
            titles = [section.title for section in candidate_doc.main_body]
            positions = (
                [titles.index(name) for name in target if name in titles]
                if isinstance(target, list)
                else []
            )
            checks["target_order_matches"] = positions == sorted(positions)
            checks["statement_text_preserved"] = source_doc.statements == candidate_doc.statements
        reasons = tuple(name for name, passed in checks.items() if not passed)
        operations.append(
            OperationVerification(
                item.operation_id,
                item.operation,
                "PASS" if not reasons else "FAIL",
                checks,
                reasons,
            )
        )
        failures.extend(f"{item.operation_id}: {reason}" for reason in reasons)
    failures.extend(name for name, passed in preservation.items() if not passed)
    status = "VERIFIED_CANDIDATE" if not failures and not unexpected else "VERIFICATION_FAILED"
    return FormatVerificationReport(
        "1.0.0",
        status,
        file_hash(source_path),
        file_hash(candidate),
        tuple(operations),
        preservation,
        tuple(unexpected),
        tuple(failures),
        tuple(
            row.rule_id for row in plan.transfer_matrix if row.status in {"BLOCKED", "UNSUPPORTED"}
        ),
    )


def write_format_reports(
    root: str | Path,
    plan: FormatTransformationPlan,
    result: FormatExecutionResult,
    verification: FormatVerificationReport,
) -> None:
    output = Path(root)
    output.mkdir(parents=True, exist_ok=True)
    value = {
        "schema_version": "1.0.0",
        "source_journal": plan.source_journal,
        "target_journal": plan.target_journal,
        "profile_version": plan.profile_version,
        "source_hash": result.source_hash,
        "candidate_hash": result.candidate_hash,
        "operations": [asdict(item) for item in verification.operations],
        "artifacts": [asdict(item) for item in result.artifacts],
        "preservation_checks": verification.preservation_checks,
        "remaining_target_requirements": verification.remaining_target_requirements,
        "transformation_verification_status": verification.transformation_verification_status,
        "unexpected_changes": verification.unexpected_changes,
        "failure_reasons": verification.failure_reasons,
    }
    (output / "format_transformation_report.json").write_text(
        json.dumps(value, indent=2) + "\n", encoding="utf-8"
    )
    rows = "".join(
        f"<tr><td>{html.escape(item.operation)}</td><td>{html.escape(item.status)}</td></tr>"
        for item in verification.operations
    )
    (output / "format_transformation_report.html").write_text(
        "<!doctype html><meta charset='utf-8'><title>JournalPort M12 report</title>"
        f"<h1>Format transformation report</h1><p>Status: {html.escape(verification.transformation_verification_status)}</p>"
        f"<p>Source: {html.escape(result.source_hash)}</p><p>Candidate: {html.escape(result.candidate_hash)}</p>"
        f"<table><thead><tr><th>Operation</th><th>Status</th></tr></thead><tbody>{rows}</tbody></table>",
        encoding="utf-8",
    )
