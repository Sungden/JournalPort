from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _run(*args: str, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "journalport.cli", *args],
        cwd=ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )


def test_apply_then_verify_in_fresh_processes_and_offline(tmp_path: Path) -> None:
    source = tmp_path / "source.tex"
    source.write_text(
        "\\documentclass{article}\n\\begin{document}\n\\section{Results}\nScientific value 42.\n\\end{document}\n",
        encoding="utf-8",
    )
    plan_dir = tmp_path / "plan"
    candidate_dir = tmp_path / "candidate"
    verify_dir = tmp_path / "verification"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    env["NO_PROXY"] = "*"
    env["HTTP_PROXY"] = "http://127.0.0.1:1"
    env["HTTPS_PROXY"] = "http://127.0.0.1:1"
    common = ["--profiles", str(ROOT / "journal_profiles")]
    planned = _run(
        "plan",
        str(source),
        "--journal",
        "nature-communications",
        "--output",
        str(plan_dir),
        *common,
        env=env,
    )
    assert planned.returncode == 0, planned.stderr
    applied = _run(
        "apply",
        str(plan_dir / "transformation_plan.json"),
        "--output",
        str(candidate_dir),
        *common,
        env=env,
    )
    assert applied.returncode == 0, applied.stderr
    candidate = next(candidate_dir.glob("*.tex"))
    verified = _run(
        "verify",
        "--source",
        str(source),
        "--candidate",
        str(candidate),
        "--plan",
        str(plan_dir / "transformation_plan.json"),
        "--log",
        str(candidate_dir / "transformation_log.json"),
        "--manifest",
        str(candidate_dir / "candidate_manifest.json"),
        "--report-before",
        str(plan_dir / "compliance_report.json"),
        "--output",
        str(verify_dir),
        *common,
        env=env,
    )
    assert verified.returncode == 0, verified.stderr
    assert (verify_dir / "verification_report.json").is_file()
    assert (verify_dir / "post_transform_compliance_report.json").is_file()
    assert (verify_dir / "compliance_delta.json").is_file()
    assert (verify_dir / "verification_report.html").is_file()
