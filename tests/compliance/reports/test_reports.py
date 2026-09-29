import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from journalport.compliance.engine import audit_manuscript
from journalport.compliance.reports import render_html, render_json
from tests.compliance.factories import active_rule, manuscript, resolved_with


def test_json_and_html_reports_are_complete() -> None:
    report = audit_manuscript(
        manuscript(), resolved_with(active_rule()), evaluation_timestamp="2026-09-29T00:00:00Z"
    )
    value = json.loads(render_json(report))
    root = Path(__file__).resolve().parents[3]
    schema = json.loads((root / "schemas/compliance_report.schema.json").read_text())
    finding = json.loads((root / "schemas/compliance_finding.schema.json").read_text())
    schema["properties"]["findings"]["items"] = finding
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(value)
    html = render_html(report)
    assert "JournalPort Compliance Report" in html
    assert report.readiness_status in html
    assert report.disclaimer in html
