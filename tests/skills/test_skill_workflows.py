from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_audit_skill_produces_structured_artifacts_and_preserves_unknown(tmp_path: Path) -> None:
    source = tmp_path / "source.tex"
    source.write_text(
        "\\documentclass{article}\n\\title{Synthetic}\n\\begin{document}Text.\\end{document}\n",
        encoding="utf-8",
    )
    output, record = tmp_path / "audit", tmp_path / "skill_run.json"
    env = os.environ | {"PYTHONPATH": str(ROOT / "src")}
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "skills/journal-audit/scripts/run.py"),
            str(source),
            "--journal",
            "nature-communications",
            "--profiles",
            str(ROOT / "journal_profiles"),
            "--output",
            str(output),
            "--record",
            str(record),
        ],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    report = json.loads((output / "compliance_report.json").read_text(encoding="utf-8"))
    assert any(item["status"] == "UNKNOWN" for item in report["findings"])
    run = json.loads(record.read_text(encoding="utf-8"))
    assert run["final_status"] == "AUDIT_COMPLETE"
    assert run["called_commands"][0][0] == "audit"


def test_transfer_skill_stops_at_approval_gate(tmp_path: Path) -> None:
    source = tmp_path / "source.tex"
    source.write_text(
        "\\documentclass{article}\n\\title{Synthetic}\n\\begin{document}Text.\\end{document}\n",
        encoding="utf-8",
    )
    output = tmp_path / "transfer"
    env = os.environ | {"PYTHONPATH": str(ROOT / "src")}
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "skills/journal-transfer/scripts/run.py"),
            str(source),
            "--journal",
            "nature-communications",
            "--profiles",
            str(ROOT / "journal_profiles"),
            "--output",
            str(output),
        ],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2
    run = json.loads((output / "skill_run.json").read_text(encoding="utf-8"))
    assert run["final_status"] == "APPROVAL_REQUIRED"
    assert run["manual_review_items"]
    assert not (output / "candidate").exists()
