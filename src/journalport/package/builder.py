"""Package builder: copies only planned artifacts and writes deterministic metadata."""

from __future__ import annotations

import json
import shutil
import zipfile
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

from journalport import __version__

from .hashing import file_hash, logical_package_hash, package_plan_hash
from .models import ManifestArtifact, SubmissionManifest, SubmissionPackagePlan
from .safety import confined_path


class PackageBuildBlocked(ValueError):
    pass


def _write_deterministic_zip(root: Path) -> Path:
    target = root.parent / "submission_package.zip"
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(item for item in root.rglob("*") if item.is_file()):
            info = zipfile.ZipInfo(path.relative_to(root).as_posix(), (1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(
                info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9
            )
    return target


def build_package(
    plan: SubmissionPackagePlan,
    output_root: Path,
    *,
    created_at: str | None = None,
    create_zip: bool = True,
) -> tuple[SubmissionManifest, Path | None]:
    if package_plan_hash(plan) != plan.plan_hash:
        raise PackageBuildBlocked("package plan hash mismatch")
    if plan.plan_status == "PACKAGE_BUILD_BLOCKED":
        raise PackageBuildBlocked("known required artifacts are missing")
    root = output_root.resolve()
    if root.exists() and any(root.iterdir()):
        raise PackageBuildBlocked("package output directory must be empty")
    root.mkdir(parents=True, exist_ok=True)
    manifest_artifacts: list[ManifestArtifact] = []
    seen_ids: set[str] = set()
    seen_paths: set[str] = set()
    for artifact in plan.artifacts:
        if artifact.artifact_id in seen_ids or artifact.target_relative_path in seen_paths:
            raise PackageBuildBlocked("duplicate artifact identity or target path")
        seen_ids.add(artifact.artifact_id)
        seen_paths.add(artifact.target_relative_path)
        source = Path(artifact.source_path).resolve()
        if source.is_symlink() or not source.is_file():
            raise PackageBuildBlocked("artifact source is missing or a symlink")
        if file_hash(source) != artifact.origin_hash:
            raise PackageBuildBlocked("artifact changed after package planning")
        target = confined_path(root, artifact.target_relative_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        manifest_artifacts.append(
            ManifestArtifact(
                artifact.artifact_id,
                artifact.artifact_type,
                artifact.target_relative_path,
                file_hash(target),
                target.stat().st_size,
                target.suffix.lower(),
                artifact.origin_type,
                artifact.origin_hash,
                artifact.origin_object_ids,
                artifact.requirement_status,
                artifact.validation_result,
                artifact.manual_review_status,
                None,
            )
        )
    for artifact_id, artifact_type, source_path, target_relative in (
        (
            "artifact:verification-report",
            "OTHER_REQUIRED_FILE",
            Path(plan.verification_report_path),
            "metadata/verification_report.json",
        ),
        (
            "artifact:compliance-report",
            "OTHER_REQUIRED_FILE",
            Path(plan.compliance_report_path),
            "metadata/post_transform_compliance_report.json",
        ),
    ):
        target = confined_path(root, target_relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source_path, target)
        manifest_artifacts.append(
            ManifestArtifact(
                artifact_id,
                artifact_type,
                target_relative,
                file_hash(target),
                target.stat().st_size,
                ".json",
                "JOURNALPORT_DERIVED_EVIDENCE",
                file_hash(source_path),
                (),
                "REQUIRED",
                "PASS",
                "NOT_REQUIRED",
                "JournalPort",
            )
        )
    manifest = SubmissionManifest(
        "1.0.0",
        plan.package_id,
        __version__,
        plan.target_journal,
        plan.article_type,
        plan.profile_id,
        plan.profile_version,
        plan.resolved_profile_hash,
        plan.candidate_hash,
        plan.verification_report_hash,
        plan.compliance_report_hash,
        tuple(manifest_artifacts),
        plan.missing_requirements,
        plan.conditional_requirements,
        plan.unknown_requirements,
        plan.manual_actions,
        created_at or datetime.now(UTC).isoformat(),
    )
    manifest = replace(manifest, logical_package_hash=logical_package_hash(manifest))
    (root / "submission_manifest.json").write_text(
        json.dumps(manifest.to_dict(), ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    file_lines = "\n".join(
        f"- `{item.relative_path}` — {item.artifact_type}" for item in manifest.artifacts
    )
    manual_lines = "\n".join(f"- `{item}`" for item in manifest.manual_review_requirements)
    (root / "PACKAGE_INDEX.md").write_text(
        f"# Submission package\n\nTarget journal: {plan.target_journal}\n\n"
        f"Article type: {plan.article_type}\n\nProfile: {plan.profile_id} {plan.profile_version}\n\n"
        "Candidate verification: VERIFIED_CANDIDATE\n\n"
        f"Logical package hash: `{manifest.logical_package_hash}`\n\n## Files\n\n{file_lines}\n\n"
        f"## Manual review\n\n{manual_lines or '- None'}\n\n"
        "Verify with `journalport package verify <package-directory>`.\n",
        encoding="utf-8",
    )
    zip_path = _write_deterministic_zip(root) if create_zip else None
    return manifest, zip_path
