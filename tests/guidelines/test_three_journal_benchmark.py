from pathlib import Path

import pytest

from journalport.guidelines.evidence import segment_evidence
from journalport.guidelines.extraction import DeterministicEvidenceExtractor
from journalport.guidelines.reviewer import detect_conflicts, review_rules
from journalport.guidelines.workflow import load_snapshots
from journalport.profiles.loader import ProfileRegistry

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(
    "slug",
    ("nature-communications", "nature-computational-science", "nature-machine-intelligence"),
)
def test_blind_extraction_against_curated_verified_subset(slug: str) -> None:
    snapshots = load_snapshots(ROOT / f"tests/fixtures/guidelines/{slug}.json")
    evidence = tuple(unit for item in snapshots for unit in segment_evidence(item))
    extractor = DeterministicEvidenceExtractor()
    runs = [extractor.extract_requirements(evidence) for _ in range(3)]
    assert runs[0] == runs[1] == runs[2]
    rules = runs[0]
    registry = ProfileRegistry.from_directory(ROOT / "journal_profiles")
    curated = registry.get(f"article-type:{slug}/article", "1.1.0")
    all_curated = {item.rule_id: item for item in curated.rules}
    verified = {key: item for key, item in all_curated.items() if item.status == "VERIFIED"}
    proposed = {item.proposed_rule_id: item for item in rules}
    comparable = [item for item in rules if item.proposed_rule_id in all_curated]
    assert comparable
    assert all(
        all_curated[item.proposed_rule_id].value == item.value
        and all_curated[item.proposed_rule_id].operator == item.operator
        and all_curated[item.proposed_rule_id].target == item.target
        for item in comparable
    )
    matched_verified = set(proposed) & set(verified)
    assert len(matched_verified) / len(verified) >= 0.75
    conflicts = detect_conflicts(rules)
    reviews = review_rules(rules, evidence, conflicts)
    assert not conflicts
    assert all(item.review_status == "SUPPORTED" for item in reviews)
    assert all(item.evidence_ids for item in rules)
    assert not [item for item in rules if item.proposed_rule_id not in all_curated]
