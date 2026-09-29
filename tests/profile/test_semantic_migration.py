from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import pytest

from journalport.compliance.engine import audit_manuscript
from journalport.profiles.loader import ProfileRegistry
from journalport.profiles.migration import migrate_profile
from journalport.profiles.resolver import resolve_profile
from tests.compliance.factories import manuscript

ROOT = Path(__file__).resolve().parents[2]
SLUGS = (
    "nature-communications",
    "nature-computational-science",
    "nature-machine-intelligence",
)


def test_migration_is_reproducible_and_all_active_rules_are_explicit() -> None:
    decisions = json.loads(
        (ROOT / "profile_migrations/m2_5_semantic_decisions.json").read_text(encoding="utf-8")
    )
    for old_path in sorted((ROOT / "journal_profiles").rglob("*1.0.0.json")):
        if old_path.name not in {"1.0.0.json", "journal-1.0.0.json", "article-1.0.0.json"}:
            continue
        old = json.loads(old_path.read_text(encoding="utf-8"))
        expected, _report = migrate_profile(old, decisions)
        new_path = old_path.with_name(old_path.name.replace("1.0.0", "1.1.0"))
        actual = json.loads(new_path.read_text(encoding="utf-8"))
        assert actual == expected
        for rule in actual["rules"]:
            assert {
                "applicability_mode",
                "critical_for_readiness",
                "machine_checkable",
                "severity",
                "autofix_class",
                "evaluation_scope",
            } <= rule.keys()


@pytest.mark.parametrize("slug", SLUGS)
def test_real_profile_verified_machine_rules_are_all_evaluated(slug: str) -> None:
    registry = ProfileRegistry.from_directory(ROOT / "journal_profiles")
    ids = (
        "publisher:nature-portfolio",
        f"journal:{slug}",
        f"article-type:{slug}/article",
    )
    pins = {profile_id: "1.1.0" for profile_id in ids}
    first = resolve_profile(registry, *ids, pins)
    second = resolve_profile(registry, *ids, pins)
    assert first == second
    report = audit_manuscript(manuscript(), first, evaluation_timestamp="2026-09-29T00:00:00Z")
    verified_machine = {
        rule.rule_id
        for rule in first.effective_rules
        if rule.status == "VERIFIED" and rule.machine_checkable
    }
    evaluated = {
        finding.rule_id
        for finding in report.findings
        if finding.rule_id in verified_machine and finding.status in {"PASS", "WARNING", "BLOCKED"}
    }
    assert evaluated == verified_machine
    assert report.coverage.unsupported_evaluator_rules == 0
    assert report.readiness_status == "REQUIRES_MANUAL_REVIEW"
    assert Counter(finding.status for finding in report.findings)["PASS"] > 0
