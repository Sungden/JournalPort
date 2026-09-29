from __future__ import annotations

import shutil
from dataclasses import replace
from pathlib import Path

from journalport.transform.hashing import file_hash
from journalport.verify.verifier import verify_candidate
from tests.verification.factories import verification_context

STAMP = "2026-09-29T00:00:00+00:00"


def _verify(context, **changes):
    source, candidate, manuscript, profile, before, plan, result = context
    values = {
        "source_path": source,
        "candidate_path": candidate,
        "original_manuscript": manuscript,
        "profile": profile,
        "before_report": before,
        "plan": plan,
        "logs": result.logs,
        "manifest": result.manifest,
        "timestamp": STAMP,
    }
    values.update(changes)
    return verify_candidate(**values)[0]


def test_tampered_plan_and_source_are_detected(tmp_path: Path) -> None:
    context = verification_context(tmp_path)
    plan = context[5]
    changed_action = replace(plan.actions[0], expected_postconditions=("forged",))
    report = _verify(context, plan=replace(plan, actions=(changed_action,)))
    assert report.transformation_verification_status == "TAMPER_DETECTED"
    context[0].write_text("changed source", encoding="utf-8")
    report = _verify(context)
    assert report.transformation_verification_status == "TAMPER_DETECTED"


def test_expected_filename_postcondition_is_independently_checked(tmp_path: Path) -> None:
    context = verification_context(tmp_path)
    wrong = tmp_path / "candidate" / "wrong.tex"
    shutil.copyfile(context[1], wrong)
    manifest = replace(context[6].manifest, candidate_hash=file_hash(wrong))
    report = _verify(context, candidate_path=wrong, manifest=manifest)
    assert report.transformation_verification_status == "VERIFICATION_FAILED"
    filename_action = next(
        item.action_id
        for item in context[5].actions
        if item.operation == "NORMALIZE_OUTPUT_FILENAME"
    )
    assert report.postcondition_checks[filename_action] == "FAIL"


def test_candidate_from_different_source_fails_scientific_preservation(tmp_path: Path) -> None:
    context = verification_context(tmp_path)
    candidate = context[1]
    candidate.write_text(
        "\\documentclass{article}\n\\begin{document}\n\\section{Results}\nDifferent 100.\n"
        "\\end{document}\n",
        encoding="utf-8",
    )
    manifest = replace(context[6].manifest, candidate_hash=file_hash(candidate))
    report = _verify(context, manifest=manifest)
    assert report.transformation_verification_status == "VERIFICATION_FAILED"
    assert report.preservation_checks["text_content"] == "FAIL"
    assert report.preservation_checks["numbers_statistics"] == "FAIL"
