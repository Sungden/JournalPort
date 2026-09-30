"""Deterministic scientific-object preservation comparisons."""

from __future__ import annotations

import copy
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
        "references": Counter(
            (item.raw_text, item.doi, repr(item.structured)) for item in manuscript.references
        ),
        "assets": Counter(
            (
                item.content_hash,
                tuple(item.file_refs),
                item.legend,
                item.content_text,
            )
            for item in manuscript.figures + manuscript.tables + manuscript.supplementary_materials
        ),
        "figure_table_references": fp.figure_table_reference,
        "sections": Counter(value for _, value in sections),
        # Parser object IDs may include source locators and therefore change when the
        # isolated candidate filename changes. Content identity is checked independently.
        "section_content": Counter(value for _, value in sections),
        "figures": [
            asdict(item) | {"object_id": None, "source_locator": None}
            for item in manuscript.figures
        ],
        "tables": [
            asdict(item) | {"object_id": None, "source_locator": None} for item in manuscript.tables
        ],
        "footnotes": [item.text for item in manuscript.footnotes],
        "endnotes": [item.text for item in manuscript.endnotes],
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


def authorized_preservation_results(
    original: CanonicalManuscript,
    candidate: CanonicalManuscript,
    allowed_changes: tuple[str, ...],
) -> tuple[dict[str, str], tuple[str, ...]]:
    """Compare manuscripts after masking only explicitly authorized semantic regions."""
    masked = copy.deepcopy(candidate)
    allowed = set(allowed_changes)
    if "abstract" in allowed:
        masked.abstract = copy.deepcopy(original.abstract)
    statement_targets = {
        item.removeprefix("statement:") for item in allowed if item.startswith("statement:")
    }
    if statement_targets:
        headings = {
            "author_contributions": {"author contributions", "author contribution statement"},
            "competing_interests": {
                "competing interests",
                "conflict of interest",
                "conflicts of interest",
            },
            "data_availability": {"data availability", "availability of data"},
            "code_availability": {"code availability", "availability of code"},
        }
        remove = set().union(*(headings[key] for key in statement_targets if key in headings))
        masked.main_body = [
            section
            for section in masked.main_body
            if section.title.strip().casefold() not in remove
        ]
        for key in statement_targets:
            masked.statements[key] = original.statements.get(key)
    heading_targets = {
        item.removeprefix("heading:") for item in allowed if item.startswith("heading:")
    }
    if heading_targets:
        aliases = {
            "author_contributions": {"author contributions", "author contribution statement"},
            "competing_interests": {
                "competing interests",
                "conflict of interest",
                "conflicts of interest",
            },
            "data_availability": {"data availability", "availability of data"},
            "code_availability": {"code availability", "availability of code"},
        }
        for key in heading_targets:
            before = [
                item for item in original.main_body if item.title.strip().casefold() in aliases[key]
            ]
            after = [
                item for item in masked.main_body if item.title.strip().casefold() in aliases[key]
            ]
            if len(before) == len(after) == 1:
                after[0].title = before[0].title
    return preservation_results(original, masked)
