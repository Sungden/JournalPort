"""Deterministic, evidence-bearing DOCX block recognition and movement."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any

from lxml import etree

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"

ALIASES = {
    "abstract": "Abstract",
    "references": "References",
    "bibliography": "References",
    "acknowledgements": "Acknowledgements",
    "acknowledgments": "Acknowledgements",
    "author contributions": "Author Contributions",
    "competing interests": "Competing Interests",
    "data availability": "Data Availability",
    "code availability": "Code Availability",
    "figure legends": "Figure Legends",
    "tables": "Tables",
    "supplementary information": "Supplementary Information",
    "introduction": "Introduction",
    "methods": "Methods",
    "results": "Results",
    "discussion": "Discussion",
    "conclusions": "Conclusions",
}
TAIL = {
    "References",
    "Acknowledgements",
    "Author Contributions",
    "Competing Interests",
    "Data Availability",
    "Code Availability",
    "Figure Legends",
    "Tables",
    "Supplementary Information",
}
CAPTION = re.compile(r"^(?:Fig(?:ure)?\.?|FIGURE)\s+(\d+)\s*[.:|]?\s+(.+)$")
TABLE_TITLE = re.compile(r"^Table\s+(\d+)\s*[.:|]?\s+(.+)$", re.IGNORECASE)


class StructureBlocked(ValueError):
    """A block boundary or asset identity is not sufficiently reliable."""


def text(node: etree._Element) -> str:
    return "".join(item.text or "" for item in node.iter(W + "t"))


def digest(node: etree._Element) -> str:
    return "sha256:" + hashlib.sha256(etree.tostring(node, method="c14n")).hexdigest()


def semantic_roles(body: etree._Element) -> dict[int, str]:
    roles: dict[int, str] = {}
    nodes = list(body)
    for block in detect_blocks(body):
        for index in range(block.start, block.end):
            if block.role == "FrontMatterBlock":
                roles[index] = (
                    "JP_TITLE"
                    if index == block.start
                    else "JP_AUTHOR"
                    if index == block.start + 1
                    else "JP_AFFILIATION"
                )
            elif block.role == "AbstractBlock":
                roles[index] = "JP_HEADING_1" if index == block.start else "JP_ABSTRACT"
            elif block.role == "ReferencesBlock":
                roles[index] = "JP_ADMIN_HEADING" if index == block.start else "JP_REFERENCES"
            elif block.role == "AdministrativeSectionBlock":
                roles[index] = "JP_ADMIN_HEADING" if index == block.start else "JP_ADMIN_BODY"
            elif block.role == "FigureLegendsBlock":
                roles[index] = "JP_ADMIN_HEADING" if index == block.start else "JP_FIGURE_LEGEND"
            elif block.role == "ScientificSectionBlock":
                roles[index] = "JP_HEADING_1" if index == block.start else "JP_BODY"
            else:
                roles[index] = "JP_BODY"
            if CAPTION.fullmatch(text(nodes[index]).strip()):
                roles[index] = "JP_FIGURE_LEGEND"
            if TABLE_TITLE.fullmatch(text(nodes[index]).strip()):
                roles[index] = "JP_TABLE_TITLE"
    return roles


@dataclass(frozen=True)
class DocumentBlock:
    role: str
    label: str
    start: int
    end: int
    confidence: str
    evidence: tuple[str, ...]


@dataclass(frozen=True)
class FigureLegend:
    number: int
    paragraph_index: int
    relationship: str | None
    body_hash: str
    confidence: str


def heading(node: etree._Element) -> tuple[str | None, str, tuple[str, ...]]:
    if node.tag != W + "p":
        return None, "LOW", ()
    value = text(node).strip().rstrip(":")
    normalized = re.sub(r"^\d+(?:\.\d+)*[.)]?\s+", "", value).casefold()
    label = ALIASES.get(normalized)
    style = node.find(W + "pPr/" + W + "pStyle")
    styled = style is not None and "heading" in str(style.get(W + "val", "")).casefold()
    bold = bool(node.findall(".//" + W + "b"))
    outline = node.find(W + "pPr/" + W + "outlineLvl") is not None
    if label and (styled or bold or outline):
        return label, "HIGH", ("canonical_label", "explicit_heading_format")
    if label:
        return label, "MEDIUM", ("canonical_label_only",)
    if styled or outline:
        return value, "HIGH", ("explicit_heading_format",)
    return None, "LOW", ()


def detect_blocks(body: etree._Element) -> tuple[DocumentBlock, ...]:
    nodes = list(body)
    markers = [
        (index, *heading(node)) for index, node in enumerate(nodes) if heading(node)[0] is not None
    ]
    blocks: list[DocumentBlock] = []
    if markers:
        blocks.append(
            DocumentBlock(
                "FrontMatterBlock",
                "Front Matter",
                0,
                markers[0][0],
                "HIGH",
                ("before_first_heading",),
            )
        )
    else:
        return (
            DocumentBlock(
                "FrontMatterBlock",
                "Front Matter",
                0,
                len(nodes),
                "LOW",
                ("no_reliable_boundaries",),
            ),
        )
    labels = [item[1] for item in markers]
    if any(labels.count(label) > 1 for label in TAIL):
        raise StructureBlocked("duplicate administrative/block heading")
    final = len(nodes) - (1 if nodes and nodes[-1].tag == W + "sectPr" else 0)
    for offset, (index, label, confidence, evidence) in enumerate(markers):
        end = markers[offset + 1][0] if offset + 1 < len(markers) else final
        role = {
            "Abstract": "AbstractBlock",
            "References": "ReferencesBlock",
            "Figure Legends": "FigureLegendsBlock",
            "Tables": "TablesBlock",
            "Supplementary Information": "SupplementBlock",
        }.get(
            str(label), "AdministrativeSectionBlock" if label in TAIL else "ScientificSectionBlock"
        )
        blocks.append(DocumentBlock(role, str(label), index, end, confidence, evidence))
    return tuple(blocks)


def conditional_blocks(body: etree._Element, target: Any) -> tuple[DocumentBlock, ...]:
    """Resolve only explicitly labelled, bounded blocks; never infer statement text."""
    order = target.get("conditional_order") if isinstance(target, dict) else None
    if (
        not isinstance(order, list)
        or len(order) < 2
        or any(not isinstance(label, str) or label.casefold() not in ALIASES for label in order)
    ):
        raise StructureBlocked("unsupported_conditional_order_target")
    labels = [ALIASES[label.casefold()] for label in order]
    if set(labels) != {"Data Availability", "Code Availability", "References"}:
        raise StructureBlocked("unsupported_conditional_section_roles")
    if len(set(labels)) != len(labels):
        raise StructureBlocked("duplicate_conditional_target")
    blocks = detect_blocks(body)
    selected = []
    for label in labels:
        matches = [block for block in blocks if block.label == label]
        if not matches:
            if label == "References":
                raise StructureBlocked("references_not_reliably_located")
            raise StructureBlocked("author_input_required_missing_" + label.replace(" ", "_"))
        block = matches[0]
        if block.confidence != "HIGH":
            raise StructureBlocked("ambiguous_conditional_heading")
        nodes = list(body)[block.start + 1 : block.end]
        if not any(text(node).strip() for node in nodes):
            if label == "References":
                raise StructureBlocked("references_not_reliably_located")
            raise StructureBlocked("author_input_required_empty_" + label.replace(" ", "_"))
        if any(node.tag != W + "p" or list(node.iter(W + "sectPr")) for node in nodes):
            raise StructureBlocked("unsupported_conditional_block_objects")
        selected.append(block)
    return tuple(selected)


def conditional_block_hashes(body: etree._Element, target: Any) -> dict[str, str]:
    # Text-body hashes retain paragraph boundaries and exact text, not renderer run segmentation.
    # XML identity for ordering-only operations is independently checked by the verifier.
    hashes = {}
    for block in conditional_blocks(body, target):
        nodes = list(body)[block.start + 1 : block.end]
        payload = json.dumps([text(node) for node in nodes], ensure_ascii=False).encode("utf-8")
        hashes[block.label] = "sha256:" + hashlib.sha256(payload).hexdigest()
    return hashes


def order_conditional_sections(body: etree._Element, target: Any) -> bool:
    blocks = conditional_blocks(body, target)
    if [block.start for block in blocks] == sorted(block.start for block in blocks):
        return False
    nodes = list(body)
    chunks = {block.start: nodes[block.start : block.end] for block in blocks}
    replacement = iter([chunks[block.start] for block in blocks])
    by_start = {block.start: block for block in blocks}
    ordered = []
    index = 0
    while index < len(nodes):
        if index in by_start:
            ordered.extend(next(replacement))
            index = by_start[index].end
        else:
            ordered.append(nodes[index])
            index += 1
    body[:] = ordered
    return True


def figure_legends(body: etree._Element) -> tuple[FigureLegend, ...]:
    nodes = list(body)
    legends: list[FigureLegend] = []
    seen: set[int] = set()
    for index, node in enumerate(nodes):
        match = CAPTION.fullmatch(text(node).strip()) if node.tag == W + "p" else None
        if not match:
            continue
        number = int(match[1])
        if number in seen:
            raise StructureBlocked("duplicate figure caption number")
        seen.add(number)
        previous = nodes[index - 1] if index else node
        embeds = list(previous.iter(A + "blip"))
        relationship = embeds[0].get(R + "embed") if len(embeds) == 1 else None
        confidence = "HIGH" if relationship else "MEDIUM"
        legends.append(
            FigureLegend(
                number,
                index,
                relationship,
                "sha256:" + hashlib.sha256(match[2].encode()).hexdigest(),
                confidence,
            )
        )
    return tuple(legends)


def collect_legends(body: etree._Element) -> None:
    nodes = list(body)
    existing = [block for block in detect_blocks(body) if block.label == "Figure Legends"]
    legends = figure_legends(body)
    if existing:
        block = existing[0]
        if any(not (block.start < legend.paragraph_index < block.end) for legend in legends):
            raise StructureBlocked("mixed inline and dedicated legend block")
        if [legend.number for legend in legends] != sorted(legend.number for legend in legends):
            raise StructureBlocked("dedicated legend order requires manual mapping")
        return
    reliable = [legend for legend in legends if legend.confidence == "HIGH"]
    if not reliable:
        return
    removed = {legend.paragraph_index for legend in reliable}
    caption_nodes = [
        nodes[legend.paragraph_index] for legend in sorted(reliable, key=lambda x: x.number)
    ]
    for node in caption_nodes:
        body.remove(node)
    title = etree.Element(W + "p")
    properties = etree.SubElement(title, W + "pPr")
    etree.SubElement(properties, W + "pStyle").set(W + "val", "JP_ADMIN_HEADING")
    etree.SubElement(properties, W + "outlineLvl").set(W + "val", "0")
    etree.SubElement(etree.SubElement(title, W + "r"), W + "t").text = "Figure Legends"
    insertion = len(body) - (1 if len(body) and body[-1].tag == W + "sectPr" else 0)
    body.insert(insertion, title)
    for offset, node in enumerate(caption_nodes, 1):
        body.insert(insertion + offset, node)
    assert len(removed) == len(caption_nodes)


def relocate_tables(body: etree._Element) -> None:
    nodes = list(body)
    if any(block.label == "Tables" for block in detect_blocks(body)):
        return
    pairs: list[tuple[int, int]] = []
    for index, node in enumerate(nodes):
        if node.tag != W + "tbl":
            continue
        neighbours = [
            candidate
            for candidate in (index - 1, index + 1)
            if 0 <= candidate < len(nodes)
            and nodes[candidate].tag == W + "p"
            and TABLE_TITLE.fullmatch(text(nodes[candidate]).strip())
        ]
        if len(neighbours) != 1:
            raise StructureBlocked("table title mapping is ambiguous or missing")
        pairs.append((index, neighbours[0]))
    if not pairs:
        return
    titles = [caption for _, caption in pairs]
    if len(titles) != len(set(titles)):
        raise StructureBlocked("one table title maps to multiple tables")
    moving = [nodes[index] for pair in pairs for index in sorted(pair)]
    for node in moving:
        body.remove(node)
    title = etree.Element(W + "p")
    props = etree.SubElement(title, W + "pPr")
    etree.SubElement(props, W + "outlineLvl").set(W + "val", "0")
    etree.SubElement(etree.SubElement(title, W + "r"), W + "t").text = "Tables"
    insertion = len(body) - (1 if len(body) and body[-1].tag == W + "sectPr" else 0)
    body.insert(insertion, title)
    for offset, node in enumerate(moving, 1):
        body.insert(insertion + offset, node)


def rebuild_structure(body: etree._Element, order: Any) -> None:
    if not isinstance(order, list) or len(order) != len(set(order)) or "References" not in order:
        raise StructureBlocked("invalid target block order")
    blocks = detect_blocks(body)
    if any(block.confidence != "HIGH" for block in blocks):
        raise StructureBlocked("automatic reordering requires HIGH-confidence boundaries")
    unknown_tail = [
        block.label for block in blocks if block.label in TAIL and block.label not in order
    ]
    if unknown_tail:
        raise StructureBlocked("target placement is undefined for: " + ", ".join(unknown_tail))
    nodes = list(body)
    fixed = [block for block in blocks if block.label not in order]
    tail_started = False
    for block in blocks:
        tail_started = tail_started or block.label in order
        if tail_started and block.role == "ScientificSectionBlock":
            raise StructureBlocked("scientific block after administrative block is ambiguous")
    # Preserve the internal order of all scientific sections.
    ordered = fixed + [block for label in order for block in blocks if block.label == label]
    final = [node for block in ordered for node in nodes[block.start : block.end]]
    sections = [node for node in nodes if node.tag == W + "sectPr"]
    if len(sections) > 1:
        raise StructureBlocked("multiple terminal section properties")
    for node in list(body):
        body.remove(node)
    for node in final + sections:
        body.append(node)
