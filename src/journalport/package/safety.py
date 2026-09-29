"""Portable relative-path and output confinement checks."""

from __future__ import annotations

import re
from pathlib import Path, PurePosixPath

SAFE_COMPONENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._ -]*$")


class UnsafePackagePath(ValueError):
    pass


def validate_relative_path(value: str) -> PurePosixPath:
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise UnsafePackagePath("package path must be relative and traversal-free")
    if any(not SAFE_COMPONENT.fullmatch(part) or ":" in part for part in path.parts):
        raise UnsafePackagePath("package path contains an unsafe component")
    return path


def confined_path(root: Path, relative: str) -> Path:
    portable = validate_relative_path(relative)
    resolved_root = root.resolve()
    target = resolved_root.joinpath(*portable.parts).resolve()
    if resolved_root not in target.parents:
        raise UnsafePackagePath("package output escapes its root")
    return target
