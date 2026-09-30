from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from journalport.manuscript.fingerprints import NUMBER_RE, fingerprint, manuscript_texts
from journalport.manuscript.parser_docx import parse_docx
from journalport.manuscript.serialization import deserialize_canonical, serialize_canonical
from tests.docx_fixture_factory import build_docx

ROOT = Path(__file__).resolve().parents[2]


def test_docx_supported_fixture_preserves_scientific_objects(tmp_path: Path) -> None:
    source = build_docx(tmp_path / "basic_article.docx")
    first = parse_docx(source)
    second = parse_docx(source)
    assert first == second
    assert first.metadata["title"] == "Synthetic DOCX study"
    assert len(first.abstract) == 1
    assert first.abstract[0].paragraphs[0].text == "We summarize 6 observations."
    assert [section.title for section in first.main_body] == ["Results", "References"]
    assert len(first.tables) == 1
    assert first.tables[0].content_text == "A | 2"
    assert len(first.figures) == 1
    assert first.figures[0].content_hash is not None
    assert len(first.equations) == 1 and first.equations[0].representation == "OMML"
    assert first.citations[0].citation_keys == ["doe2025"]
    assert len(first.references) == 1
    assert len(first.footnotes) == 1 and len(first.endnotes) == 1
    expected_numbers = {"42", "12.5%", "p<0.01", "2025", "3.14"}
    observed = {
        match.group(0).replace(" ", "")
        for text in manuscript_texts(first)
        for match in NUMBER_RE.finditer(text)
    }
    assert expected_numbers <= observed
    assert not [item for item in first.unsupported_content if item.severity == "BLOCKING"]
    assert deserialize_canonical(serialize_canonical(first)) == first
    assert fingerprint(first) == fingerprint(second)
    schema = json.loads(
        (ROOT / "schemas/canonical_manuscript.schema.json").read_text(encoding="utf-8")
    )
    Draft202012Validator(schema).validate(first.to_dict())


def test_docx_hazards_are_blocking_and_raw_preserved(tmp_path: Path) -> None:
    parsed = parse_docx(build_docx(tmp_path / "tracked_changes.docx", hazards=True))
    kinds = {item.object_type for item in parsed.unsupported_content}
    assert {"TRACKED_CHANGE", "DOCX_FIELD_UNKNOWN", "EMBEDDED_OBJECT"} <= kinds
    assert all(item.raw_fragment_preserved for item in parsed.unsupported_content)
    tracked = next(
        item for item in parsed.unsupported_content if item.object_type == "TRACKED_CHANGE"
    )
    assert "citation [1]" in (tracked.raw_fragment or "")
    assert "citation [2] with 11" in (tracked.raw_fragment or "")


@pytest.mark.parametrize("heading", ("styled", "plain", "bold"))
def test_common_abstract_headings_with_front_matter_are_recognized(
    tmp_path: Path, heading: str
) -> None:
    parsed = parse_docx(
        build_docx(
            tmp_path / f"abstract-{heading}.docx",
            abstract_heading=heading,
            front_matter=True,
            numbered_introduction=True,
        )
    )
    assert len(parsed.abstract) == 1
    assert parsed.abstract[0].paragraphs[0].text == "We summarize 6 observations."
    assert "1 Introduction" in [section.title for section in parsed.main_body]


def test_ambiguous_body_use_of_abstract_remains_fail_closed(tmp_path: Path) -> None:
    parsed = parse_docx(
        build_docx(tmp_path / "ambiguous.docx", abstract_heading="ambiguous", front_matter=True)
    )
    assert not parsed.abstract
