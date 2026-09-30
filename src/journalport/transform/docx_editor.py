"""Surgical, local-only DOCX edits for explicitly authorized M10 operations."""

from __future__ import annotations

import copy
import os
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from journalport.manuscript.model import CanonicalManuscript, Section

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W = f"{{{W_NS}}}"
ET.register_namespace("w", W_NS)

ADMIN_HEADINGS = {
    "author_contributions": "Author Contributions",
    "competing_interests": "Competing Interests",
    "data_availability": "Data Availability",
    "code_availability": "Code Availability",
}


class DocxEditBlocked(ValueError):
    """The requested edit cannot be located unambiguously."""


def _paragraph(
    text: str, paragraph_properties: ET.Element | None = None, *, bold: bool = False
) -> ET.Element:
    node = ET.Element(W + "p")
    if paragraph_properties is not None:
        node.append(copy.deepcopy(paragraph_properties))
    run = ET.SubElement(node, W + "r")
    if bold:
        run_properties = ET.SubElement(run, W + "rPr")
        ET.SubElement(run_properties, W + "b")
    text_node = ET.SubElement(run, W + "t")
    if text[:1].isspace() or text[-1:].isspace():
        text_node.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    text_node.text = text
    return node


def _replace_paragraph_text(paragraph: ET.Element, text: str) -> None:
    properties = paragraph.find(W + "pPr")
    for child in list(paragraph):
        if child is not properties:
            paragraph.remove(child)
    run = ET.SubElement(paragraph, W + "r")
    text_node = ET.SubElement(run, W + "t")
    text_node.text = text


def _replace_inline_abstract(paragraph: ET.Element, text: str) -> None:
    properties = paragraph.find(W + "pPr")
    for child in list(paragraph):
        if child is not properties:
            paragraph.remove(child)
    heading_run = ET.SubElement(paragraph, W + "r")
    run_properties = ET.SubElement(heading_run, W + "rPr")
    ET.SubElement(run_properties, W + "b")
    heading = ET.SubElement(heading_run, W + "t")
    heading.text = "Abstract"
    body_run = ET.SubElement(paragraph, W + "r")
    body = ET.SubElement(body_run, W + "t")
    body.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    body.text = " " + text


def _section_indices(section: Section) -> tuple[int, tuple[int, ...]]:
    heading = section.source_locator.index
    paragraphs = tuple(
        item.source_locator.index
        for item in section.paragraphs
        if item.source_locator.index is not None
    )
    if heading is None:
        raise DocxEditBlocked("target section has no exact DOCX locator")
    return heading, paragraphs


def edit_docx(
    source: Path,
    destination: Path,
    manuscript: CanonicalManuscript,
    operations: tuple[tuple[str, str, str], ...],
) -> None:
    """Apply `(operation, target_key, approved_text)` edits and atomically publish."""
    if source.suffix.lower() != ".docx":
        raise DocxEditBlocked("semantic transformation requires a DOCX source")
    with zipfile.ZipFile(source) as archive:
        document = ET.fromstring(archive.read("word/document.xml"))
        body = document.find(W + "body")
        if body is None:
            raise DocxEditBlocked("DOCX body is missing")
        elements = list(body)
        for operation, target_key, approved_text in operations:
            if operation == "REPLACE_ABSTRACT":
                if len(manuscript.abstract) != 1:
                    raise DocxEditBlocked("abstract target is missing or ambiguous")
                heading_index, paragraph_indices = _section_indices(manuscript.abstract[0])
                if not paragraph_indices:
                    raise DocxEditBlocked("abstract body target is missing")
                first_body = paragraph_indices[0]
                if first_body == heading_index:
                    _replace_inline_abstract(elements[heading_index], approved_text)
                else:
                    _replace_paragraph_text(elements[first_body], approved_text)
                    for index in sorted(paragraph_indices[1:], reverse=True):
                        body.remove(elements[index])
                        elements.pop(index)
            elif operation == "INSERT_REQUIRED_SECTION":
                heading_text = ADMIN_HEADINGS.get(target_key)
                if heading_text is None:
                    raise DocxEditBlocked("administrative section target is unsupported")
                if manuscript.statements.get(target_key):
                    raise DocxEditBlocked("administrative section already exists")
                references = [
                    item
                    for item in manuscript.main_body
                    if item.title.strip().casefold() in {"references", "bibliography"}
                    and item.source_locator.index is not None
                ]
                if len(references) != 1:
                    raise DocxEditBlocked("administrative section insertion point is ambiguous")
                original_reference_index = references[0].source_locator.index
                assert original_reference_index is not None
                reference = elements[original_reference_index]
                reference_index = list(body).index(reference)
                heading_properties = reference.find(W + "pPr")
                heading_node = _paragraph(heading_text, heading_properties, bold=True)
                text_node = _paragraph(approved_text)
                body.insert(reference_index, heading_node)
                body.insert(reference_index + 1, text_node)
            elif operation == "NORMALIZE_SECTION_HEADING":
                heading_text = ADMIN_HEADINGS.get(target_key)
                if heading_text is None:
                    raise DocxEditBlocked("administrative heading target is unsupported")
                aliases = {
                    "author_contributions": {
                        "author contributions",
                        "author contribution statement",
                    },
                    "competing_interests": {
                        "competing interests",
                        "conflict of interest",
                        "conflicts of interest",
                    },
                    "data_availability": {"data availability", "availability of data"},
                    "code_availability": {"code availability", "availability of code"},
                }[target_key]
                matches = [
                    section
                    for section in manuscript.main_body
                    if section.title.strip().casefold() in aliases
                    and section.source_locator.index is not None
                ]
                if len(matches) != 1:
                    raise DocxEditBlocked("administrative heading target is missing or ambiguous")
                admin_heading_index = matches[0].source_locator.index
                assert admin_heading_index is not None
                _replace_paragraph_text(elements[admin_heading_index], heading_text)
            else:
                raise DocxEditBlocked("semantic operation is unsupported")

        document_bytes = ET.tostring(document, encoding="utf-8", xml_declaration=True)
        destination.parent.mkdir(parents=True, exist_ok=True)
        handle, temporary_name = tempfile.mkstemp(
            prefix=".journalport-", suffix=".tmp.docx", dir=destination.parent
        )
        os.close(handle)
        temporary = Path(temporary_name)
        try:
            os.chmod(temporary, 0o600)
            with zipfile.ZipFile(temporary, "w") as output:
                for info in archive.infolist():
                    payload = (
                        document_bytes
                        if info.filename == "word/document.xml"
                        else archive.read(info.filename)
                    )
                    output.writestr(info, payload)
            os.replace(temporary, destination)
            os.chmod(destination, 0o600)
        finally:
            temporary.unlink(missing_ok=True)
