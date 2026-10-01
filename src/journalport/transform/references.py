"""Conservative bibliographic identities; no metadata enrichment or inferred fields."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Any

from lxml import etree

from journalport.manuscript.numeric_citations import expand_numeric_marker

from .structure import W, detect_blocks, text


@dataclass(frozen=True)
class CanonicalReference:
    reference_id: str
    number: int
    raw_text: str
    authors: tuple[str, ...]
    title: str | None
    source_title: str | None
    year: str | None
    volume: str | None
    issue: str | None
    pages_or_article_number: str | None
    doi: str | None
    pmid: str | None
    preprint_identifier: str | None
    parse_confidence: str

    def identity(self) -> tuple[object, ...]:
        return (
            self.authors,
            self.title,
            self.year,
            self.doi,
            self.pmid,
            self.preprint_identifier,
            self.source_title,
            self.volume,
            self.issue,
            self.pages_or_article_number,
        )


@dataclass(frozen=True)
class CitationOccurrence:
    citation_id: str
    location: int
    raw_marker: str
    linked_reference_ids: tuple[str, ...]
    linkage_confidence: str


def parse_reference(raw: str) -> CanonicalReference:
    numbered = re.fullmatch(r"\s*(\d+)\s*[.)]\s+(.+)", raw)
    number = int(numbered[1]) if numbered else 0
    payload = numbered[2] if numbered else raw
    doi_match = re.search(
        r"(?:https?://doi\.org/|doi:\s*)(10\.\d{4,9}/\S+)", payload, re.IGNORECASE
    )
    doi = doi_match[1] if doi_match else None
    pmid_match = re.search(r"PMID:\s*(\d+)", payload)
    preprint_match = re.search(r"arXiv:\s*(\d{4}\.\d{4,5}(?:v\d+)?)", payload)
    # Only an explicitly delimited, lossless subset is HIGH. General prose stays opaque.
    author_pattern = r"[^,;.&]+, (?:[A-Z]\.(?:[- ]?[A-Z]\.)*)"
    pattern = re.fullmatch(
        rf"({author_pattern}(?:(?:; |, | & ){author_pattern})*)\.? ([^.]+)\. (.+?) (\d+)(?:\((\d+)\))?, ([\w–-]+) \((\d{{4}})\)\."
        r"(?: (?:https?://doi\.org/|doi:\s*)(10\.\d{4,9}/\S+))?",
        payload,
    )
    authors = (
        tuple(item.strip() for item in re.findall(author_pattern, pattern[1])) if pattern else ()
    )
    authors_valid = bool(authors) and all(re.fullmatch(author_pattern, item) for item in authors)
    identity_source = repr((authors, pattern.groups()[1:7] if pattern else payload, doi)).encode()
    return CanonicalReference(
        "ref:" + hashlib.sha256(identity_source).hexdigest()[:24],
        number,
        raw,
        authors,
        pattern[2] if pattern else None,
        pattern[3] if pattern else None,
        pattern[7] if pattern else None,
        pattern[4] if pattern else None,
        pattern[5] if pattern else None,
        pattern[6] if pattern else None,
        doi,
        pmid_match[1] if pmid_match else None,
        preprint_match[1] if preprint_match else None,
        "HIGH"
        if pattern and number and authors_valid and not pmid_match and not preprint_match
        else "MEDIUM"
        if pattern
        else "LOW",
    )


def render_reference(reference: CanonicalReference, target: dict[str, str]) -> str:
    if reference.parse_confidence != "HIGH" or target.get("syntax") != "NUMBERED_JOURNAL_ARTICLE":
        raise ValueError("unsupported reference identity or rendering target")
    authors = "; ".join(reference.authors)
    issue = f"({reference.issue})" if reference.issue else ""
    value = (
        f"{reference.number}. {authors} {reference.title}. {reference.source_title} "
        f"{reference.volume}{issue}, {reference.pages_or_article_number} ({reference.year})."
    )
    if reference.doi:
        value += " " + doi_presentation(reference)
    if parse_reference(value).identity() != reference.identity():
        raise ValueError("rendered reference identity changed")
    return value


def doi_presentation(reference: CanonicalReference) -> str:
    match = re.search(
        r"(?:https?://doi\.org/|doi:\s*)(10\.\d{4,9}/\S+)", reference.raw_text, re.IGNORECASE
    )
    if match is None or match[1] != reference.doi:
        raise ValueError("DOI presentation cannot be preserved")
    return match[0]


@dataclass(frozen=True)
class ReferenceStyleTarget:
    """Only explicitly verified presentation attributes may affect rendering."""

    syntax: str
    status: str
    evidence_hash: str
    evidence_text: str
    source_url: str

    def validate(self) -> None:
        if (
            self.syntax != "NATURE_JOURNAL_ARTICLE"
            or self.status != "VERIFIED"
            or self.source_url != "https://www.nature.com/ncomms/submit/how-to-submit"
            or self.evidence_hash
            != "sha256:" + hashlib.sha256(self.evidence_text.encode()).hexdigest()
        ):
            raise ValueError("unverified reference style attributes")


class ReferenceRenderer:
    def __init__(self, target: ReferenceStyleTarget) -> None:
        target.validate()
        self.target = target

    def segments(self, reference: CanonicalReference) -> tuple[tuple[str, str], ...]:
        if reference.parse_confidence != "HIGH" or len(reference.authors) >= 6:
            raise ValueError("reference requires manual review; author identity cannot be elided")
        if reference.issue is not None:
            raise ValueError("issue presentation is not verified; manual review required")
        source = reference.source_title or ""
        if not ("." in source or source in {"Nature", "Science"}):
            raise ValueError("journal abbreviation requires verified author-supplied mapping")
        authors = (
            reference.authors[0]
            if len(reference.authors) == 1
            else ", ".join(reference.authors[:-1]) + " & " + reference.authors[-1]
        )
        issue = f"({reference.issue})" if reference.issue else ""
        result: tuple[tuple[str, str], ...] = (
            (f"{reference.number}. {authors} {reference.title}. ", "roman"),
            (source, "italic"),
            (" ", "roman"),
            (f"{reference.volume}{issue},", "bold"),
            (f" {reference.pages_or_article_number} ({reference.year}).", "roman"),
        )
        if reference.doi:
            result += ((" " + doi_presentation(reference), "roman"),)
        rendered = "".join(value for value, _ in result)
        if parse_reference(rendered).identity() != reference.identity():
            raise ValueError("Nature reference identity roundtrip failed")
        return result

    def render(self, reference: CanonicalReference) -> str:
        return "".join(value for value, _ in self.segments(reference))


class CitationRenderer:
    """Preserve numeric presentation and prove identity; no live-field rewriting."""

    @staticmethod
    def render(occurrence: CitationOccurrence, references: tuple[CanonicalReference, ...]) -> str:
        if occurrence.linkage_confidence != "HIGH":
            raise ValueError("citation linkage requires manual review")
        by_number = {ref.number: ref.reference_id for ref in references}
        if len(by_number) != len(references):
            raise ValueError("ambiguous reference numbering")
        linked = tuple(by_number[number] for number in expand_numeric_marker(occurrence.raw_marker))
        if linked != occurrence.linked_reference_ids:
            raise ValueError("citation identity roundtrip failed")
        return occurrence.raw_marker


def reference_nodes(body: etree._Element) -> list[etree._Element]:
    return [
        node
        for block in detect_blocks(body)
        if block.label == "References"
        for node in list(body)[block.start + 1 : block.end]
        if text(node)
    ]


def render_reference_nodes(body: etree._Element, target: dict[str, str]) -> int:
    renderer = ReferenceRenderer(ReferenceStyleTarget(**target))
    nodes = reference_nodes(body)
    linkage = inspect_linkage(body, [text(node) for node in nodes])
    if linkage["live_fields"] or linkage["linkage_confidence"] != "HIGH":
        raise ValueError(
            "reference transformation requires HIGH numeric linkage without live fields"
        )
    references = tuple(linkage["references"])
    for occurrence in linkage["citations"]:
        CitationRenderer.render(occurrence, references)
    segments = [renderer.segments(ref) for ref in references]
    for node in nodes:
        if node.tag != W + "p" or any(child.tag not in {W + "pPr", W + "r"} for child in node):
            raise ValueError("unsupported reference paragraph objects")
        if any(
            child.tag not in {W + "rPr", W + "t"} for run in node.findall(W + "r") for child in run
        ):
            raise ValueError("reference fields or non-text objects require manual review")
    for node, values in zip(nodes, segments, strict=True):
        for run in list(node.findall(W + "r")):
            node.remove(run)
        for value, presentation in values:
            run = etree.SubElement(node, W + "r")
            props = etree.SubElement(run, W + "rPr")
            # Explicit flags avoid inherited italic/bold reference styles.
            etree.SubElement(props, W + "i").set(
                W + "val", "1" if presentation == "italic" else "0"
            )
            etree.SubElement(props, W + "b").set(W + "val", "1" if presentation == "bold" else "0")
            token = etree.SubElement(run, W + "t")
            token.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
            token.text = value
    after = inspect_linkage(body, [text(node) for node in nodes])
    if [ref.identity() for ref in references] != [ref.identity() for ref in after["references"]]:
        raise ValueError("reference identity changed")
    if [(c.raw_marker, c.linked_reference_ids) for c in linkage["citations"]] != [
        (c.raw_marker, c.linked_reference_ids) for c in after["citations"]
    ]:
        raise ValueError("numeric citation identity changed")
    return len(nodes)


def inspect_linkage(body: etree._Element, reference_texts: list[str]) -> dict[str, Any]:
    refs = [parse_reference(value) for value in reference_texts]
    numbers = [ref.number for ref in refs]
    duplicate = len(numbers) != len(set(numbers)) or 0 in numbers
    by_number = {ref.number: ref.reference_id for ref in refs}
    live_fields = any(
        any(
            keyword in (node.text or "").upper()
            for keyword in ("CITATION", "ZOTERO", "ENDNOTE", "MENDELEY", "BIBLIOGRAPHY")
        )
        for node in body.iter(W + "instrText")
    ) or any(
        "CITATION" in str(node.get(W + "instr", "")).upper() for node in body.iter(W + "fldSimple")
    )
    occurrences: list[CitationOccurrence] = []
    for index, paragraph in enumerate(body.iter(W + "p")):
        value = text(paragraph)
        if value in reference_texts:
            continue
        markers = re.findall(r"\[\d+(?:\s*(?:,|–|-)\s*\d+)*\]", value)
        for run in paragraph.iter(W + "r"):
            vertical = run.find(W + "rPr/" + W + "vertAlign")
            if vertical is not None and vertical.get(W + "val") == "superscript":
                candidate = text(run)
                if re.fullmatch(r"\d+(?:\s*(?:,|–|-)\s*\d+)*", candidate):
                    markers.append(candidate)
        for marker in markers:
            try:
                linked = expand_numeric_marker(marker)
            except ValueError:
                linked = ()
            high = (
                bool(linked)
                and not duplicate
                and not live_fields
                and all(number in by_number for number in linked)
            )
            occurrences.append(
                CitationOccurrence(
                    f"citation:{index}:{len(occurrences)}",
                    index,
                    marker,
                    tuple(by_number[number] for number in linked if number in by_number),
                    "HIGH" if high else "LOW",
                )
            )
    return {
        "references": refs,
        "citations": occurrences,
        "live_fields": live_fields,
        "linkage_confidence": "HIGH"
        if occurrences and all(item.linkage_confidence == "HIGH" for item in occurrences)
        else "LOW",
        "reference_parse_confidence": "HIGH"
        if refs and all(ref.parse_confidence == "HIGH" for ref in refs)
        else "LOW",
    }
