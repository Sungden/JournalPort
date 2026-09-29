"""Static, auditable verification report renderers."""

from __future__ import annotations

import html
import json

from .models import ComplianceDelta, VerificationReport


def render_json(value: VerificationReport | ComplianceDelta) -> str:
    return json.dumps(value.to_dict(), ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def render_html(report: VerificationReport, delta: ComplianceDelta) -> str:
    def rows(values: dict[str, str]) -> str:
        return "".join(
            f"<tr><td>{html.escape(key)}</td><td>{html.escape(value)}</td></tr>"
            for key, value in sorted(values.items())
        )

    changes = "".join(
        f"<li>{html.escape(item.change)}: {html.escape(item.rule_id)}</li>" for item in delta.items
    )
    return (
        "<!doctype html><meta charset='utf-8'><title>JournalPort Verification</title>"
        "<h1>Independent Verification Report</h1>"
        f"<p>Verification Status: <strong>{html.escape(report.verification_status)}</strong></p>"
        f"<p>Transformation: {html.escape(report.transformation_verification_status)}; "
        f"Compliance readiness: {html.escape(report.compliance_readiness_status)}</p>"
        f"<h2>Scientific Preservation</h2><table>{rows(report.preservation_checks)}</table>"
        f"<h2>Expected and Unexpected Changes</h2><p>Allowed: {html.escape(', '.join(report.allowed_changes))}</p>"
        f"<p>Unexpected: {html.escape(', '.join(report.unexpected_changes))}</p>"
        f"<h2>Transformation Actions / Postconditions</h2><table>{rows(report.postcondition_checks)}</table>"
        f"<h2>Compliance Before/After</h2><ul>{changes}</ul>"
        f"<h2>New Violations</h2><p>{html.escape(', '.join(delta.new_blocking_findings))}</p>"
        f"<h2>Manual Review</h2><p>{html.escape('; '.join(report.manual_review_requirements))}</p>"
        f"<h2>Manifest / Integrity Checks</h2><table>{rows(report.manifest_checks | report.tamper_checks)}</table>"
    )
