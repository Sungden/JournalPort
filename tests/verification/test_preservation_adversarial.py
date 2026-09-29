from __future__ import annotations

from copy import deepcopy

import pytest

from journalport.manuscript.model import Asset, Citation, Equation, Reference, SourceLocator
from journalport.verify.preservation import preservation_results
from tests.compliance.factories import manuscript


def _locator() -> SourceLocator:
    return SourceLocator("LATEX", "EXACT", "main.tex", line_start=1, line_end=1)


def _rich_manuscript():
    value = manuscript()
    value.equations = [Equation("eq:1", "LATEX", "x=42", _locator(), "eq:x")]
    value.citations = [Citation("cite:1", ["ref:1"], "[1]", _locator(), ["smith2020"])]
    value.references = [Reference("ref:1", "Smith (2020)", _locator(), doi="10.1/x")]
    value.figures = [Asset("fig:1", "Figure 1", "Caption", ["f.png"], _locator(), "sha256:a")]
    value.tables = [Asset("table:1", "Table 1", "Caption", [], _locator(), content_text="42")]
    return value


@pytest.mark.parametrize(
    ("category", "mutate"),
    [
        (
            "numbers_statistics",
            lambda value: setattr(value.abstract[0].paragraphs[0], "text", "99"),
        ),
        ("equations", lambda value: setattr(value.equations[0], "value", "x=43")),
        ("citations", lambda value: setattr(value.citations[0], "reference_ids", ["ref:2"])),
        ("references", lambda value: setattr(value.references[0], "doi", "10.1/y")),
        ("assets", lambda value: setattr(value.figures[0], "content_hash", "sha256:b")),
        ("tables", lambda value: setattr(value.tables[0], "content_text", "43")),
    ],
)
def test_high_risk_scientific_changes_are_detected(category, mutate) -> None:
    original = _rich_manuscript()
    candidate = deepcopy(original)
    mutate(candidate)
    checks, changed = preservation_results(original, candidate)
    assert checks[category] == "FAIL"
    assert category in changed


def test_nonsemantic_source_locator_change_is_not_a_false_positive() -> None:
    original = _rich_manuscript()
    candidate = deepcopy(original)
    candidate.abstract[0].source_locator.source_file = "candidate.tex"
    candidate.abstract[0].paragraphs[0].source_locator.source_file = "candidate.tex"
    checks, changed = preservation_results(original, candidate)
    assert not changed
    assert all(value == "PASS" for value in checks.values())
