from __future__ import annotations

import json
import socket
from pathlib import Path

import pytest

from journalport.cli import main
from journalport.compliance.engine import audit_manuscript
from journalport.compliance.reports import render_json as render_compliance
from journalport.manuscript.parser_docx import parse_docx
from journalport.package.builder import build_package
from journalport.package.planner import create_package_plan
from journalport.package.verify import verify_package
from journalport.profiles.loader import ProfileRegistry
from journalport.profiles.resolver import resolve_profile
from journalport.transform import docx_editor
from journalport.transform.approvals import proposed_content_hash
from journalport.transform.executor import TransformationBlocked, execute_plan
from journalport.transform.hashing import file_hash
from journalport.transform.models import Approval
from journalport.transform.planner import create_plan
from journalport.verify.reports import render_json as render_verification
from journalport.verify.verifier import verify_candidate
from tests.docx_fixture_factory import build_docx

ROOT = Path(__file__).resolve().parents[2]
STAMP = "2026-09-30T00:00:00+00:00"


def _profile():
    registry = ProfileRegistry.from_directory(ROOT / "journal_profiles")
    ids = (
        "publisher:nature-portfolio",
        "journal:nature-communications",
        "article-type:nature-communications/article",
    )
    return resolve_profile(registry, *ids, {item: "1.1.0" for item in ids})


def _context(tmp_path: Path):
    secret = "CONFIDENTIAL_SECRET_MARKER_7F92"
    long_abstract = " ".join([secret] + [f"synthetic{i}" for i in range(220)])
    source = build_docx(
        tmp_path / "private-synthetic.docx",
        abstract_body=long_abstract,
        numbered_introduction=True,
    )
    manuscript = parse_docx(source)
    profile = _profile()
    report = audit_manuscript(manuscript, profile, evaluation_timestamp=STAMP)
    plan = create_plan(manuscript, profile, report, source, created_at=STAMP)
    payload_by_target = {
        "abstract": "Approved concise abstract with deterministic synthetic wording and no claims.",
        "author_contributions": "A.E. designed and wrote the synthetic study.",
        "competing_interests": "The authors declare no competing interests.",
        "data_availability": "Synthetic data are available in the local test fixture.",
    }
    approvals: list[Approval] = []
    payloads: dict[str, str] = {}
    for action in plan.actions:
        target = action.parameters.get("target_key")
        if not isinstance(target, str) or target not in payload_by_target:
            continue
        payload = payload_by_target[target]
        payloads[action.action_id] = payload
        approvals.append(
            Approval(
                "1.0.0",
                action.action_id,
                plan.plan_hash,
                proposed_content_hash(action, payload),
                "APPROVED",
                "synthetic-author",
                STAMP,
            )
        )
    return source, manuscript, profile, report, plan, tuple(approvals), payloads, secret


def test_m10_approved_docx_changes_are_local_verified_and_content_minimal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source, manuscript, profile, before, plan, approvals, payloads, secret = _context(tmp_path)
    source_before = file_hash(source)

    def blocked_socket(*args: object, **kwargs: object) -> None:
        raise AssertionError("network access attempted")

    monkeypatch.setattr(socket, "socket", blocked_socket)
    result = execute_plan(
        plan,
        manuscript,
        profile,
        before,
        tmp_path / "runtime",
        approvals=approvals,
        payloads=payloads,
        timestamp=STAMP,
    )
    candidate = Path(result.candidate_path)
    assert file_hash(source) == source_before
    assert file_hash(candidate) != source_before
    parsed = parse_docx(candidate)
    assert (
        parsed.abstract[0].paragraphs[0].text
        == payloads[
            next(
                action.action_id
                for action in plan.actions
                if action.operation == "REPLACE_ABSTRACT"
            )
        ]
    )
    assert parsed.statements["author_contributions"]
    assert parsed.statements["competing_interests"]
    assert parsed.statements["data_availability"]
    verification, after, _ = verify_candidate(
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
    assert verification.transformation_verification_status == "VERIFIED_CANDIDATE"
    assert not verification.unexpected_changes
    assert len(result.manifest.applied_action_ids) == 4
    assert after.findings
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    verification_path = evidence / "verification_report.json"
    compliance_path = evidence / "post_transform_compliance_report.json"
    verification_path.write_text(render_verification(verification), encoding="utf-8")
    compliance_path.write_text(render_compliance(after), encoding="utf-8")
    cover = tmp_path / "cover_letter.pdf"
    cover.write_bytes(b"%PDF-1.4 synthetic cover letter")
    package_plan = create_package_plan(
        candidate=candidate,
        verification_report_path=verification_path,
        verification_report=verification,
        compliance_report_path=compliance_path,
        compliance_report=after,
        profile=profile,
        auxiliary_paths=(cover,),
        created_at=STAMP,
    )
    assert package_plan.plan_status == "READY_TO_BUILD"
    build_package(package_plan, tmp_path / "package", created_at=STAMP, create_zip=False)
    _, readiness = verify_package(
        tmp_path / "package",
        profile=profile,
        verification_report=verification,
        compliance_report=after,
        timestamp=STAMP,
    )
    assert readiness.final_package_status != "PACKAGE_VERIFICATION_FAILED"
    metadata = (tmp_path / "runtime" / "transformation_log.json").read_text(encoding="utf-8")
    metadata += (tmp_path / "runtime" / "candidate_manifest.json").read_text(encoding="utf-8")
    assert secret not in metadata
    assert all(payload not in metadata for payload in payloads.values())
    assert not list((tmp_path / "runtime").glob("*.tmp*"))
    assert not candidate.is_relative_to(ROOT)


def test_m10_missing_or_wrong_approval_never_modifies_content(tmp_path: Path) -> None:
    source, manuscript, profile, before, plan, approvals, payloads, _ = _context(tmp_path)
    result = execute_plan(plan, manuscript, profile, before, tmp_path / "no-approval")
    assert file_hash(Path(result.candidate_path)) == file_hash(source)
    assert not result.manifest.applied_action_ids
    wrong_payloads = dict(payloads)
    first = approvals[0].action_id
    wrong_payloads[first] = "Different unapproved content."
    result = execute_plan(
        plan,
        manuscript,
        profile,
        before,
        tmp_path / "wrong-approval",
        approvals=approvals,
        payloads=wrong_payloads,
    )
    assert first not in result.manifest.applied_action_ids


def test_m10_changed_source_and_forced_failure_leave_no_temporary_content(
    tmp_path: Path,
) -> None:
    source, manuscript, profile, before, plan, approvals, payloads, _ = _context(tmp_path)
    source.write_bytes(source.read_bytes() + b"changed")
    with pytest.raises(TransformationBlocked, match="source artifact"):
        execute_plan(
            plan,
            manuscript,
            profile,
            before,
            tmp_path / "changed-source",
            approvals=approvals,
            payloads=payloads,
        )
    assert not (tmp_path / "changed-source").exists()


def test_m10_atomic_write_failure_cleans_temporary_package(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, manuscript, profile, before, plan, approvals, payloads, _ = _context(tmp_path)
    output = tmp_path / "forced-failure"

    def fail_replace(*args: object, **kwargs: object) -> None:
        raise OSError("synthetic atomic replace failure")

    monkeypatch.setattr(docx_editor.os, "replace", fail_replace)
    with pytest.raises(TransformationBlocked, match="OSError"):
        execute_plan(
            plan,
            manuscript,
            profile,
            before,
            output,
            approvals=approvals,
            payloads=payloads,
        )
    assert not list(output.glob(".journalport-*.tmp.docx"))
    assert not (output / "manuscript_transformed.docx").exists()


def test_m10_cli_approval_is_explicit_and_payload_is_not_embedded(tmp_path: Path) -> None:
    source, _, _, before, plan, _, payloads, _ = _context(tmp_path)
    plan_dir = tmp_path / "plan"
    plan_dir.mkdir()
    plan_path = plan_dir / "transformation_plan.json"
    plan_path.write_text(json.dumps(plan.to_dict()), encoding="utf-8")
    (plan_dir / "compliance_report.json").write_text(render_compliance(before), encoding="utf-8")
    action = next(item for item in plan.actions if item.operation == "REPLACE_ABSTRACT")
    payload_path = tmp_path / "approved-abstract.txt"
    payload_path.write_text(payloads[action.action_id], encoding="utf-8")
    approval_path = tmp_path / "approval.json"
    assert (
        main(
            [
                "approve",
                str(plan_path),
                "--action",
                action.action_id,
                "--payload",
                str(payload_path),
                "--approved-by",
                "synthetic-author",
                "--output",
                str(approval_path),
            ]
        )
        == 0
    )
    approval_text = approval_path.read_text(encoding="utf-8")
    assert payloads[action.action_id] not in approval_text
    assert (
        main(
            [
                "apply",
                str(plan_path),
                "--profiles",
                str(ROOT / "journal_profiles"),
                "--output",
                str(tmp_path / "cli-candidate"),
                "--approval",
                str(approval_path),
                "--payload",
                f"{action.action_id}={payload_path}",
            ]
        )
        == 0
    )
    assert file_hash(source) != file_hash(tmp_path / "cli-candidate/manuscript_transformed.docx")
