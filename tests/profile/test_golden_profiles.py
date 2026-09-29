from __future__ import annotations

import json
from pathlib import Path

import pytest

from journalport.profiles.hashing import resolved_hash
from journalport.profiles.loader import ProfileRegistry
from journalport.profiles.provenance import validate_profile_provenance
from journalport.profiles.resolver import resolve_profile

ROOT = Path(__file__).resolve().parents[2]
PROFILE_ROOT = ROOT / "journal_profiles"
REPORT_ROOT = ROOT / "profile_reports"
ARTICLES = (
    "nature-communications",
    "nature-computational-science",
    "nature-machine-intelligence",
)


@pytest.fixture(scope="module")
def registry() -> ProfileRegistry:
    return ProfileRegistry.from_directory(PROFILE_ROOT)


@pytest.mark.parametrize("slug", ARTICLES)
def test_golden_profile_gate(registry: ProfileRegistry, slug: str) -> None:
    pins = {
        "publisher:nature-portfolio": "1.0.0",
        f"journal:{slug}": "1.0.0",
        f"article-type:{slug}/article": "1.0.0",
    }
    first = resolve_profile(
        registry,
        "publisher:nature-portfolio",
        f"journal:{slug}",
        f"article-type:{slug}/article",
        pins,
    )
    second = resolve_profile(
        registry,
        "publisher:nature-portfolio",
        f"journal:{slug}",
        f"article-type:{slug}/article",
        pins,
    )
    assert first == second
    assert first.resolved_profile_hash == second.resolved_profile_hash
    assert first.resolved_profile_hash == resolved_hash(first)
    assert first.status == "PARTIAL"
    assert first.conflicts == ()
    assert len(first.pinned_profiles) == 3
    for profile_id, version in pins.items():
        assert not validate_profile_provenance(registry.get(profile_id, version))
    assert all(rule.provenance for rule in first.effective_rules if rule.status == "VERIFIED")
    trace = json.loads((REPORT_ROOT / slug / "resolution_trace.json").read_text(encoding="utf-8"))
    conflict = json.loads(
        (REPORT_ROOT / slug / "profile_conflict_report.json").read_text(encoding="utf-8")
    )
    inventory = json.loads(
        (REPORT_ROOT / slug / "source_inventory.json").read_text(encoding="utf-8")
    )
    assert trace["resolved_profile_hash"] == first.resolved_profile_hash
    assert conflict == {"schema_version": "1.0.0", "status": "CLEAR", "conflicts": []}
    assert inventory["profile_id"] == first.root_profile_id


def test_registry_contains_exactly_three_article_profiles(registry: ProfileRegistry) -> None:
    article_profiles = [
        profile for profile in registry._profiles.values() if profile.profile_kind == "ARTICLE_TYPE"
    ]
    assert {profile.profile_id for profile in article_profiles} == {
        f"article-type:{slug}/article" for slug in ARTICLES
    }
