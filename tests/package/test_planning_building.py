from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from journalport.package.builder import PackageBuildBlocked, build_package
from journalport.package.hashing import file_hash
from journalport.package.verify import verify_package
from tests.compliance.factories import active_rule
from tests.package.factories import STAMP, package_context, with_rule


def test_complete_known_package_build_verify_and_reproduce(tmp_path: Path) -> None:
    plan, profile, verification, compliance = package_context(tmp_path)
    assert plan.plan_status == "READY_TO_BUILD"
    first, zip_one = build_package(plan, tmp_path / "one", created_at=STAMP)
    second, zip_two = build_package(plan, tmp_path / "two", created_at=STAMP)
    assert first.logical_package_hash == second.logical_package_hash
    assert zip_one is not None and zip_two is not None
    assert file_hash(zip_one) == file_hash(zip_two)
    third, _ = build_package(
        plan, tmp_path / "three", created_at="2030-01-01T00:00:00Z", create_zip=False
    )
    assert third.logical_package_hash == first.logical_package_hash
    _, readiness = verify_package(
        tmp_path / "one",
        profile=profile,
        verification_report=verification,
        compliance_report=compliance,
        timestamp=STAMP,
    )
    assert readiness.final_package_status in {"PACKAGE_READY", "PACKAGE_READY_WITH_WARNINGS"}
    assert all(value == "PASS" for value in readiness.integrity_checks.values())


def test_missing_required_and_unknown_requirement_are_preserved(tmp_path: Path) -> None:
    required = replace(
        active_rule("cover.required", True),
        target="cover_letter",
        operator="EXISTS",
        critical_for_readiness=True,
    )
    plan, _, _, _ = package_context(
        tmp_path / "missing", profile_override=lambda profile: with_rule(profile, required)
    )
    assert plan.plan_status == "PACKAGE_BUILD_BLOCKED"
    assert "requirement:cover.required" in plan.missing_requirements
    with pytest.raises(PackageBuildBlocked, match="required artifacts"):
        build_package(plan, tmp_path / "blocked")

    unknown = replace(
        active_rule("title.page.unknown", "UNKNOWN", status="UNKNOWN", critical=False),
        target="title_page_requirements",
    )
    plan, profile, verification, compliance = package_context(
        tmp_path / "unknown", profile_override=lambda value: with_rule(value, unknown)
    )
    assert plan.unknown_requirements == ("requirement:title.page.unknown",)
    build_package(plan, tmp_path / "unknown-package", created_at=STAMP, create_zip=False)
    _, readiness = verify_package(
        tmp_path / "unknown-package",
        profile=profile,
        verification_report=verification,
        compliance_report=compliance,
        timestamp=STAMP,
    )
    assert readiness.final_package_status == "PACKAGE_REQUIRES_MANUAL_REVIEW"

    conditional = replace(
        active_rule("ethics.document", True, critical=False),
        target="ethics_document",
        operator="EXISTS",
        applicability_mode="CONDITIONAL",
        applicability="When human-subject research applies",
    )
    plan, profile, verification, compliance = package_context(
        tmp_path / "conditional", profile_override=lambda value: with_rule(value, conditional)
    )
    assert plan.conditional_requirements == ("requirement:ethics.document",)
    build_package(plan, tmp_path / "conditional-package", created_at=STAMP, create_zip=False)
    _, readiness = verify_package(
        tmp_path / "conditional-package",
        profile=profile,
        verification_report=verification,
        compliance_report=compliance,
        timestamp=STAMP,
    )
    assert readiness.final_package_status == "PACKAGE_REQUIRES_MANUAL_REVIEW"


def test_modified_missing_and_extra_files_are_detected(tmp_path: Path) -> None:
    plan, profile, verification, compliance = package_context(tmp_path)
    manifest, _ = build_package(plan, tmp_path / "package", created_at=STAMP, create_zip=False)
    main = next(item for item in manifest.artifacts if item.artifact_type == "MAIN_MANUSCRIPT")
    (tmp_path / "package" / main.relative_path).write_text("tampered", encoding="utf-8")
    (tmp_path / "package" / "hidden.bin").write_bytes(b"payload")
    _, readiness = verify_package(
        tmp_path / "package",
        profile=profile,
        verification_report=verification,
        compliance_report=compliance,
        timestamp=STAMP,
    )
    assert readiness.final_package_status == "PACKAGE_VERIFICATION_FAILED"
    assert readiness.integrity_checks[f"artifact:{main.artifact_id}"] == "FAIL"
    assert readiness.integrity_checks["no_undeclared_files"] == "FAIL"


def test_missing_file_manifest_and_evidence_swaps_are_detected(tmp_path: Path) -> None:
    plan, profile, verification, compliance = package_context(tmp_path)
    manifest, _ = build_package(plan, tmp_path / "package", created_at=STAMP, create_zip=False)
    report_file = tmp_path / "package/metadata/verification_report.json"
    report_file.unlink()
    _, readiness = verify_package(
        tmp_path / "package",
        profile=profile,
        verification_report=replace(verification, disclaimer="swapped")
        if hasattr(verification, "disclaimer")
        else replace(verification, journalport_version="swapped"),
        compliance_report=compliance,
        timestamp=STAMP,
    )
    assert readiness.final_package_status == "PACKAGE_VERIFICATION_FAILED"
    assert readiness.integrity_checks["verification_report_hash"] == "FAIL"
    verification_artifact = next(
        item for item in manifest.artifacts if item.artifact_id == "artifact:verification-report"
    )
    assert readiness.integrity_checks[f"artifact:{verification_artifact.artifact_id}"] == "FAIL"

    _, profile_readiness = verify_package(
        tmp_path / "package",
        profile=replace(profile, status="STALE"),
        verification_report=verification,
        compliance_report=compliance,
        timestamp=STAMP,
    )
    assert profile_readiness.integrity_checks["profile_hash"] == "FAIL"

    value = json.loads((tmp_path / "package/submission_manifest.json").read_text(encoding="utf-8"))
    value["package_id"] = "package:tampered"
    (tmp_path / "package/submission_manifest.json").write_text(json.dumps(value), encoding="utf-8")
    _, readiness = verify_package(
        tmp_path / "package",
        profile=profile,
        verification_report=verification,
        compliance_report=compliance,
        timestamp=STAMP,
    )
    assert readiness.integrity_checks["manifest_logical_hash"] == "FAIL"


def test_portable_manifest_contains_no_absolute_paths(tmp_path: Path) -> None:
    plan, _, _, _ = package_context(tmp_path)
    manifest, _ = build_package(plan, tmp_path / "package", created_at=STAMP, create_zip=False)
    for artifact in manifest.artifacts:
        assert not Path(artifact.relative_path).is_absolute()
        assert str(tmp_path) not in artifact.relative_path
