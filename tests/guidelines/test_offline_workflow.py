import json
from pathlib import Path

import pytest

from journalport.guidelines.workflow import load_snapshots, refresh_draft
from journalport.profiles.loader import ProfileRegistry

ROOT = Path(__file__).resolve().parents[2]


def test_offline_replay_writes_immutable_draft_without_touching_production(tmp_path: Path) -> None:
    fixture = ROOT / "tests/fixtures/guidelines/nature-communications.json"
    snapshots = load_snapshots(fixture)
    registry = ProfileRegistry.from_directory(ROOT / "journal_profiles")
    curated = registry.get("article-type:nature-communications/article", "1.1.0")
    before = fixture.read_bytes()
    production_before = (
        ROOT / "journal_profiles/journals/nature-communications/article-1.1.0.json"
    ).read_bytes()
    run = refresh_draft(
        journal="nature-communications",
        article_type="article",
        snapshots=snapshots,
        output_root=tmp_path,
        curated_profile=curated,
        timestamp="2026-09-29T00:00:00Z",
        schema_root=ROOT / "schemas",
    )
    assert {item.name for item in run.iterdir()} == {
        "retrieved_sources.json",
        "evidence_units.json",
        "candidate_profile.json",
        "profile_diff.json",
        "profile_review_queue.json",
        "extraction_run.json",
    }
    candidate = json.loads((run / "candidate_profile.json").read_text(encoding="utf-8"))
    assert candidate["status"] == "DRAFT"
    assert candidate["candidate_rules"]
    assert all(item["evidence_ids"] for item in candidate["candidate_rules"])
    assert fixture.read_bytes() == before
    assert (
        ROOT / "journal_profiles/journals/nature-communications/article-1.1.0.json"
    ).read_bytes() == production_before
    with pytest.raises(FileExistsError):
        refresh_draft(
            journal="nature-communications",
            article_type="article",
            snapshots=snapshots,
            output_root=tmp_path,
            timestamp="2026-09-29T00:00:00Z",
            schema_root=ROOT / "schemas",
        )
