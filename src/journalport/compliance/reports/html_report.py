"""Self-contained static HTML report output."""

from __future__ import annotations

from html import escape

from ..models import ComplianceReport


def render_html(report: ComplianceReport) -> str:
    groups = {
        "Blocking Issues": {"BLOCKED", "EVALUATION_ERROR"},
        "Warnings": {"WARNING"},
        "Unknown / Manual Review": {"UNKNOWN"},
        "Passed Rules": {"PASS", "NOT_APPLICABLE"},
    }
    sections: list[str] = []
    for heading, statuses in groups.items():
        rows = []
        for finding in report.findings:
            if finding.status in statuses:
                rows.append(
                    "<tr><td>"
                    + escape(finding.status)
                    + "</td><td>"
                    + escape(finding.rule_id)
                    + "</td><td>"
                    + escape(finding.message)
                    + "</td><td>"
                    + escape(finding.profile_id)
                    + "</td></tr>"
                )
        sections.append(
            f"<h2>{escape(heading)}</h2><table><tr><th>Status</th><th>Rule</th>"
            f"<th>Explanation</th><th>Profile source</th></tr>{''.join(rows)}</table>"
        )
    caveats = "".join(f"<li>{escape(item)}</li>" for item in report.profile_caveats)
    unsupported = "".join(
        f"<li>{escape(item)}</li>" for item in report.unsupported_manuscript_content
    )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>JournalPort Compliance Report</title>
<style>body{{font:15px system-ui;max-width:1100px;margin:2rem auto;padding:0 1rem}}table{{border-collapse:collapse;width:100%}}th,td{{border:1px solid #bbb;padding:.5rem;text-align:left;vertical-align:top}}code{{word-break:break-all}}.status{{font-size:1.4rem;font-weight:700}}</style></head>
<body><h1>JournalPort Compliance Report</h1><p class="status">{escape(report.readiness_status)}</p>
<p>Profile: {escape(report.profile_id)} @ {escape(report.profile_version)}</p>
<p>Resolved hash: <code>{escape(report.resolved_profile_hash)}</code></p>
<h2>Summary</h2><pre>{escape(str(report.summary))}</pre>{"".join(sections)}
<h2>Profile Caveats</h2><ul>{caveats}</ul><h2>Unsupported Manuscript Content</h2><ul>{unsupported}</ul>
<h2>Provenance</h2><p>Each row retains its profile ID, rule ID, provenance references, and resolution-trace reference in the JSON report.</p>
<p>{escape(report.disclaimer)}</p></body></html>"""
