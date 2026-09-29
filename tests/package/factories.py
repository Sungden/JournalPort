from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from journalport.compliance.hashing import report_hash
from journalport.compliance.reports import render_json as render_compliance
from journalport.package.planner import create_package_plan
from journalport.profiles.hashing import resolved_hash
from journalport.profiles.models import ProfileRule
from journalport.verify.hashing import verification_report_hash
from journalport.verify.reports import render_json as render_verification
from journalport.verify.verifier import verify_candidate
from tests.verification.factories import verification_context

STAMP = "2026-09-29T00:00:00+00:00"


def with_rule(profile, rule: ProfileRule):
    trace = replace(
        profile.resolution_trace[0],
        rule_id=rule.rule_id,
        selected_rule_version=rule.rule_version,
        provenance_chain=rule.provenance,
    )
    changed = replace(
        profile,
        effective_rules=profile.effective_rules + (rule,),
        resolution_trace=profile.resolution_trace + (trace,),
        resolved_profile_hash="",
    )
    return replace(changed, resolved_profile_hash=resolved_hash(changed))


def package_context(tmp_path: Path, *, profile_override=None, auxiliary: tuple[Path, ...] = ()):
    tmp_path.mkdir(parents=True, exist_ok=True)
    (tmp_path / "transform").mkdir(parents=True, exist_ok=True)
    source, candidate, manuscript, profile, before, transformation_plan, execution = (
        verification_context(tmp_path / "transform")
    )
    verification, after, _ = verify_candidate(
        source_path=source,
        candidate_path=candidate,
        original_manuscript=manuscript,
        profile=profile,
        before_report=before,
        plan=transformation_plan,
        logs=execution.logs,
        manifest=execution.manifest,
        timestamp=STAMP,
    )
    if profile_override is not None:
        profile = profile_override(profile)
        after = replace(after, resolved_profile_hash=profile.resolved_profile_hash, report_hash="")
        after = replace(after, report_hash=report_hash(after))
        verification = replace(
            verification,
            resolved_profile_hash=profile.resolved_profile_hash,
            compliance_report_after_hash=after.report_hash,
            verification_report_hash="",
        )
        verification = replace(
            verification, verification_report_hash=verification_report_hash(verification)
        )
    evidence = tmp_path / "evidence"
    evidence.mkdir(parents=True)
    verification_path = evidence / "verification_report.json"
    compliance_path = evidence / "post_transform_compliance_report.json"
    verification_path.write_text(render_verification(verification), encoding="utf-8")
    compliance_path.write_text(render_compliance(after), encoding="utf-8")
    plan = create_package_plan(
        candidate=candidate,
        verification_report_path=verification_path,
        verification_report=verification,
        compliance_report_path=compliance_path,
        compliance_report=after,
        profile=profile,
        auxiliary_paths=auxiliary,
        created_at=STAMP,
    )
    return plan, profile, verification, after
