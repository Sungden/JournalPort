"""Independent scientific-content fingerprints (lexical, not semantic NLP)."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass

from .model import CanonicalManuscript, Section

NUMBER_RE = re.compile(
    r"(?<![\w.])(?:p\s*[<=>]\s*)?[+-]?(?:\d+(?:\.\d+)?|\.\d+)(?:[eE][+-]?\d+)?%?"
)
FIGURE_TABLE_RE = re.compile(r"\b(?:fig(?:ure)?|table)\s*[A-Za-z0-9.-]+", re.IGNORECASE)


def _digest(values: list[str]) -> str:
    payload = json.dumps(values, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _normalized(text: str) -> str:
    return " ".join(unicodedata.normalize("NFC", text).replace(r"\%", "%").split())


def _section_text(sections: list[Section]) -> list[str]:
    values: list[str] = []
    for section in sections:
        values.append(section.title)
        values.extend(block.text for block in section.paragraphs)
        values.extend(_section_text(section.subsections))
    return values


def manuscript_texts(manuscript: CanonicalManuscript) -> list[str]:
    values = [str(manuscript.metadata.get("title", ""))]
    values.extend(_section_text(manuscript.abstract))
    values.extend(_section_text(manuscript.main_body))
    if manuscript.methods:
        values.extend(_section_text(manuscript.methods))
    values.extend(reference.raw_text for reference in manuscript.references)
    for asset in manuscript.figures + manuscript.tables + manuscript.supplementary_materials:
        values.extend(value for value in (asset.legend, asset.content_text) if value)
    values.extend(note.text for note in manuscript.footnotes)
    values.extend(note.text for note in manuscript.endnotes)
    return [_normalized(value) for value in values if value]


@dataclass(frozen=True, slots=True)
class ScientificContentFingerprint:
    text: str
    numeric: str
    citation: str
    reference: str
    equation: str
    asset: str
    figure_table_reference: str


def fingerprint(manuscript: CanonicalManuscript) -> ScientificContentFingerprint:
    texts = manuscript_texts(manuscript)
    numbers = [
        match.group(0).replace(" ", "") for text in texts for match in NUMBER_RE.finditer(text)
    ]
    cross_refs = [
        match.group(0).lower() for text in texts for match in FIGURE_TABLE_RE.finditer(text)
    ]
    citations = [f"{item.raw_text}|{'|'.join(item.reference_ids)}" for item in manuscript.citations]
    references = [
        f"{item.object_id}|{item.doi or ''}|{_normalized(item.raw_text)}"
        for item in manuscript.references
    ]
    equations = [
        f"{item.representation}|{item.label or ''}|{item.value}" for item in manuscript.equations
    ]
    assets = [
        f"{item.object_id}|{item.content_hash or ''}|{'|'.join(item.file_refs)}|{item.legend}|{item.content_text or ''}"
        for item in manuscript.figures + manuscript.tables + manuscript.supplementary_materials
    ]
    return ScientificContentFingerprint(
        text=_digest(texts),
        numeric=_digest(numbers),
        citation=_digest(citations),
        reference=_digest(references),
        equation=_digest(equations),
        asset=_digest(assets),
        figure_table_reference=_digest(cross_refs),
    )
