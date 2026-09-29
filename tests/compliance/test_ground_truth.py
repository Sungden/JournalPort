from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from journalport.compliance.engine import audit_manuscript
from journalport.manuscript.model import Asset, Citation, Reference, SourceLocator
from tests.compliance.factories import active_rule, manuscript, resolved_with

GROUND_TRUTH = json.loads(
    (Path(__file__).resolve().parents[1] / "fixtures/compliance/ground_truth.json").read_text()
)


@pytest.mark.parametrize("case", sorted(GROUND_TRUTH))
def test_synthetic_ground_truth(case: str) -> None:
    source = manuscript()
    locator = SourceLocator("synthetic", "PARSED", "fixture.json")
    profile_rule = active_rule()
    selected_rule_id = profile_rule.rule_id
    if case == "abstract_too_long":
        source = manuscript(abstract_words=6)
    elif case == "missing_data_availability":
        source = manuscript(data=None)
        profile_rule = replace(
            profile_rule,
            rule_id="statements.data.required",
            target="data_availability",
            operator="EXISTS",
            value=True,
        )
    elif case == "missing_competing_interests":
        source.statements["competing_interests"] = None
        profile_rule = replace(
            profile_rule,
            rule_id="statements.competing.required",
            target="competing_interests",
            operator="EXISTS",
            value=True,
        )
    elif case == "too_many_references":
        source.references = [Reference("ref:1", "One", locator), Reference("ref:2", "Two", locator)]
        source.citations = [Citation("cite:1", ["ref:1", "ref:2"], "[1,2]", locator)]
        profile_rule = replace(
            profile_rule, rule_id="references.max_count", target="references", value=1
        )
    elif case == "too_many_figures":
        source.figures = [
            Asset("fig:1", "F1", "Caption", ["f1.png"], locator),
            Asset("fig:2", "F2", "Caption", ["f2.png"], locator),
        ]
        profile_rule = replace(
            profile_rule, rule_id="display_items.max_count", target="figures_and_tables", value=1
        )
    elif case == "missing_figure_asset":
        source.figures = [Asset("fig:1", "F1", "Caption", [], locator)]
        selected_rule_id = "integrity.figure_missing_asset"
    elif case == "citation_reference_mismatch":
        source.citations = [Citation("cite:1", ["ref:missing"], "[1]", locator)]
        selected_rule_id = "integrity.citation_missing_reference"
    elif case == "conditional_rule_unknown":
        profile_rule = replace(profile_rule, applicability_mode="CONDITIONAL")
    elif case == "unsupported_profile_rule":
        profile_rule = replace(profile_rule, operator="CUSTOM")
    elif case == "profile_unknown_case":
        profile_rule = replace(profile_rule, status="UNKNOWN", confidence="UNKNOWN")
    if not case.startswith(("missing_figure_asset", "citation_reference_mismatch")):
        selected_rule_id = profile_rule.rule_id
    report = audit_manuscript(source, resolved_with(profile_rule))
    finding = next(item for item in report.findings if item.rule_id == selected_rule_id)
    expected = GROUND_TRUTH[case]
    assert finding.status == expected["finding_status"]
    assert report.readiness_status == expected["readiness"]
