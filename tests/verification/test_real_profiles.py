from pathlib import Path

import pytest

from journalport.compliance.engine import audit_manuscript
from journalport.manuscript.parser_latex import parse_latex
from journalport.profiles.loader import ProfileRegistry
from journalport.profiles.resolver import resolve_profile
from journalport.transform.executor import execute_plan
from journalport.transform.planner import create_plan
from journalport.verify.verifier import verify_candidate

ROOT = Path(__file__).resolve().parents[2]
STAMP = "2026-09-29T00:00:00+00:00"


@pytest.mark.parametrize(
    "slug",
    ("nature-communications", "nature-computational-science", "nature-machine-intelligence"),
)
def test_real_profile_audit_plan_apply_verify(slug: str, tmp_path: Path) -> None:
    source = tmp_path / f"{slug}.tex"
    source.write_text(
        "\\documentclass{article}\n\\title{Synthetic verification article}\n"
        "\\begin{document}\n\\maketitle\n\\begin{abstract}Preserved abstract.\\end{abstract}\n"
        "\\section{Results}\nA result of 42 percent.\n\\end{document}\n",
        encoding="utf-8",
    )
    original = parse_latex(source)
    ids = (
        "publisher:nature-portfolio",
        f"journal:{slug}",
        f"article-type:{slug}/article",
    )
    registry = ProfileRegistry.from_directory(ROOT / "journal_profiles")
    profile = resolve_profile(registry, *ids, {item: "1.1.0" for item in ids})
    before = audit_manuscript(original, profile, evaluation_timestamp=STAMP)
    plan = create_plan(original, profile, before, source, created_at=STAMP)
    execution = execute_plan(
        plan, original, profile, before, tmp_path / "candidate", timestamp=STAMP
    )
    report, _, delta = verify_candidate(
        source_path=source,
        candidate_path=Path(execution.candidate_path),
        original_manuscript=original,
        profile=profile,
        before_report=before,
        plan=plan,
        logs=execution.logs,
        manifest=execution.manifest,
        timestamp=STAMP,
    )
    assert report.transformation_verification_status == "VERIFIED_CANDIDATE"
    assert report.verification_status == "REQUIRES_MANUAL_REVIEW"
    assert not delta.new_blocking_findings
    assert all(value == "PASS" for value in report.preservation_checks.values())
