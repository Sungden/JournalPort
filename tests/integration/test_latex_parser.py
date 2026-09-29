from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

from journalport.manuscript.fingerprints import NUMBER_RE, fingerprint, manuscript_texts
from journalport.manuscript.parser_latex import parse_latex
from journalport.manuscript.serialization import deserialize_canonical, serialize_canonical

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests/fixtures/latex"


def test_basic_latex_preserves_required_scientific_objects() -> None:
    source = FIXTURES / "basic_article/main.tex"
    first = parse_latex(source)
    second = parse_latex(source)
    assert first == second
    assert first.metadata["title"] == "Synthetic reproducible study"
    assert len(first.metadata["authors"]) == 2
    assert [section.title for section in first.main_body] == ["Results"]
    assert len(first.figures) == 1 and first.figures[0].legend == "Synthetic signal."
    assert len(first.tables) == 1 and first.tables[0].legend == "Synthetic values."
    assert len(first.equations) == 2
    assert first.citations[0].citation_keys == ["doe2025"]
    assert len(first.references) == 1
    expected_numbers = {"42", "95%", "12.5%", "p<0.01", "2025"}
    observed = {
        match.group(0).replace("\\", "").replace(" ", "")
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


def test_multifile_is_root_confined_and_provenance_is_retained() -> None:
    fixture = FIXTURES / "multi_file"
    parsed = parse_latex(fixture / "main.tex", root_directory=fixture)
    included = next(section for section in parsed.main_body if section.title == "Included results")
    assert included.source_locator.source_file.endswith("results.tex")
    nested = included.subsections[0]
    assert nested.title == "Nested detail"
    assert nested.source_locator.source_file.endswith("details.tex")
    assert not parsed.unsupported_content

    traversal = FIXTURES / "path_traversal"
    parsed_escape = parse_latex(traversal / "main.tex", root_directory=traversal)
    assert any(
        item.object_type == "LATEX_PATH_TRAVERSAL" for item in parsed_escape.unsupported_content
    )
    missing = FIXTURES / "missing_include"
    parsed_missing = parse_latex(missing / "main.tex", root_directory=missing)
    assert any(
        item.object_type == "LATEX_MISSING_INCLUDE" for item in parsed_missing.unsupported_content
    )


def test_cycles_unknown_macros_and_environments_fail_closed() -> None:
    cycle = parse_latex(
        FIXTURES / "include_cycle/main.tex", root_directory=FIXTURES / "include_cycle"
    )
    assert any(item.object_type == "LATEX_INCLUDE_CYCLE" for item in cycle.unsupported_content)
    macro = parse_latex(FIXTURES / "custom_macros/main.tex")
    assert any(
        item.object_type == "UNKNOWN_LATEX_MACRO" and item.severity == "BLOCKING"
        for item in macro.unsupported_content
    )
    environment = parse_latex(FIXTURES / "unsupported_environment/main.tex")
    assert any(
        item.object_type == "UNKNOWN_LATEX_ENVIRONMENT" and item.raw_fragment_preserved
        for item in environment.unsupported_content
    )
    unsafe = parse_latex(FIXTURES / "unsafe_commands/main.tex")
    assert any(
        item.object_type == "UNSAFE_LATEX_COMMAND" and item.severity == "BLOCKING"
        for item in unsafe.unsupported_content
    )


def test_specialized_latex_fixtures_have_golden_counts() -> None:
    citations = parse_latex(FIXTURES / "citations/main.tex")
    assert len(citations.citations) == 3
    assert sum(len(item.citation_keys) for item in citations.citations) == 4
    assert len(citations.references) == 4
    figures = parse_latex(FIXTURES / "figures/main.tex")
    assert len(figures.figures) == 1 and figures.figures[0].legend == "Panel A."
    tables = parse_latex(FIXTURES / "tables/main.tex")
    assert len(tables.tables) == 1 and "1&2" in (tables.tables[0].content_text or "")
    equations = parse_latex(FIXTURES / "equations/main.tex")
    assert len(equations.equations) == 2
