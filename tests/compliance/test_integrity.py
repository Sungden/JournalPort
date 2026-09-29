from journalport.compliance.engine import audit_manuscript
from journalport.manuscript.model import Asset, Citation, Reference, SourceLocator
from tests.compliance.factories import active_rule, manuscript, resolved_with


def test_reference_and_figure_integrity_findings() -> None:
    source = manuscript()
    locator = SourceLocator("synthetic", "PARSED", "fixture.json")
    source.references = [
        Reference("ref:1", "Same", locator, doi="10.1/example"),
        Reference("ref:2", "Same", locator, doi="https://doi.org/10.1/example"),
    ]
    source.citations = [Citation("cite:1", ["ref:missing"], "[1]", locator)]
    source.figures = [Asset("fig:1", "Figure 1", "", [], locator)]
    report = audit_manuscript(source, resolved_with(active_rule()))
    status = {item.rule_id: item.status for item in report.findings}
    assert status["integrity.citation_missing_reference"] == "BLOCKED"
    assert status["integrity.uncited_reference"] == "WARNING"
    assert status["integrity.duplicate_reference"] == "WARNING"
    assert status["integrity.duplicate_doi"] == "WARNING"
    assert status["integrity.figure_missing_asset"] == "BLOCKED"
    assert status["integrity.figure_missing_caption"] == "WARNING"
