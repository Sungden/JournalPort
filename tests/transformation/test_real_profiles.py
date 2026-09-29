from pathlib import Path

import pytest

from journalport.compliance.engine import audit_manuscript
from journalport.profiles.loader import ProfileRegistry
from journalport.profiles.resolver import resolve_profile
from journalport.transform.hashing import file_hash
from journalport.transform.planner import create_plan
from tests.compliance.factories import manuscript

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(
    "slug",
    ("nature-communications", "nature-computational-science", "nature-machine-intelligence"),
)
def test_real_profiles_create_only_explicit_manual_actions(slug: str, tmp_path: Path) -> None:
    artifact = tmp_path / f"{slug}.tex"
    artifact.write_text("synthetic source", encoding="utf-8")
    source = manuscript()
    source.source["sha256"] = file_hash(artifact)
    registry = ProfileRegistry.from_directory(ROOT / "journal_profiles")
    ids = (
        "publisher:nature-portfolio",
        f"journal:{slug}",
        f"article-type:{slug}/article",
    )
    profile = resolve_profile(registry, *ids, {item: "1.1.0" for item in ids})
    report = audit_manuscript(source, profile, evaluation_timestamp="2026-09-29T00:00:00Z")
    plan = create_plan(source, profile, report, artifact, created_at="2026-09-29T00:00:00Z")
    assert plan.automatic_action_count == 0
    assert plan.approval_required_action_count == report.summary["unknown"]
    assert all(item.transformation_status == "UNSUPPORTED" for item in plan.actions)
    assert plan.plan_status == "APPROVAL_REQUIRED"
