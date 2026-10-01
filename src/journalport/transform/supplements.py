"""Explicit local supplementary artifacts with identity-preserving packaging."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from .hashing import file_hash


@dataclass(frozen=True)
class SupplementArtifact:
    filename: str
    type: str
    relationship: str
    source_hash: str
    target_name: str
    packaging_role: str = "SUPPLEMENTARY_INFORMATION"


def supplement_inventory(paths: tuple[Path, ...]) -> tuple[SupplementArtifact, ...]:
    if len(paths) > 1:
        raise ValueError("combined supplement content requires author-provided single file")
    artifacts = []
    for path in paths:
        if path.is_symlink() or not path.is_file() or path.suffix.lower() not in {".docx", ".pdf"}:
            raise ValueError("unsupported or unsafe supplementary artifact")
        artifacts.append(
            SupplementArtifact(
                str(path.resolve()),
                path.suffix.lower()[1:],
                "EXPLICIT_AUTHOR_INPUT",
                file_hash(path),
                "Supplementary_Information" + path.suffix.lower(),
            )
        )
    return tuple(artifacts)


def package_supplements(
    artifacts: tuple[SupplementArtifact, ...], output: Path
) -> list[dict[str, str]]:
    entries = []
    for artifact in artifacts:
        source = Path(artifact.filename)
        if file_hash(source) != artifact.source_hash:
            raise ValueError("supplement source changed after planning")
        destination = output / artifact.target_name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        if destination.read_bytes() != source.read_bytes():
            raise ValueError("supplement identity verification failed")
        entries.append(
            {
                "filename": artifact.target_name,
                "sha256": artifact.source_hash,
                "packaging_role": artifact.packaging_role,
            }
        )
    return entries
