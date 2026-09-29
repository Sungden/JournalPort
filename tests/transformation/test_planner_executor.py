from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from journalport.compliance.hashing import report_hash
from journalport.transform.executor import TransformationBlocked, execute_plan
from journalport.transform.hashing import file_hash, plan_hash
from journalport.transform.planner import TransformationInputError, create_plan
from tests.transformation.factories import context


def test_safe_filename_plan_execution_is_deterministic_idempotent_and_preserving(
    tmp_path: Path,
) -> None:
    artifact, manuscript, profile, report = context(tmp_path, safe=True)
    first = create_plan(manuscript, profile, report, artifact, created_at="2026-09-29T00:00:00Z")
    second = create_plan(manuscript, profile, report, artifact, created_at="2030-01-01T00:00:00Z")
    assert first.plan_hash == second.plan_hash
    assert first.actions[0].action_id == second.actions[0].action_id
    assert first.plan_status == "READY_FOR_SAFE_EXECUTION"
    before = file_hash(artifact)
    result = execute_plan(first, manuscript, profile, report, tmp_path / "candidate")
    repeated = execute_plan(first, manuscript, profile, report, tmp_path / "candidate")
    assert Path(result.candidate_path).name == "manuscript.tex"
    assert file_hash(artifact) == before
    assert result.manifest.candidate_hash == repeated.manifest.candidate_hash == before
    assert result.manifest.status == "TRANSFORMED_CANDIDATE"
    assert all(result.manifest.preliminary_preservation_checks.values())
    assert result.logs[0].execution_status == "APPLIED"


def test_manual_action_never_executes_without_approval(tmp_path: Path) -> None:
    artifact, manuscript, profile, report = context(tmp_path)
    plan = create_plan(manuscript, profile, report, artifact)
    assert plan.plan_status == "APPROVAL_REQUIRED"
    result = execute_plan(plan, manuscript, profile, report, tmp_path / "candidate")
    assert all(log.execution_status == "BLOCKED_APPROVAL" for log in result.logs)
    assert not result.manifest.applied_action_ids
    assert result.manifest.pending_manual_action_ids


def test_plan_source_profile_and_report_tampering_are_blocked(tmp_path: Path) -> None:
    artifact, manuscript, profile, report = context(tmp_path, safe=True)
    plan = create_plan(manuscript, profile, report, artifact)
    tampered_action = replace(plan.actions[0], parameters={"output_filename": "other.tex"})
    with pytest.raises(TransformationBlocked, match="plan hash"):
        execute_plan(
            replace(plan, actions=(tampered_action,)), manuscript, profile, report, tmp_path / "a"
        )
    artifact.write_text("changed", encoding="utf-8")
    with pytest.raises(TransformationBlocked, match="source artifact"):
        execute_plan(plan, manuscript, profile, report, tmp_path / "b")
    artifact, manuscript, profile, report = context(tmp_path / "fresh", safe=True)
    plan = create_plan(manuscript, profile, report, artifact)
    with pytest.raises(TransformationBlocked, match="profile changed"):
        execute_plan(plan, manuscript, replace(profile, status="STALE"), report, tmp_path / "c")
    with pytest.raises(TransformationBlocked, match="report changed"):
        execute_plan(
            plan, manuscript, profile, replace(report, disclaimer="tampered"), tmp_path / "d"
        )


def test_output_traversal_unknown_action_and_wrong_planning_input_are_blocked(
    tmp_path: Path,
) -> None:
    artifact, manuscript, profile, report = context(tmp_path, safe=True)
    plan = create_plan(manuscript, profile, report, artifact)
    bad_name = replace(plan.actions[0], parameters={"output_filename": "../source.tex"})
    bad_plan = replace(plan, actions=(bad_name,), plan_hash="")
    bad_plan = replace(bad_plan, plan_hash=plan_hash(bad_plan))
    with pytest.raises(ValueError, match="unsafe"):
        execute_plan(bad_plan, manuscript, profile, report, tmp_path / "candidate")
    unknown = replace(plan.actions[0], operation="UNKNOWN_AUTOMATIC")
    unknown_plan = replace(plan, actions=(unknown,), plan_hash="")
    unknown_plan = replace(unknown_plan, plan_hash=plan_hash(unknown_plan))
    with pytest.raises(TransformationBlocked, match="unknown automatic"):
        execute_plan(unknown_plan, manuscript, profile, report, tmp_path / "candidate2")
    bad_report = replace(report, input_manuscript_hash="sha256:" + "0" * 64, report_hash="")
    bad_report = replace(bad_report, report_hash=report_hash(bad_report))
    with pytest.raises(TransformationInputError, match="input artifact hash"):
        create_plan(manuscript, profile, bad_report, artifact)
