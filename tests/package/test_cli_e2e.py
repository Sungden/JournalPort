from __future__ import annotations

import json
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


def test_full_cli_pipeline_in_fresh_offline_processes(tmp_path: Path) -> None:
    source = tmp_path / "source.tex"
    source.write_text(
        "\\documentclass{article}\n\\title{Synthetic article}\n\\begin{document}\n"
        "\\maketitle\n\\begin{abstract}Abstract.\\end{abstract}\n"
        "\\section{Results}Value 42.\\end{document}\n",
        encoding="utf-8",
    )
    cover = tmp_path / "cover_letter.pdf"
    cover.write_bytes(b"author supplied cover letter fixture")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    env["NO_PROXY"] = "*"
    env["HTTP_PROXY"] = "http://127.0.0.1:1"
    env["HTTPS_PROXY"] = "http://127.0.0.1:1"
    profiles = ["--profiles", str(ROOT / "journal_profiles")]
    audit = _run(
        "audit",
        str(source),
        "--journal",
        "nature-communications",
        "--output",
        str(tmp_path / "audit"),
        *profiles,
        env=env,
    )
    assert audit.returncode == 0, audit.stderr
    planned = _run(
        "plan",
        str(source),
        "--journal",
        "nature-communications",
        "--output",
        str(tmp_path / "transform-plan"),
        *profiles,
        env=env,
    )
    assert planned.returncode == 0, planned.stderr
    applied = _run(
        "apply",
        str(tmp_path / "transform-plan/transformation_plan.json"),
        "--output",
        str(tmp_path / "candidate"),
        *profiles,
        env=env,
    )
    assert applied.returncode == 0, applied.stderr
    candidate = next((tmp_path / "candidate").glob("*.tex"))
    verified = _run(
        "verify",
        "--source",
        str(source),
        "--candidate",
        str(candidate),
        "--plan",
        str(tmp_path / "transform-plan/transformation_plan.json"),
        "--log",
        str(tmp_path / "candidate/transformation_log.json"),
        "--manifest",
        str(tmp_path / "candidate/candidate_manifest.json"),
        "--report-before",
        str(tmp_path / "transform-plan/compliance_report.json"),
        "--output",
        str(tmp_path / "verification"),
        *profiles,
        env=env,
    )
    assert verified.returncode == 0, verified.stderr
    package_plan = _run(
        "package",
        "plan",
        "--candidate",
        str(candidate),
        "--verification-report",
        str(tmp_path / "verification/verification_report.json"),
        "--compliance-report",
        str(tmp_path / "verification/post_transform_compliance_report.json"),
        "--journal",
        "nature-communications",
        "--artifact",
        str(cover),
        "--output",
        str(tmp_path / "package-plan"),
        *profiles,
        env=env,
    )
    assert package_plan.returncode == 0, package_plan.stderr
    built = _run(
        "package",
        "build",
        str(tmp_path / "package-plan/submission_package_plan.json"),
        "--output",
        str(tmp_path / "submission-package"),
        env=env,
    )
    assert built.returncode == 0, built.stderr
    checked = _run(
        "package",
        "verify",
        str(tmp_path / "submission-package"),
        *profiles,
        env=env,
    )
    assert checked.returncode == 0, checked.stderr
    report = json.loads(
        (tmp_path / "submission-package/package_readiness_report.json").read_text(encoding="utf-8")
    )
    assert report["candidate_verification_status"] == "VERIFIED_CANDIDATE"
    assert report["final_package_status"] == "PACKAGE_REQUIRES_MANUAL_REVIEW"
