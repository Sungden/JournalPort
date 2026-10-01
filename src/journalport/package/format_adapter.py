"""Package adapter for independently verified M12 format artifacts."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from journalport.transform.format_models import FormatExecutionResult, FormatVerificationReport
from journalport.transform.hashing import file_hash


class FormatPackageBlocked(ValueError):
    """A format result is not eligible for packaging."""


def build_format_package(
    result: FormatExecutionResult,
    verification: FormatVerificationReport,
    output_root: str | Path,
) -> dict[str, Any]:
    if (
        verification.transformation_verification_status != "VERIFIED_CANDIDATE"
        or verification.unexpected_changes
        or verification.failure_reasons
    ):
        raise FormatPackageBlocked("only a clean VERIFIED_CANDIDATE may be packaged")
    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=True)
    candidate_source = Path(result.candidate_path)
    if (
        candidate_source.is_symlink()
        or file_hash(candidate_source) != result.candidate_hash
        or result.candidate_hash != verification.candidate_hash
    ):
        raise FormatPackageBlocked("candidate changed after independent verification")
    candidate = root / "manuscript" / "manuscript_transformed.docx"
    candidate.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(candidate_source, candidate)
    files = [
        {
            "relative_path": "manuscript/manuscript_transformed.docx",
            "artifact_type": "MANUSCRIPT",
            "sha256": file_hash(candidate),
        }
    ]
    result_root = candidate_source.parent
    for artifact in result.artifacts:
        relative = Path(artifact.relative_path)
        if relative.is_absolute() or ".." in relative.parts:
            raise FormatPackageBlocked("unsafe artifact path")
        source = result_root / artifact.relative_path
        if source.is_symlink() or file_hash(source) != artifact.sha256:
            raise FormatPackageBlocked("artifact changed after verification")
        destination = root / "artifacts" / artifact.relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        files.append(
            {
                "relative_path": str(destination.relative_to(root)).replace("\\", "/"),
                "artifact_type": artifact.artifact_type,
                "sha256": file_hash(destination),
            }
        )
    status = (
        "PACKAGE_REQUIRES_MANUAL_REVIEW"
        if verification.remaining_target_requirements
        else "PACKAGE_READY"
    )
    manifest: dict[str, Any] = {
        "schema_version": "1.0.0",
        "candidate_verification_status": "VERIFIED_CANDIDATE",
        "package_status": status,
        "files": files,
        "remaining_target_requirements": list(verification.remaining_target_requirements),
    }
    (root / "format_package_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    return manifest


def verify_format_package(root: str | Path) -> dict[str, Any]:
    package = Path(root)
    manifest_path = package / "format_package_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    failures: list[str] = []
    seen: set[str] = set()
    for item in manifest["files"]:
        relative = item["relative_path"]
        if relative in seen or Path(relative).is_absolute() or ".." in Path(relative).parts:
            failures.append(f"unsafe or duplicate path: {relative}")
            continue
        seen.add(relative)
        path = package / relative
        if not path.is_file() or file_hash(path) != item["sha256"]:
            failures.append(f"hash mismatch: {relative}")
    return {
        "schema_version": "1.0.0",
        "package_integrity": "PASS" if not failures else "FAIL",
        "package_status": manifest["package_status"]
        if not failures
        else "PACKAGE_VERIFICATION_FAILED",
        "failure_reasons": failures,
    }
