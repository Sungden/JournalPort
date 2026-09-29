"""Conflict report serialization."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from .models import ProfileConflict


def conflict_report(conflicts: tuple[ProfileConflict, ...]) -> dict[str, object]:
    return {
        "schema_version": "1.0.0",
        "status": "CONFLICTED" if conflicts else "CLEAR",
        "conflicts": [asdict(item) for item in conflicts],
    }


def write_conflict_report(path: str | Path, conflicts: tuple[ProfileConflict, ...]) -> None:
    Path(path).write_text(
        json.dumps(conflict_report(conflicts), ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
