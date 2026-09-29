"""Draft lifecycle and offline replay orchestration."""

from __future__ import annotations

import json
from dataclasses import asdict, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from journalport import __version__
from journalport.profiles.models import Profile

from .diff import compare_to_curated
from .evidence import segment_evidence
from .extraction import DeterministicEvidenceExtractor
from .hashing import candidate_profile_hash, canonical_hash
from .models import CandidateProfile, DiscoveredSource, ExtractionRun
from .retrieval import RetrievalSnapshot
from .reviewer import REVIEWER_VERSION, detect_conflicts, review_rules

PROMPT_VERSION = "guideline-extraction-v1"


def load_snapshots(path: Path) -> tuple[RetrievalSnapshot, ...]:
    value = json.loads(path.read_text(encoding="utf-8"))
    snapshots: list[RetrievalSnapshot] = []
    for item in value["snapshots"]:
        source = DiscoveredSource(**item["source"])
        snapshots.append(RetrievalSnapshot(**(item | {"source": source})))
    return tuple(snapshots)


def _validate(schema_name: str, value: Any, schema_root: Path) -> None:
    schema = json.loads((schema_root / schema_name).read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(json.loads(json.dumps(value)))


def refresh_draft(
    *,
    journal: str,
    article_type: str,
    snapshots: tuple[RetrievalSnapshot, ...],
    output_root: Path,
    curated_profile: Profile | None = None,
    extractor: DeterministicEvidenceExtractor | None = None,
    timestamp: str | None = None,
    schema_root: Path = Path("schemas"),
) -> Path:
    now = timestamp or datetime.now(UTC).isoformat()
    engine = extractor or DeterministicEvidenceExtractor()
    evidence = tuple(unit for snapshot in snapshots for unit in segment_evidence(snapshot))
    rules = engine.extract_requirements(evidence)
    conflicts = detect_conflicts(rules)
    profile = CandidateProfile(
        "1.0.0",
        f"draft:{journal}/{article_type}",
        journal,
        article_type,
        "DRAFT",
        rules,
        conflicts,
        tuple(
            snapshot.source.source_id
            for snapshot in snapshots
            if snapshot.retrieval_status != "RETRIEVED"
        ),
    )
    profile = replace(profile, candidate_profile_hash=candidate_profile_hash(profile))
    reviews = review_rules(rules, evidence, conflicts)
    diffs = () if curated_profile is None else compare_to_curated(rules, curated_profile)
    run_id = (
        "run:"
        + canonical_hash(
            [
                journal,
                article_type,
                [item.content_hash for item in snapshots],
                profile.candidate_profile_hash,
            ]
        ).split(":", 1)[1][:24]
    )
    run = ExtractionRun(
        "1.0.0",
        run_id,
        __version__,
        engine.version,
        PROMPT_VERSION,
        engine.provider,
        engine.model,
        {"temperature": 0, "max_repair_attempts": 2},
        tuple(item.source.source_url for item in snapshots),
        tuple(item.content_hash for item in snapshots),
        tuple(item.retrieved_at for item in snapshots),
        profile.candidate_profile_hash,
        REVIEWER_VERSION,
        now,
    )
    run_dir = output_root / journal / run_id.removeprefix("run:")
    if run_dir.exists():
        raise FileExistsError("immutable draft run already exists")
    run_dir.mkdir(parents=True)
    outputs = {
        "retrieved_sources.json": {
            "schema_version": "1.0.0",
            "sources": [asdict(item) for item in snapshots],
        },
        "evidence_units.json": {
            "schema_version": "1.0.0",
            "evidence_units": [asdict(item) for item in evidence],
        },
        "candidate_profile.json": profile.to_dict(),
        "profile_diff.json": {
            "schema_version": "1.0.0",
            "items": [asdict(item) for item in diffs],
        },
        "profile_review_queue.json": {
            "schema_version": "1.0.0",
            "items": [asdict(item) for item in reviews],
        },
        "extraction_run.json": asdict(run),
    }
    for snapshot in snapshots:
        _validate("source_record.schema.json", asdict(snapshot.source), schema_root)
    for unit in evidence:
        _validate("evidence_unit.schema.json", asdict(unit), schema_root)
    for rule in rules:
        _validate("candidate_rule.schema.json", asdict(rule), schema_root)
    schema_names = {
        "candidate_profile.json": "candidate_profile.schema.json",
        "profile_diff.json": "profile_diff.schema.json",
        "profile_review_queue.json": "profile_review_queue.schema.json",
        "extraction_run.json": "extraction_run.schema.json",
    }
    for name, value in outputs.items():
        schema_name = schema_names.get(name)
        if schema_name:
            _validate(schema_name, value, schema_root)
        (run_dir / name).write_text(
            json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
    return run_dir
