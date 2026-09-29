"""Package readiness renderers."""

from __future__ import annotations

import html
import json

from .models import PackageReadinessReport


def render_json(report: PackageReadinessReport) -> str:
    return json.dumps(report.to_dict(), ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def render_html(report: PackageReadinessReport) -> str:
    checks = "".join(
        f"<tr><td>{html.escape(key)}</td><td>{html.escape(value)}</td></tr>"
        for key, value in sorted(report.integrity_checks.items())
    )
    return (
        "<!doctype html><meta charset='utf-8'><title>Package Readiness</title>"
        f"<h1>{html.escape(report.final_package_status)}</h1>"
        f"<p>Candidate verification: {html.escape(report.candidate_verification_status)}</p>"
        f"<p>Compliance readiness: {html.escape(report.compliance_readiness_status)}</p>"
        f"<p>Package completeness: {html.escape(report.package_completeness_status)}</p>"
        f"<p>Profile confidence: {html.escape(report.profile_confidence_status)}</p>"
        f"<h2>Integrity checks</h2><table>{checks}</table>"
        f"<h2>Missing artifacts</h2><p>{html.escape(', '.join(report.missing_artifacts))}</p>"
        f"<h2>Unknown/conditional requirements</h2><p>{html.escape(', '.join(report.unknown_requirements + report.conditional_requirements))}</p>"
        f"<h2>Manual review</h2><p>{html.escape(', '.join(report.manual_review_requirements))}</p>"
    )
