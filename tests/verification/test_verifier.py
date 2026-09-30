from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from journalport.compliance.engine import audit_manuscript
from journalport.compliance.hashing import report_hash
from journalport.manuscript.parser_docx import parse_docx
from journalport.transform.executor import execute_plan
from journalport.transform.hashing import file_hash
from journalport.transform.planner import create_plan
from journalport.verify.verifier import VerificationInputError, verify_candidate
from tests.compliance.factories import active_rule, resolved_with
from tests.docx_fixture_factory import build_docx
from tests.verification.factories import verification_context

STAMP = "2026-09-29T00:00:00+00:00"


def test_valid_filename_only_candidate_is_independently_verified(tmp_path: Path) -> None:
    source, candidate, manuscript, profile, before, plan, result = verification_context(tmp_path)
    report, after, delta = verify_candidate(
        source_path=source,
        candidate_path=candidate,
        original_manuscript=manuscript,
        profile=profile,
        before_report=before,
        plan=plan,
        logs=result.logs,
        manifest=result.manifest,
        timestamp=STAMP,
    )
    assert report.transformation_verification_status == "VERIFIED_CANDIDATE"
    assert report.allowed_changes == report.observed_changes == ("filename",)
    assert not report.unexpected_changes
    assert all(value == "PASS" for value in report.preservation_checks.values())
    assert delta.profile_unchanged
    assert after.resolved_profile_hash == before.resolved_profile_hash


def test_numeric_change_and_manifest_tampering_fail_closed(tmp_path: Path) -> None:
    source, candidate, manuscript, profile, before, plan, result = verification_context(tmp_path)
    candidate.write_text(
        candidate.read_text(encoding="utf-8").replace("42", "43"), encoding="utf-8"
    )
    tampered_manifest = replace(result.manifest, candidate_hash="sha256:" + "0" * 64)
    report, _, _ = verify_candidate(
        source_path=source,
        candidate_path=candidate,
        original_manuscript=manuscript,
        profile=profile,
        before_report=before,
        plan=plan,
        logs=result.logs,
        manifest=tampered_manifest,
        timestamp=STAMP,
    )
    assert report.transformation_verification_status == "TAMPER_DETECTED"
    assert report.preservation_checks["numbers_statistics"] == "FAIL"
    assert "numbers_statistics" in report.unexpected_changes


def test_ghost_missing_duplicate_actions_and_profile_tamper_are_detected(tmp_path: Path) -> None:
    source, candidate, manuscript, profile, before, plan, result = verification_context(tmp_path)
    ghost = replace(result.logs[0], action_id="action:ghost")
    report, _, _ = verify_candidate(
        source_path=source,
        candidate_path=candidate,
        original_manuscript=manuscript,
        profile=replace(profile, status="STALE"),
        before_report=before,
        plan=plan,
        logs=(ghost, ghost),
        manifest=result.manifest,
        timestamp=STAMP,
    )
    assert report.transformation_verification_status == "TAMPER_DETECTED"
    assert report.manifest_checks["no_unknown_executed_action"] == "FAIL"
    assert report.manifest_checks["no_duplicate_execution"] == "FAIL"
    assert report.tamper_checks["profile_hash"] == "FAIL"


def test_source_candidate_isolation_and_deterministic_logical_hash(tmp_path: Path) -> None:
    source, candidate, manuscript, profile, before, plan, result = verification_context(tmp_path)
    kwargs = {
        "source_path": source,
        "candidate_path": candidate,
        "original_manuscript": manuscript,
        "profile": profile,
        "before_report": before,
        "plan": plan,
        "logs": result.logs,
        "manifest": result.manifest,
    }
    first, _, _ = verify_candidate(**kwargs, timestamp=STAMP)
    second, _, _ = verify_candidate(**kwargs, timestamp="2030-01-01T00:00:00+00:00")
    assert first.verification_report_hash == second.verification_report_hash
    with pytest.raises(VerificationInputError, match="isolated"):
        verify_candidate(**(kwargs | {"candidate_path": source}), timestamp=STAMP)


def test_byte_identical_renamed_docx_with_unsupported_content_verifies(tmp_path: Path) -> None:
    source = build_docx(
        tmp_path / "realistic-source.docx",
        abstract_heading="flattened",
        front_matter=True,
        numbered_introduction=True,
        warning_field=True,
        title_mode="plain",
        core_title=False,
        real_world_structure=True,
    )
    manuscript = parse_docx(source)
    assert manuscript.metadata["title"] == "A World Model of the Virtual Cell"
    assert manuscript.abstract
    assert sum(section.title[:1].isdigit() for section in manuscript.main_body) == 12
    assert manuscript.unsupported_content
    profile = resolved_with(active_rule(value=500))
    before = audit_manuscript(manuscript, profile, evaluation_timestamp=STAMP)
    filename_finding = replace(
        before.findings[0],
        finding_id="finding:docx-filename-normalization",
        rule_id="file.name.normalized",
        status="WARNING",
        expected_value="manuscript.docx",
        autofix_class="SAFE_AUTOMATIC",
    )
    before = replace(before, findings=before.findings + (filename_finding,), report_hash="")
    before = replace(before, report_hash=report_hash(before))
    plan = create_plan(manuscript, profile, before, source, created_at=STAMP)
    result = execute_plan(
        plan, manuscript, profile, before, tmp_path / "candidate", timestamp=STAMP
    )
    candidate = Path(result.candidate_path)
    assert file_hash(source) == file_hash(candidate)
    report, _, _ = verify_candidate(
        source_path=source,
        candidate_path=candidate,
        original_manuscript=manuscript,
        profile=profile,
        before_report=before,
        plan=plan,
        logs=result.logs,
        manifest=result.manifest,
        timestamp=STAMP,
    )
    assert report.preservation_checks["unsupported_content"] == "PASS"
    assert report.transformation_verification_status == "VERIFIED_CANDIDATE"


def test_pending_actions_do_not_duplicate_unrelated_preservation_failure(tmp_path: Path) -> None:
    source, candidate, manuscript, profile, before, plan, result = verification_context(
        tmp_path, safe=False, abstract_limit=1
    )
    candidate.write_text(
        candidate.read_text(encoding="utf-8").replace("42", "43"), encoding="utf-8"
    )
    manifest = replace(result.manifest, candidate_hash=file_hash(candidate))
    report, _, _ = verify_candidate(
        source_path=source,
        candidate_path=candidate,
        original_manuscript=manuscript,
        profile=profile,
        before_report=before,
        plan=plan,
        logs=result.logs,
        manifest=manifest,
        timestamp=STAMP,
    )
    assert report.transformation_verification_status == "VERIFICATION_FAILED"
    assert report.preservation_checks["numbers_statistics"] == "FAIL"
    assert report.postcondition_checks
    assert set(report.postcondition_checks.values()) == {"NOT_APPLICABLE"}
    assert not set(report.postcondition_checks) & set(report.failure_reasons)
