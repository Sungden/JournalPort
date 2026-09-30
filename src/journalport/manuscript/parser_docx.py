"""Read-only, fail-closed DOCX parser using direct Open XML inspection."""

from __future__ import annotations

import hashlib
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree as ET

from .ids import StableIdFactory
from .model import (
    Asset,
    CanonicalManuscript,
    Citation,
    Equation,
    Note,
    Reference,
    Section,
    SourceLocator,
    TextBlock,
)
from .unsupported import register_unsupported

NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "m": "http://schemas.openxmlformats.org/officeDocument/2006/math",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "wp": "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "pr": "http://schemas.openxmlformats.org/package/2006/relationships",
    "dc": "http://purl.org/dc/elements/1.1/",
}
W = f"{{{NS['w']}}}"
M = f"{{{NS['m']}}}"
A = f"{{{NS['a']}}}"
R = f"{{{NS['r']}}}"
WP = f"{{{NS['wp']}}}"


class DocxParseError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class DocxResourceLimits:
    max_archive_bytes: int = 100_000_000
    max_zip_members: int = 2_000
    max_uncompressed_total_bytes: int = 500_000_000
    max_member_bytes: int = 100_000_000
    max_xml_bytes: int = 20_000_000
    max_relationships: int = 20_000
    max_xml_depth: int = 256


DEFAULT_LIMITS = DocxResourceLimits()


def _sha256(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _xml(data: bytes, name: str, limits: DocxResourceLimits = DEFAULT_LIMITS) -> ET.Element:
    if len(data) > limits.max_xml_bytes:
        raise DocxParseError(f"XML part exceeds configured size limit: {name}")
    try:
        root = ET.fromstring(data)
    except ET.ParseError as exc:
        raise DocxParseError(f"malformed Open XML part {name}: {exc}") from exc
    stack: list[tuple[ET.Element, int]] = [(root, 1)]
    while stack:
        node, depth = stack.pop()
        if depth > limits.max_xml_depth:
            raise DocxParseError(f"XML nesting exceeds configured depth limit: {name}")
        stack.extend((child, depth + 1) for child in node)
    return root


def _locator(
    filename: str, part: str, index: int, *, relationship_id: str | None = None
) -> SourceLocator:
    return SourceLocator(
        format="DOCX",
        status="EXACT",
        source_file=filename,
        part=part,
        index=index,
        relationship_id=relationship_id,
    )


def _text(element: ET.Element) -> str:
    chunks: list[str] = []
    for node in element.iter():
        if node.tag in {W + "t", W + "delText", W + "instrText"} and node.text:
            chunks.append(node.text)
        elif node.tag == W + "tab":
            chunks.append("\t")
        elif node.tag in {W + "br", W + "cr"}:
            chunks.append("\n")
    return "".join(chunks)


def _style(paragraph: ET.Element) -> str:
    node = paragraph.find("./w:pPr/w:pStyle", NS)
    return "" if node is None else node.get(W + "val", "")


def _alignment(paragraph: ET.Element) -> str:
    node = paragraph.find("./w:pPr/w:jc", NS)
    return "" if node is None else node.get(W + "val", "").casefold()


def _heading_label(value: str) -> str:
    return re.sub(r"\s+", " ", value.replace("\u00a0", " ")).strip().rstrip(":").casefold()


def _all_text_runs_bold(paragraph: ET.Element) -> bool:
    """Return true only when every non-empty text run is explicitly bold."""
    runs = [run for run in paragraph.findall("./w:r", NS) if _text(run).strip()]
    if not runs:
        return False
    for run in runs:
        bold = run.find("./w:rPr/w:b", NS)
        if bold is None or bold.get(W + "val", "true").casefold() in {"0", "false", "off"}:
            return False
    return True


def _inline_abstract_body(paragraph: ET.Element) -> str | None:
    """Return body text only for a distinct bold Abstract lead-in run."""
    children = list(paragraph)
    first_text_index = next(
        (index for index, child in enumerate(children) if _text(child).strip()), None
    )
    if first_text_index is None:
        return None
    lead = children[first_text_index]
    if lead.tag != W + "r" or _heading_label(_text(lead)) != "abstract":
        return None
    bold = lead.find("./w:rPr/w:b", NS)
    if bold is None or bold.get(W + "val", "true").casefold() in {"0", "false", "off"}:
        return None
    remainder = "".join(_text(child) for child in children[first_text_index + 1 :]).strip()
    return remainder or None


def _numbered_heading_parts(
    value: str, paragraph: ET.Element
) -> tuple[int, int | None, int] | None:
    """Return a strongly formatted, heading-like numeric label."""
    match = re.fullmatch(r"([1-9]\d*)(?:\.([1-9]\d*))?[.)]?\s+(.+)", value.strip())
    if not match or not _all_text_runs_bold(paragraph):
        return None
    heading_text = match.group(3).strip()
    words = re.findall(r"[^\W_]+", heading_text, re.UNICODE)
    if not words or len(words) > 20 or len(value) > 200:
        return None
    if heading_text.endswith((".", ";")):
        return None
    minor = int(match.group(2)) if match.group(2) else None
    return int(match.group(1)), minor, 2 if minor is not None else 1


def _sequenced_numbered_headings(
    paragraphs: list[tuple[int, ET.Element, str, str]],
) -> dict[int, int]:
    """Accept only a continuous top-level sequence and its continuous subsections."""
    accepted: dict[int, int] = {}
    expected_top = 1
    active_top: int | None = None
    expected_minor = 1
    for index, paragraph, value, _ in paragraphs:
        parts = _numbered_heading_parts(value, paragraph)
        if parts is None:
            continue
        major, minor, level = parts
        if level == 1:
            if major != expected_top:
                continue
            accepted[index] = level
            active_top = major
            expected_top += 1
            expected_minor = 1
        elif major == active_top and minor == expected_minor:
            accepted[index] = level
            expected_minor += 1
    return accepted


def _plain_heading(
    value: str, paragraph: ET.Element, before_body_sections: bool
) -> tuple[int, str] | None:
    """Recognize conservative common headings when Word styles are absent."""
    label = _heading_label(value)
    if label == "abstract" and before_body_sections:
        return 1, "Abstract"
    numbered = re.fullmatch(r"([1-9]\d*)(?:\.([1-9]\d*))?[.)]?\s+(.+)", value.strip())
    common_sections = {
        "introduction",
        "background",
        "methods",
        "materials and methods",
        "results",
        "discussion",
        "conclusion",
        "conclusions",
        "references",
        "bibliography",
    }
    if numbered and _heading_label(numbered.group(3)) in common_sections:
        return (2 if numbered.group(2) else 1), value
    if _all_text_runs_bold(paragraph) and label in {
        "abstract",
        "introduction",
        "methods",
        "results",
        "discussion",
        "references",
        "bibliography",
    }:
        return 1, value
    return None


def _front_matter_signal(value: str) -> bool:
    normalized = value.casefold()
    return bool(
        "@" in value
        or re.search(
            r"\b(university|institute|department|laboratory|centre|center|hospital|correspondence|affiliation)\b",
            normalized,
        )
        or re.search(
            r"\b(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\b",
            normalized,
        )
    )


def _plausible_plain_title(value: str) -> bool:
    words = re.findall(r"[^\W_]+", value, re.UNICODE)
    return 3 <= len(words) <= 40 and len(value) <= 300 and not value.endswith((".", ":", ";"))


def _relationships(archive: zipfile.ZipFile, limits: DocxResourceLimits) -> dict[str, str]:
    name = "word/_rels/document.xml.rels"
    if name not in archive.namelist():
        return {}
    root = _xml(archive.read(name), name, limits)
    relationships = {
        node.get("Id", ""): node.get("Target", "")
        for node in root.findall("pr:Relationship", NS)
        if node.get("Id")
    }
    if len(relationships) > limits.max_relationships:
        raise DocxParseError("relationship count exceeds configured limit")
    return relationships


def _note_part(
    archive: zipfile.ZipFile,
    part: str,
    kind: str,
    filename: str,
    ids: StableIdFactory,
    limits: DocxResourceLimits,
) -> list[Note]:
    if part not in archive.namelist():
        return []
    root = _xml(archive.read(part), part, limits)
    notes: list[Note] = []
    tag = W + ("footnote" if kind == "footnote" else "endnote")
    id_kind = "footnote" if kind == "footnote" else "endnote"
    for index, node in enumerate(root.findall(f".//{tag}")):
        note_id = node.get(W + "id", "")
        if note_id.startswith("-"):
            continue
        value = _text(node).strip()
        loc = _locator(filename, part, index)
        notes.append(Note(ids.make(id_kind, f"{part}:{note_id}", value), value, loc))
    return notes


def parse_docx(
    path: str | Path, *, limits: DocxResourceLimits = DEFAULT_LIMITS
) -> CanonicalManuscript:
    source_path = Path(path)
    if source_path.stat().st_size > limits.max_archive_bytes:
        raise DocxParseError("DOCX archive exceeds configured compressed size limit")
    payload = source_path.read_bytes()
    ids = StableIdFactory()
    try:
        archive = zipfile.ZipFile(source_path)
    except zipfile.BadZipFile as exc:
        raise DocxParseError(f"not a valid DOCX/ZIP container: {source_path}") from exc

    with archive:
        members = archive.infolist()
        if len(members) > limits.max_zip_members:
            raise DocxParseError("DOCX member count exceeds configured limit")
        if sum(item.file_size for item in members) > limits.max_uncompressed_total_bytes:
            raise DocxParseError("DOCX uncompressed size exceeds configured limit")
        if any(item.file_size > limits.max_member_bytes for item in members):
            raise DocxParseError("DOCX member exceeds configured size limit")
        if "word/document.xml" not in archive.namelist():
            raise DocxParseError("DOCX is missing word/document.xml")
        root = _xml(archive.read("word/document.xml"), "word/document.xml", limits)
        rels = _relationships(archive, limits)
        metadata_title = ""
        creator = ""
        if "docProps/core.xml" in archive.namelist():
            core = _xml(archive.read("docProps/core.xml"), "docProps/core.xml", limits)
            metadata_title = core.findtext("dc:title", default="", namespaces=NS)
            creator = core.findtext("dc:creator", default="", namespaces=NS)

        document_hash = _sha256(payload)
        manuscript = CanonicalManuscript(
            manuscript_id=ids.make("document", document_hash, source_path.name),
            source={"format": "DOCX", "filename": source_path.name, "sha256": document_hash},
            metadata={
                "title": metadata_title,
                "short_title": None,
                "article_type": "UNKNOWN",
                "authors": [],
                "author_order": [],
                "affiliations": [],
                "keywords": [],
            },
        )
        if creator:
            author_id = ids.make("author", "docProps/core.xml:creator", creator)
            manuscript.metadata["authors"].append(
                {
                    "object_id": author_id,
                    "name": creator,
                    "orcid": None,
                    "affiliation_ids": [],
                    "corresponding": False,
                    "email": None,
                }
            )
            manuscript.metadata["author_order"].append(author_id)

        body = root.find("w:body", NS)
        if body is None:
            raise DocxParseError("word/document.xml has no body")
        body_elements = list(body)
        paragraphs = [
            (index, element, _text(element).strip(), _style(element))
            for index, element in enumerate(body_elements)
            if element.tag == W + "p" and _text(element).strip()
        ]
        first_paragraph_index = paragraphs[0][0] if paragraphs else None
        abstract_indices = [
            index
            for index, paragraph, value, _ in paragraphs
            if _heading_label(value) == "abstract" or _inline_abstract_body(paragraph) is not None
        ]
        first_abstract_index = abstract_indices[0] if abstract_indices else None
        front_matter_values = [
            value
            for index, _, value, _ in paragraphs
            if first_paragraph_index is not None
            and first_abstract_index is not None
            and first_paragraph_index < index < first_abstract_index
        ]
        has_front_matter_evidence = len(front_matter_values) >= 2 and any(
            _front_matter_signal(value) for value in front_matter_values
        )
        if (
            first_abstract_index is not None
            and len(front_matter_values) == 1
            and len(front_matter_values[0].split()) <= 20
        ):
            has_front_matter_evidence = True
        numbered_headings = _sequenced_numbered_headings(paragraphs)
        section_stack: list[Section] = []
        current_section: Section | None = None
        in_references = False
        pending_figure_captions: list[str] = []
        pending_table_captions: list[str] = []

        for index, element in enumerate(body_elements):
            loc = _locator(source_path.name, "word/document.xml", index)
            raw_xml = ET.tostring(element, encoding="unicode")
            if element.tag == W + "p":
                value = _text(element).strip()
                style = _style(element)
                heading_match = re.match(r"Heading\s*([1-9])", style, re.IGNORECASE)
                before_abstract = first_abstract_index is None or index < first_abstract_index
                styled_title = index == first_paragraph_index and style.casefold() in {
                    "title",
                    "articletitle",
                    "manuscripttitle",
                }
                prominent_first = (
                    index == first_paragraph_index
                    and before_abstract
                    and _plausible_plain_title(value)
                    and (
                        (_all_text_runs_bold(element) and _alignment(element) == "center")
                        or has_front_matter_evidence
                    )
                )
                if value and (styled_title or prominent_first):
                    manuscript.metadata["title"] = value
                    continue
                only_front_matter = not manuscript.main_body or all(
                    not section.title for section in manuscript.main_body
                )
                inline_abstract = _inline_abstract_body(element) if only_front_matter else None
                if inline_abstract is not None:
                    section = Section(
                        ids.make("section", f"word/document.xml:p:{index}", "Abstract"),
                        "Abstract",
                        1,
                        loc,
                    )
                    section_stack.clear()
                    section_stack.append(section)
                    manuscript.abstract.append(section)
                    current_section = section
                    in_references = False
                    value = inline_abstract
                inferred_heading = (
                    (numbered_headings[index], value)
                    if index in numbered_headings
                    else _plain_heading(value, element, only_front_matter)
                )
                if inline_abstract is None and (heading_match or inferred_heading):
                    level = (
                        int(heading_match.group(1)) if heading_match else inferred_heading[0]  # type: ignore[index]
                    )
                    section = Section(
                        ids.make(
                            "section" if level == 1 else "subsection",
                            f"word/document.xml:p:{index}",
                            value,
                        ),
                        value,
                        level,
                        loc,
                    )
                    while section_stack and section_stack[-1].level >= level:
                        section_stack.pop()
                    if _heading_label(value) == "abstract" and level == 1:
                        section_stack.clear()
                        manuscript.abstract.append(section)
                    elif section_stack:
                        section_stack[-1].subsections.append(section)
                    else:
                        manuscript.main_body.append(section)
                    section_stack.append(section)
                    current_section = section
                    in_references = _heading_label(value) in {"references", "bibliography"}
                    continue
                if (
                    re.match(r"^(figure|fig\.)\s*\d+", value, re.IGNORECASE)
                    or style.lower() == "caption"
                    and value.lower().startswith(("figure", "fig."))
                ):
                    pending_figure_captions.append(value)
                if (
                    re.match(r"^table\s*\d+", value, re.IGNORECASE)
                    or style.lower() == "caption"
                    and value.lower().startswith("table")
                ):
                    pending_table_captions.append(value)

                tracked = list(element.iter(W + "ins")) + list(element.iter(W + "del"))
                if tracked:
                    manuscript.unsupported_content.append(
                        register_unsupported(
                            ids,
                            object_type="TRACKED_CHANGE",
                            locator=loc,
                            reason="inserted/deleted views are ambiguous; both are preserved as raw XML",
                            severity="BLOCKING",
                            raw_fragment=raw_xml,
                        )
                    )

                for field_index, instruction in enumerate(element.iter(W + "instrText")):
                    instruction_text = (instruction.text or "").strip()
                    field_type = (
                        instruction_text.split(maxsplit=1)[0].upper()
                        if instruction_text
                        else "UNKNOWN"
                    )
                    if field_type == "CITATION":
                        keys = re.findall(r"CITATION\s+([^\s\\]+)", instruction_text, re.IGNORECASE)
                        manuscript.citations.append(
                            Citation(
                                ids.make(
                                    "citation",
                                    f"word/document.xml:p:{index}:field:{field_index}",
                                    instruction_text,
                                ),
                                [],
                                instruction_text,
                                loc,
                                keys,
                            )
                        )
                    elif field_type in {"REF", "SEQ", "HYPERLINK"}:
                        manuscript.unsupported_content.append(
                            register_unsupported(
                                ids,
                                object_type=f"DOCX_FIELD_{field_type}",
                                locator=loc,
                                reason="recognized field instruction is preserved; target resolution is deferred",
                                severity="WARNING",
                                raw_fragment=instruction_text,
                            )
                        )
                    else:
                        manuscript.unsupported_content.append(
                            register_unsupported(
                                ids,
                                object_type=f"DOCX_FIELD_{field_type}",
                                locator=loc,
                                reason="field instruction is preserved but not interpreted",
                                severity="BLOCKING",
                                raw_fragment=instruction_text,
                            )
                        )

                for equation_index, equation in enumerate(element.iter(M + "oMath")):
                    raw_equation = ET.tostring(equation, encoding="unicode")
                    manuscript.equations.append(
                        Equation(
                            ids.make(
                                "equation",
                                f"word/document.xml:p:{index}:omml:{equation_index}",
                                raw_equation,
                            ),
                            "OMML",
                            raw_equation,
                            loc,
                        )
                    )

                for image_index, blip in enumerate(element.iter(A + "blip")):
                    relationship_id = blip.get(R + "embed") or blip.get(R + "link") or ""
                    target = rels.get(relationship_id, "")
                    part = (
                        "word/" + target.lstrip("/")
                        if target and not target.startswith("word/")
                        else target
                    )
                    content_hash = (
                        _sha256(archive.read(part)) if part in archive.namelist() else None
                    )
                    image_loc = _locator(
                        source_path.name,
                        "word/document.xml",
                        index,
                        relationship_id=relationship_id,
                    )
                    manuscript.figures.append(
                        Asset(
                            ids.make(
                                "figure",
                                f"word/document.xml:p:{index}:image:{relationship_id}:{image_index}",
                                target,
                            ),
                            f"Figure {len(manuscript.figures) + 1}",
                            "",
                            [target] if target else [],
                            image_loc,
                            content_hash,
                            None,
                        )
                    )
                    if not target or part not in archive.namelist():
                        manuscript.unsupported_content.append(
                            register_unsupported(
                                ids,
                                object_type="MISSING_IMAGE_RELATIONSHIP",
                                locator=image_loc,
                                reason="image relationship target is missing",
                                severity="BLOCKING",
                                raw_fragment=raw_xml,
                            )
                        )

                if in_references and value:
                    manuscript.references.append(
                        Reference(
                            ids.make("reference", f"word/document.xml:p:{index}", value), value, loc
                        )
                    )
                elif value and not (
                    re.match(r"^(figure|fig\.)\s*\d+", value, re.IGNORECASE)
                    or re.match(r"^table\s*\d+", value, re.IGNORECASE)
                ):
                    if current_section is None:
                        current_section = Section(
                            ids.make("section", "word/document.xml:implicit", "Untitled body"),
                            "",
                            1,
                            SourceLocator(
                                "DOCX", "PARTIAL", source_path.name, part="word/document.xml"
                            ),
                        )
                        manuscript.main_body.append(current_section)
                    current_section.paragraphs.append(
                        TextBlock(
                            ids.make("paragraph", f"word/document.xml:p:{index}", value), value, loc
                        )
                    )

            elif element.tag == W + "tbl":
                table_text = " | ".join(
                    filter(None, (_text(cell).strip() for cell in element.iter(W + "tc")))
                )
                manuscript.tables.append(
                    Asset(
                        ids.make("table", f"word/document.xml:tbl:{index}", table_text),
                        f"Table {len(manuscript.tables) + 1}",
                        "",
                        [],
                        loc,
                        _sha256(raw_xml.encode()),
                        table_text,
                    )
                )
            elif element.tag != W + "sectPr":
                manuscript.unsupported_content.append(
                    register_unsupported(
                        ids,
                        object_type=element.tag.rsplit("}", 1)[-1],
                        locator=loc,
                        reason="unrecognized top-level WordprocessingML element",
                        severity="BLOCKING",
                        raw_fragment=raw_xml,
                    )
                )

        for caption, figure in zip(pending_figure_captions, manuscript.figures, strict=False):
            figure.legend = caption
        for caption, table in zip(pending_table_captions, manuscript.tables, strict=False):
            table.legend = caption
        manuscript.footnotes = _note_part(
            archive, "word/footnotes.xml", "footnote", source_path.name, ids, limits
        )
        manuscript.endnotes = _note_part(
            archive, "word/endnotes.xml", "endnote", source_path.name, ids, limits
        )

        for tag, kind in ((W + "object", "EMBEDDED_OBJECT"), (W + "txbxContent", "TEXT_BOX")):
            for item_index, node in enumerate(root.iter(tag)):
                manuscript.unsupported_content.append(
                    register_unsupported(
                        ids,
                        object_type=kind,
                        locator=_locator(source_path.name, "word/document.xml", item_index),
                        reason="object may contain scientific content and is not represented canonically",
                        severity="BLOCKING",
                        raw_fragment=ET.tostring(node, encoding="unicode"),
                    )
                )
        for item_index, node in enumerate(root.iter(WP + "anchor")):
            manuscript.unsupported_content.append(
                register_unsupported(
                    ids,
                    object_type="FLOATING_SHAPE",
                    locator=_locator(source_path.name, "word/document.xml", item_index),
                    reason="floating layout and off-flow content are not represented canonically",
                    severity="BLOCKING",
                    raw_fragment=ET.tostring(node, encoding="unicode"),
                )
            )
        comment_nodes = list(root.iter(W + "commentRangeStart")) + list(
            root.iter(W + "commentReference")
        )
        if "word/comments.xml" in archive.namelist() or comment_nodes:
            raw_comments = (
                archive.read("word/comments.xml")
                if "word/comments.xml" in archive.namelist()
                else ET.tostring(root)
            )
            manuscript.unsupported_content.append(
                register_unsupported(
                    ids,
                    object_type="DOCX_COMMENTS",
                    locator=SourceLocator(
                        "DOCX", "PARTIAL", source_path.name, part="word/comments.xml"
                    ),
                    reason="comments may carry scientific review content and are not modeled",
                    severity="BLOCKING",
                    raw_fragment=raw_comments,
                )
            )
        return manuscript
