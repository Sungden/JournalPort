from pathlib import Path

import pytest

from journalport.compliance.engine import audit_manuscript
from journalport.compliance.reports import render_json as render_compliance
from journalport.manuscript.parser_latex import parse_latex
from journalport.package.builder import build_package
from journalport.package.planner import create_package_plan
from journalport.package.verify import verify_package
from journalport.profiles.loader import ProfileRegistry
from journalport.profiles.resolver import resolve_profile
from journalport.transform.executor import execute_plan
from journalport.transform.planner import create_plan
from journalport.verify.reports import render_json as render_verification
from journalport.verify.verifier import verify_candidate

ROOT = Path(__file__).resolve().parents[2]
STAMP = "2026-09-29T00:00:00+00:00"


@pytest.mark.parametrize(
    "slug",
    ("nature-communications", "nature-computational-science", "nature-machine-intelligence"),
)
def test_three_real_profile_package_workflows(slug: str, tmp_path: Path) -> None:
    source = tmp_path / f"{slug}.tex"
    source.write_text(
        "\\documentclass{article}\n\\title{Synthetic article}\n\\begin{document}\n"
        "\\maketitle\n\\begin{abstract}Abstract.\\end{abstract}\n"
        "\\section{Results}Value 42.\\end{document}\n",
        encoding="utf-8",
    )
    cover = tmp_path / "cover_letter.pdf"
    cover.write_bytes(b"author supplied")
    original = parse_latex(source)
    ids = (
        "publisher:nature-portfolio",
        f"journal:{slug}",
        f"article-type:{slug}/article",
    )
    registry = ProfileRegistry.from_directory(ROOT / "journal_profiles")
    profile = resolve_profile(registry, *ids, {item: "1.1.0" for item in ids})
    before = audit_manuscript(original, profile, evaluation_timestamp=STAMP)
    transform_plan = create_plan(original, profile, before, source, created_at=STAMP)
    execution = execute_plan(
        transform_plan, original, profile, before, tmp_path / "candidate", timestamp=STAMP
    )
    verification, after, _ = verify_candidate(
        source_path=source,
        candidate_path=Path(execution.candidate_path),
        original_manuscript=original,
        profile=profile,
        before_report=before,
        plan=transform_plan,
        logs=execution.logs,
        manifest=execution.manifest,
        timestamp=STAMP,
    )
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    verification_path = evidence / "verification_report.json"
    compliance_path = evidence / "post_transform_compliance_report.json"
    verification_path.write_text(render_verification(verification), encoding="utf-8")
    compliance_path.write_text(render_compliance(after), encoding="utf-8")
    package_plan = create_package_plan(
        candidate=Path(execution.candidate_path),
        verification_report_path=verification_path,
        verification_report=verification,
        compliance_report_path=compliance_path,
        compliance_report=after,
        profile=profile,
        auxiliary_paths=(cover,),
        created_at=STAMP,
    )
    assert package_plan.plan_status == "READY_TO_BUILD"
    manifest, _ = build_package(
        package_plan, tmp_path / "package", created_at=STAMP, create_zip=False
    )
    _, readiness = verify_package(
        tmp_path / "package",
        profile=profile,
        verification_report=verification,
        compliance_report=after,
        timestamp=STAMP,
    )
    assert verification.transformation_verification_status == "VERIFIED_CANDIDATE"
    assert readiness.package_completeness_status == "COMPLETE"
    assert readiness.final_package_status == "PACKAGE_REQUIRES_MANUAL_REVIEW"
    assert manifest.logical_package_hash
