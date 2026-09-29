"""Output confinement and immutable-source safety helpers."""

from __future__ import annotations

import re
from pathlib import Path


class UnsafeOutputPath(ValueError):
    pass


SAFE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,199}$")


def confined_output(root: Path, name: str, source: Path) -> Path:
    if not SAFE_NAME.fullmatch(name) or Path(name).name != name:
        raise UnsafeOutputPath("candidate filename is unsafe")
    if root.exists() and root.is_symlink():
        raise UnsafeOutputPath("output root may not be a symlink")
    resolved_root = root.resolve()
    target = (resolved_root / name).resolve()
    if not target.is_relative_to(resolved_root):
        raise UnsafeOutputPath("candidate path escapes output root")
    if target == source.resolve():
        raise UnsafeOutputPath("in-place transformation is forbidden")
    return target
