"""Independent package integrity and readiness verification."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from journalport.compliance.models import ComplianceReport
from journalport.profiles.hashing import resolved_hash
from journalport.profiles.models import ResolvedJournalProfile
from journalport.verify.hashing import verification_report_hash
from journalport.verify.models import VerificationReport

from .hashing import file_hash, logical_package_hash
from .models import PackageReadinessReport, SubmissionManifest, manifest_from_dict
from .safety import UnsafePackagePath, confined_path, validate_relative_path

KNOWN_GENERATED = {
    "submission_manifest.json",
    "PACKAGE_INDEX.md",
    "package_readiness_report.json",
    "package_readiness_report.html",
}


def verify_package(
    root: Path,
    *,
    profile: ResolvedJournalProfile,
    verification_report: VerificationReport,
    compliance_report: ComplianceReport,
    timestamp: str | None = None,
) -> tuple[SubmissionManifest, PackageReadinessReport]:
    root = root.resolve()
    manifest_path = root / "submission_manifest.json"
    manifest = manifest_from_dict(json.loads(manifest_path.read_text(encoding="utf-8")))
    integrity: dict[str, str] = {
        "manifest_logical_hash": "PASS"
        if logical_package_hash(manifest) == manifest.logical_package_hash
        else "FAIL",
        "profile_hash": "PASS"
        if resolved_hash(profile) == manifest.resolved_profile_hash == profile.resolved_profile_hash
        else "FAIL",
        "verification_report_hash": "PASS"
        if verification_report_hash(verification_report)
        == verification_report.verification_report_hash
        == manifest.verification_report_hash
        else "FAIL",
        "compliance_report_hash": "PASS"
        if compliance_report.report_hash == manifest.compliance_report_hash
        else "FAIL",
    }
    declared: set[str] = set()
    ids: set[str] = set()
    format_checks: dict[str, str] = {}
    candidate_match = False
    for artifact in manifest.artifacts:
        try:
            validate_relative_path(artifact.relative_path)
            path = confined_path(root, artifact.relative_path)
            safe = not path.is_symlink()
        except UnsafePackagePath:
            path = root / "__unsafe__"
            safe = False
        exists = safe and path.is_file()
        matches = (
            exists
            and file_hash(path) == artifact.file_hash
            and path.stat().st_size == artifact.file_size
        )
        integrity[f"artifact:{artifact.artifact_id}"] = "PASS" if matches else "FAIL"
        format_checks[artifact.artifact_id] = (
            "PASS"
            if exists and (not artifact.format or path.suffix.lower() == artifact.format)
            else "FAIL"
        )
        if artifact.artifact_type == "MAIN_MANUSCRIPT" and matches:
            candidate_match = artifact.file_hash == manifest.candidate_hash
        declared.add(artifact.relative_path)
        if artifact.artifact_id in ids:
            integrity["duplicate_artifact_identity"] = "FAIL"
        ids.add(artifact.artifact_id)
    integrity.setdefault("duplicate_artifact_identity", "PASS")
    integrity["candidate_hash"] = "PASS" if candidate_match else "FAIL"
    actual = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() and not path.is_symlink()
    }
    extras = actual - declared - KNOWN_GENERATED
    integrity["no_undeclared_files"] = "PASS" if not extras else "FAIL"
    integrity["no_symlinks"] = (
        "PASS" if not any(path.is_symlink() for path in root.rglob("*")) else "FAIL"
    )

    known_required = sum(item.requirement_status == "REQUIRED" for item in manifest.artifacts)
    present_required = sum(
        item.requirement_status == "REQUIRED"
        and integrity.get(f"artifact:{item.artifact_id}") == "PASS"
        for item in manifest.artifacts
    )
    integrity_failed = any(value == "FAIL" for value in integrity.values()) or any(
        value == "FAIL" for value in format_checks.values()
    )
    candidate_status = verification_report.transformation_verification_status
    if candidate_status != "VERIFIED_CANDIDATE":
        final = "PACKAGE_BLOCKED"
    elif integrity_failed:
        final = "PACKAGE_VERIFICATION_FAILED"
    elif (
        manifest.missing_requirements
        or profile.status == "VERIFIED"
        and compliance_report.readiness_status
        in {
            "BLOCKED",
            "EVALUATION_FAILED",
        }
    ):
        final = "PACKAGE_BLOCKED"
    elif (
        manifest.unknown_requirements
        or manifest.conditional_requirements
        or profile.status != "VERIFIED"
    ):
        final = "PACKAGE_REQUIRES_MANUAL_REVIEW"
    elif verification_report.manual_review_requirements:
        final = "PACKAGE_READY_WITH_WARNINGS"
    else:
        final = "PACKAGE_READY"
    completeness = "COMPLETE" if not manifest.missing_requirements else "INCOMPLETE"
    report = PackageReadinessReport(
        "1.0.0",
        manifest.package_id,
        candidate_status,
        compliance_report.readiness_status,
        completeness,
        profile.status,
        known_required,
        present_required,
        manifest.missing_requirements,
        manifest.unknown_requirements,
        manifest.conditional_requirements,
        format_checks,
        integrity,
        manifest.manual_review_requirements,
        final,
        manifest.logical_package_hash,
        timestamp or datetime.now(UTC).isoformat(),
    )
    return manifest, report
