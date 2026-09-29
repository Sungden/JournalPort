"""Deterministic submission package planning."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

from journalport import __version__
from journalport.compliance.hashing import report_hash
from journalport.compliance.models import ComplianceReport
from journalport.profiles.hashing import resolved_hash
from journalport.profiles.models import ResolvedJournalProfile
from journalport.verify.hashing import verification_report_hash
from journalport.verify.models import VerificationReport

from .discovery import discover_explicit
from .hashing import canonical_hash, file_hash, package_plan_hash
from .models import PlannedArtifact, SubmissionPackagePlan
from .requirements import requirements_from_profile

TARGET_DIRS = {
    "MAIN_MANUSCRIPT": "manuscript",
    "TITLE_PAGE": "title_page",
    "COVER_LETTER": "declarations",
    "FIGURE": "figures",
    "TABLE": "tables",
    "SUPPLEMENTARY_INFORMATION": "supplementary",
    "SUPPLEMENTARY_DATA": "supplementary",
    "REPORTING_CHECKLIST": "checklists",
}


class PackagePlanningBlocked(ValueError):
    pass


def _planned(
    path: Path, artifact_type: str, index: int, requirement_status: str
) -> PlannedArtifact:
    digest = file_hash(path)
    directory = TARGET_DIRS.get(artifact_type, "other")
    return PlannedArtifact(
        f"artifact:{canonical_hash([artifact_type, digest, index]).split(':', 1)[1][:20]}",
        artifact_type,
        str(path.resolve()),
        f"{directory}/{path.name}",
        "TRANSFORMED_CANDIDATE" if artifact_type == "MAIN_MANUSCRIPT" else "AUTHOR_SUPPLIED",
        digest,
        (),
        requirement_status,
        "PASS",
        "REQUIRED" if requirement_status in {"UNKNOWN", "CONDITIONAL"} else "NOT_REQUIRED",
    )


def create_package_plan(
    *,
    candidate: Path,
    verification_report_path: Path,
    verification_report: VerificationReport,
    compliance_report_path: Path,
    compliance_report: ComplianceReport,
    profile: ResolvedJournalProfile,
    auxiliary_paths: tuple[Path, ...] = (),
    created_at: str | None = None,
) -> SubmissionPackagePlan:
    candidate = candidate.resolve()
    candidate_hash = file_hash(candidate)
    if (
        verification_report_hash(verification_report)
        != verification_report.verification_report_hash
    ):
        raise PackagePlanningBlocked("verification report hash mismatch")
    if verification_report.transformation_verification_status != "VERIFIED_CANDIDATE":
        raise PackagePlanningBlocked("candidate is not independently verified")
    if candidate_hash != verification_report.candidate_artifact_hash:
        raise PackagePlanningBlocked("candidate hash does not match verification report")
    if resolved_hash(profile) != profile.resolved_profile_hash:
        raise PackagePlanningBlocked("resolved profile hash mismatch")
    if profile.resolved_profile_hash != verification_report.resolved_profile_hash:
        raise PackagePlanningBlocked("profile does not match verification report")
    if report_hash(compliance_report) != compliance_report.report_hash:
        raise PackagePlanningBlocked("post-transform compliance report hash mismatch")
    if compliance_report.report_hash != verification_report.compliance_report_after_hash:
        raise PackagePlanningBlocked("compliance report does not match verification report")

    requirements = requirements_from_profile(profile)
    discovered = discover_explicit(auxiliary_paths)
    status_by_type = {item.artifact_type: item.requirement_status for item in requirements}
    artifacts = [_planned(candidate, "MAIN_MANUSCRIPT", 0, "REQUIRED")]
    artifacts.extend(
        _planned(path, artifact_type, index + 1, status_by_type.get(artifact_type, "OPTIONAL"))
        for index, (path, artifact_type) in enumerate(discovered)
    )
    counts: dict[str, int] = {}
    for artifact in artifacts:
        counts[artifact.artifact_type] = counts.get(artifact.artifact_type, 0) + 1
    missing = tuple(
        item.requirement_id
        for item in requirements
        if item.requirement_status == "REQUIRED"
        and counts.get(item.artifact_type, 0) < item.min_count
    )
    conditional = tuple(
        item.requirement_id for item in requirements if item.requirement_status == "CONDITIONAL"
    )
    unknown = tuple(
        item.requirement_id for item in requirements if item.requirement_status == "UNKNOWN"
    )
    manual = tuple(sorted(set(missing + conditional + unknown)))
    status = "PACKAGE_BUILD_BLOCKED" if missing else "READY_TO_BUILD"
    profile_version = next(
        item.profile_version
        for item in profile.pinned_profiles
        if item.profile_id == profile.root_profile_id
    )
    package_id = (
        "package:"
        + canonical_hash(
            [
                candidate_hash,
                profile.resolved_profile_hash,
                verification_report.verification_report_hash,
            ]
        ).split(":", 1)[1][:24]
    )
    plan = SubmissionPackagePlan(
        "1.0.0",
        "1.0.0",
        __version__,
        package_id,
        profile.root_profile_id.removeprefix("article-type:").rsplit("/", 1)[0],
        profile.root_profile_id.rsplit("/", 1)[-1],
        profile.root_profile_id,
        profile_version,
        profile.resolved_profile_hash,
        str(candidate),
        candidate_hash,
        str(verification_report_path.resolve()),
        verification_report.verification_report_hash,
        str(compliance_report_path.resolve()),
        compliance_report.report_hash,
        requirements,
        tuple(artifacts),
        missing,
        conditional,
        unknown,
        manual,
        status,
        created_at or datetime.now(UTC).isoformat(),
    )
    return replace(plan, plan_hash=package_plan_hash(plan))
