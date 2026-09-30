"""Independent, offline post-transformation verifier."""

from __future__ import annotations

from dataclasses import asdict, replace
from datetime import UTC, datetime
from pathlib import Path

from journalport import __version__
from journalport.compliance.engine import audit_manuscript
from journalport.compliance.hashing import report_hash
from journalport.compliance.models import ComplianceReport
from journalport.manuscript.model import CanonicalManuscript
from journalport.manuscript.parser_docx import parse_docx
from journalport.manuscript.parser_latex import parse_latex
from journalport.manuscript.serialization import logical_hash
from journalport.profiles.hashing import resolved_hash
from journalport.profiles.models import ResolvedJournalProfile
from journalport.transform.hashing import canonical_hash, plan_hash
from journalport.transform.models import ActionLog, CandidateManifest, TransformationPlan

from .changes import allowed_change_set, observed_non_scientific_changes
from .compliance_delta import compare_compliance
from .hashing import artifact_hash, verification_report_hash
from .models import ComplianceDelta, VerificationFinding, VerificationReport
from .preservation import preservation_results
from .reconciliation import reconcile

VERIFICATION_VERSION = "1.0.1"


class VerificationInputError(ValueError):
    """The verification evidence cannot be safely interpreted."""


def _parse(path: Path) -> CanonicalManuscript:
    if path.suffix.lower() == ".docx":
        return parse_docx(path)
    if path.suffix.lower() == ".tex":
        return parse_latex(path)
    raise VerificationInputError("candidate format is unsupported for verification")


def _finding(category: str, check: str, passed: bool, message: str) -> VerificationFinding:
    return VerificationFinding(
        "1.0.0",
        f"verify:{category.lower()}:{check}",
        category,
        check,
        "PASS" if passed else "FAIL",
        "INFO" if passed else "ERROR",
        message,
    )


def verify_candidate(
    *,
    source_path: Path,
    candidate_path: Path,
    original_manuscript: CanonicalManuscript,
    profile: ResolvedJournalProfile,
    before_report: ComplianceReport,
    plan: TransformationPlan,
    logs: tuple[ActionLog, ...],
    manifest: CandidateManifest,
    timestamp: str | None = None,
) -> tuple[VerificationReport, ComplianceReport, ComplianceDelta]:
    """Re-read the candidate and independently verify evidence and postconditions."""
    source = source_path.resolve()
    candidate = candidate_path.resolve()
    if source == candidate:
        raise VerificationInputError("source and candidate paths must be isolated")
    source_hash = artifact_hash(source)
    candidate_hash = artifact_hash(candidate)
    candidate_manuscript = _parse(candidate)  # fresh parse is the verification authority
    original_hash = logical_hash(original_manuscript)
    candidate_canonical_hash = logical_hash(candidate_manuscript)
    actual_profile_hash = resolved_hash(profile)
    actual_plan_hash = plan_hash(plan)
    actual_before_hash = report_hash(before_report)
    log_hash = canonical_hash({"schema_version": "1.0.0", "entries": [asdict(x) for x in logs]})

    tamper_checks = {
        "source_hash": "PASS"
        if source_hash == plan.input_artifact_hash == manifest.source_hash
        else "FAIL",
        "candidate_hash": "PASS" if candidate_hash == manifest.candidate_hash else "FAIL",
        "original_canonical_hash": "PASS"
        if original_hash
        == plan.canonical_manuscript_hash
        == before_report.canonical_manuscript_hash
        else "FAIL",
        "profile_hash": "PASS"
        if actual_profile_hash
        == profile.resolved_profile_hash
        == plan.resolved_profile_hash
        == before_report.resolved_profile_hash
        == manifest.profile_hash
        else "FAIL",
        "plan_hash": "PASS"
        if actual_plan_hash == plan.plan_hash == manifest.transformation_plan_hash
        else "FAIL",
        "before_report_hash": "PASS"
        if actual_before_hash == before_report.report_hash == manifest.compliance_report_hash
        else "FAIL",
        "manifest_status": "PASS" if manifest.status == "TRANSFORMED_CANDIDATE" else "FAIL",
    }
    manifest_checks = reconcile(plan, logs, manifest)

    preservation, scientific_changes = preservation_results(
        original_manuscript, candidate_manuscript
    )
    allowed = allowed_change_set(plan)
    observed = observed_non_scientific_changes(source, candidate)
    unexpected = tuple(sorted(set(scientific_changes) | (set(observed) - set(allowed))))

    postconditions: dict[str, str] = {}
    action_by_id = {item.action_id: item for item in plan.actions}
    for log in logs:
        action = action_by_id.get(log.action_id)
        if action is None:
            continue
        if log.execution_status == "APPLIED" and action.operation == "NORMALIZE_OUTPUT_FILENAME":
            expected = action.parameters.get("output_filename")
            postconditions[action.action_id] = (
                "PASS" if isinstance(expected, str) and candidate.name == expected else "FAIL"
            )
        elif log.execution_status == "APPLIED":
            postconditions[action.action_id] = "FAIL"
        else:
            # A pending/manual action made no claim of achieving its requested semantic state.
            # Global preservation is reported once by preservation_checks, not duplicated per action.
            postconditions[action.action_id] = "NOT_APPLICABLE"

    profile_integrity = tamper_checks["profile_hash"] == "PASS"
    if profile_integrity:
        post_report = audit_manuscript(
            candidate_manuscript,
            profile,
            evaluation_timestamp=timestamp or datetime.now(UTC).isoformat(),
        )
    else:
        # A changed profile cannot be used for a meaningful before/after comparison.
        # Preserve the signed pre-transform report as evidence while the tamper status fails closed.
        post_report = before_report
    delta = compare_compliance(before_report, post_report)
    compliance_checks = {
        "profile_unchanged": "PASS" if delta.profile_unchanged and profile_integrity else "FAIL",
        "no_new_blocking_findings": "PASS" if not delta.new_blocking_findings else "FAIL",
        "readiness_not_silently_decreased": "PASS" if not delta.new_blocking_findings else "FAIL",
    }

    integrity_failed = any(value == "FAIL" for value in tamper_checks.values()) or any(
        value == "FAIL" for value in manifest_checks.values()
    )
    preservation_failed = bool(unexpected) or any(
        value == "FAIL" for value in preservation.values()
    )
    postcondition_failed = any(value == "FAIL" for value in postconditions.values())
    compliance_failed = any(value == "FAIL" for value in compliance_checks.values())
    if integrity_failed:
        transform_status = "TAMPER_DETECTED"
    elif preservation_failed or postcondition_failed or compliance_failed:
        transform_status = "VERIFICATION_FAILED"
    else:
        transform_status = "VERIFIED_CANDIDATE"
    manual = tuple(sorted(set(post_report.manual_review_requirements)))
    overall = (
        transform_status
        if transform_status != "VERIFIED_CANDIDATE" or not manual
        else "REQUIRES_MANUAL_REVIEW"
    )
    failures = (
        tuple(
            key
            for group in (
                tamper_checks,
                manifest_checks,
                preservation,
                postconditions,
                compliance_checks,
            )
            for key, value in group.items()
            if value == "FAIL"
        )
        + unexpected
    )
    findings = tuple(
        _finding("PRESERVATION", key, value == "PASS", f"{key}: {value}")
        for key, value in preservation.items()
    ) + tuple(
        _finding("INTEGRITY", key, value == "PASS", f"{key}: {value}")
        for key, value in (tamper_checks | manifest_checks).items()
    )
    root_version = next(
        item.profile_version
        for item in profile.pinned_profiles
        if item.profile_id == profile.root_profile_id
    )
    report = VerificationReport(
        "1.0.0",
        VERIFICATION_VERSION,
        __version__,
        source_hash,
        candidate_hash,
        original_hash,
        candidate_canonical_hash,
        profile.root_profile_id,
        root_version,
        profile.resolved_profile_hash,
        before_report.report_hash,
        post_report.report_hash,
        plan.plan_hash,
        log_hash,
        timestamp or datetime.now(UTC).isoformat(),
        overall,
        transform_status,
        post_report.readiness_status,
        preservation,
        compliance_checks,
        postconditions,
        manifest_checks,
        tamper_checks,
        allowed,
        observed,
        unexpected,
        findings,
        manual,
        failures,
    )
    return (
        replace(report, verification_report_hash=verification_report_hash(report)),
        post_report,
        delta,
    )
