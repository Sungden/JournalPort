"""Thin, host-neutral helpers for JournalPort skill scripts."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from collections.abc import Iterable
from pathlib import Path

SKILL_VERSION = "1.0.0"


def _hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def artifacts(paths: Iterable[Path]) -> list[dict[str, str]]:
    values: list[dict[str, str]] = []
    for path in paths:
        if path.is_file():
            values.append({"path": str(path.resolve()), "sha256": _hash(path)})
        elif path.is_dir():
            values.extend(artifacts(sorted(item for item in path.rglob("*") if item.is_file())))
    return values


def run_cli(args: list[str]) -> subprocess.CompletedProcess[str]:
    executable = shutil.which("journalport")
    command = (
        [executable, *args] if executable else [sys.executable, "-m", "journalport.cli", *args]
    )
    return subprocess.run(command, check=False, capture_output=True, text=True)


def write_record(
    path: Path,
    *,
    skill_id: str,
    inputs: Iterable[Path],
    outputs: Iterable[Path],
    commands: list[list[str]],
    final_status: str,
    manual_review_items: list[str] | None = None,
    profile_hash: str | None = None,
) -> None:
    from journalport import __version__

    value = {
        "schema_version": "1.0.0",
        "skill_id": skill_id,
        "skill_version": SKILL_VERSION,
        "journalport_version": __version__,
        "input_artifacts": artifacts(inputs),
        "profile_hash": profile_hash,
        "called_commands": commands,
        "generated_artifacts": artifacts(outputs),
        "final_status": final_status,
        "manual_review_items": manual_review_items or [],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def fail(result: subprocess.CompletedProcess[str]) -> None:
    message = result.stderr.strip() or result.stdout.strip() or "JournalPort command failed"
    raise SystemExit(message)


def ensure_draft_destination(output: Path, production_profiles: Path) -> None:
    destination = output.resolve()
    production = production_profiles.resolve()
    if destination == production or production in destination.parents:
        raise SystemExit("draft output must not be journal_profiles or one of its descendants")
