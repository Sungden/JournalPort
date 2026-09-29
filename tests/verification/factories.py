from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

from journalport.compliance.engine import audit_manuscript
from journalport.compliance.hashing import report_hash
from journalport.manuscript.parser_latex import parse_latex
from journalport.transform.executor import execute_plan
from journalport.transform.planner import create_plan
from tests.compliance.factories import active_rule, resolved_with


def verification_context(tmp_path: Path, *, safe: bool = True):
    source_path = tmp_path / "unsafe name.tex"
    source_path.write_text(
        "\\documentclass{article}\n\\begin{document}\n\\begin{abstract}A short abstract.\\end{abstract}\n"
        "\\section{Results}\nValue 42 and p < 0.05.\n\\end{document}\n",
        encoding="utf-8",
    )
    manuscript = parse_latex(source_path)
    profile = resolved_with(active_rule(value=500))
    before = audit_manuscript(manuscript, profile, evaluation_timestamp="2026-09-29T00:00:00+00:00")
    if safe:
        finding = replace(
            before.findings[0],
            finding_id="finding:filename-normalization",
            rule_id="file.name.normalized",
            status="WARNING",
            expected_value="manuscript.tex",
            autofix_class="SAFE_AUTOMATIC",
        )
        before = replace(before, findings=before.findings + (finding,), report_hash="")
        before = replace(before, report_hash=report_hash(before))
    plan = create_plan(
        manuscript, profile, before, source_path, created_at="2026-09-29T00:00:00+00:00"
    )
    candidate_dir = tmp_path / "candidate"
    result = execute_plan(
        plan,
        manuscript,
        profile,
        before,
        candidate_dir,
        timestamp="2026-09-29T00:00:00+00:00",
    )
    return source_path, Path(result.candidate_path), manuscript, profile, before, plan, result


def load_persisted_logs(path: Path):
    from journalport.transform.models import ActionLog

    value = json.loads(path.read_text(encoding="utf-8"))
    return tuple(
        ActionLog(
            **(
                item
                | {
                    "input_object_ids": tuple(item["input_object_ids"]),
                    "errors": tuple(item["errors"]),
                    "warnings": tuple(item["warnings"]),
                }
            )
        )
        for item in value["entries"]
    )
