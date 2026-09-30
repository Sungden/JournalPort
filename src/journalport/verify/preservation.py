"""Deterministic scientific-object preservation comparisons."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict
from typing import Any

from journalport.manuscript.fingerprints import fingerprint, manuscript_texts
from journalport.manuscript.model import CanonicalManuscript, Section


def _section_objects(sections: list[Section]) -> list[tuple[str, str]]:
    values: list[tuple[str, str]] = []
    for section in sections:
        values.append((section.object_id, section.title))
        values.extend((item.object_id, item.text) for item in section.paragraphs)
        values.extend(_section_objects(section.subsections))
    return values


def scientific_snapshot(manuscript: CanonicalManuscript) -> dict[str, Any]:
    fp = fingerprint(manuscript)
    sections = _section_objects(manuscript.abstract + manuscript.main_body)
    if manuscript.methods:
        sections.extend(_section_objects(manuscript.methods))
    return {
        "text_content": fp.text,
        "numbers_statistics": fp.numeric,
        "equations": fp.equation,
        "citations": fp.citation,
        "references": fp.reference,
        "assets": fp.asset,
        "figure_table_references": fp.figure_table_reference,
        "sections": Counter(value for _, value in sections),
        # Parser object IDs may include source locators and therefore change when the
        # isolated candidate filename changes. Content identity is checked independently.
        "section_content": Counter(value for _, value in sections),
        "figures": [asdict(item) | {"source_locator": None} for item in manuscript.figures],
        "tables": [asdict(item) | {"source_locator": None} for item in manuscript.tables],
        "footnotes": [(item.object_id, item.text) for item in manuscript.footnotes],
        "endnotes": [(item.object_id, item.text) for item in manuscript.endnotes],
        "author_metadata": manuscript.metadata.get("authors", []),
        # Unsupported fragments are an order-insensitive multiset. Object IDs and source
        # locators are deliberately excluded because they may include the isolated filename.
        # Counter multiplicity still detects additions and removals.
        "unsupported_content": Counter(
            (
                item.object_type,
                item.severity,
                item.source_fragment_hash,
                item.raw_fragment_preserved,
                item.preservation_possible,
            )
            for item in manuscript.unsupported_content
        ),
        "text_multiset": Counter(manuscript_texts(manuscript)),
    }


def preservation_results(
    original: CanonicalManuscript, candidate: CanonicalManuscript
) -> tuple[dict[str, str], tuple[str, ...]]:
    before = scientific_snapshot(original)
    after = scientific_snapshot(candidate)
    checks: dict[str, str] = {}
    changed: list[str] = []
    for key in before:
        passed = before[key] == after[key]
        checks[key] = "PASS" if passed else "FAIL"
        if not passed:
            changed.append(key)
    return checks, tuple(changed)
