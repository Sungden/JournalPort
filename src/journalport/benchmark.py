"""Reproduce the frozen guideline-extraction benchmark summary."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from journalport import __version__


def default_snapshot() -> Path:
    installed = (
        Path(__file__).resolve().parent / "data" / "benchmark" / "guideline_extraction_results.json"
    )
    checkout = Path("benchmark/guideline_extraction_results.json")
    return checkout if checkout.is_file() else installed


def reproduce_guideline_extraction(snapshot: Path | None = None) -> dict[str, Any]:
    """Load and arithmetically verify the frozen three-journal benchmark snapshot."""
    value: dict[str, Any] = json.loads((snapshot or default_snapshot()).read_text(encoding="utf-8"))
    journals = value["journals"]
    matches = sum(item["verified_matches"] for item in journals.values())
    ground_truth = sum(item["verified_ground_truth"] for item in journals.values())
    recall = matches / ground_truth
    precision = value["aggregate"]["supported_candidate_precision"]
    f1 = 2 * precision * recall / (precision + recall)
    if abs(recall - value["aggregate"]["verified_rule_recall"]) > 1e-9:
        raise ValueError("benchmark recall does not reproduce")
    if abs(f1 - value["aggregate"]["f1"]) > 1e-9:
        raise ValueError("benchmark F1 does not reproduce")
    return value | {"journalport_version_verified_with": __version__}
