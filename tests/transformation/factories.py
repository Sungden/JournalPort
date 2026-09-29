from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from journalport.compliance.engine import audit_manuscript
from journalport.compliance.hashing import report_hash
from journalport.manuscript.model import CanonicalManuscript
from journalport.transform.hashing import file_hash
from tests.compliance.factories import active_rule, manuscript, resolved_with


def context(tmp_path: Path, *, safe: bool = False):
    tmp_path.mkdir(parents=True, exist_ok=True)
    artifact = tmp_path / "unsafe name.tex"
    artifact.write_text(
        "\\documentclass{article}\n\\begin{document}42\\end{document}\n", encoding="utf-8"
    )
    source: CanonicalManuscript = manuscript(abstract_words=6)
    source.source["sha256"] = file_hash(artifact)
    profile = resolved_with(active_rule(value=5))
    report = audit_manuscript(source, profile, evaluation_timestamp="2026-09-29T00:00:00Z")
    if safe:
        finding = replace(
            report.findings[0],
            rule_id="file.name.normalized",
            status="WARNING",
            expected_value="manuscript.tex",
            autofix_class="SAFE_AUTOMATIC",
        )
        report = replace(report, findings=(finding,), report_hash="")
        report = replace(report, report_hash=report_hash(report))
    return artifact, source, profile, report
