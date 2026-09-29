from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime

import pytest

from journalport.profiles.freshness import is_stale
from journalport.profiles.hashing import resolved_hash
from journalport.profiles.loader import ProfileRegistry
from journalport.profiles.models import ProfileRef
from journalport.profiles.resolver import ProfileResolutionError, resolve_profile
from tests.profile.factories import hierarchy, profile, rule, with_parents


def _registry(*profiles):
    registry = ProfileRegistry()
    for item in profiles:
        registry.add(item)
    return registry


def _resolve(registry: ProfileRegistry):
    return resolve_profile(
        registry,
        "publisher:test",
        "journal:test",
        "article-type:test/article",
        {
            "publisher:test": "1.0.0",
            "journal:test": "1.0.0",
            "article-type:test/article": "1.0.0",
        },
    )


def test_explicit_override_has_trace_and_deterministic_hash() -> None:
    profiles = hierarchy(journal_rule=rule("abstract.max_words", 200, override=True))
    first = _resolve(_registry(*profiles))
    second = _resolve(_registry(*reversed(profiles)))
    assert first == second
    assert first.status == "VERIFIED"
    assert first.effective_rules[0].value == 200
    assert first.resolution_trace[0].classification == "VALID_OVERRIDE"
    assert first.resolved_profile_hash == second.resolved_profile_hash
    assert first.resolved_profile_hash == resolved_hash(first)


def test_invalid_override_is_conflicted_not_last_write_wins() -> None:
    profiles = hierarchy(journal_rule=rule("abstract.max_words", 200))
    resolved = _resolve(_registry(*profiles))
    assert resolved.status == "CONFLICTED"
    assert not resolved.effective_rules
    assert resolved.conflicts[0].candidate_values == (250, 200)


def test_equal_precedence_conflict_and_duplicate_are_distinguished() -> None:
    publisher = profile("publisher:test", "PUBLISHER")
    first = profile(
        "journal:test",
        "JOURNAL",
        (rule("title.max_words", 20),),
        (ProfileRef("publisher:test", "1.0.0"),),
    )
    second = profile(
        "journal:test-second",
        "JOURNAL",
        (rule("title.max_words", 25),),
        (ProfileRef("publisher:test", "1.0.0"),),
    )
    article = profile(
        "article-type:test/article",
        "ARTICLE_TYPE",
        (),
        (ProfileRef(first.profile_id, "1.0.0"), ProfileRef(second.profile_id, "1.0.0")),
    )
    registry = _registry(publisher, first, second, article)
    resolved = resolve_profile(
        registry,
        "publisher:test",
        "journal:test",
        article.profile_id,
        {item.profile_id: "1.0.0" for item in (publisher, first, second, article)},
    )
    assert resolved.status == "CONFLICTED"
    assert resolved.resolution_trace[0].classification == "CONFLICT"

    registry_same = _registry(
        publisher, first, replace(second, rules=(rule("title.max_words", 20),)), article
    )
    duplicate = resolve_profile(
        registry_same,
        "publisher:test",
        "journal:test",
        article.profile_id,
        {item.profile_id: "1.0.0" for item in (publisher, first, second, article)},
    )
    assert duplicate.resolution_trace[0].classification == "DUPLICATE"


def test_cycle_detection_blocks_before_precedence_repair() -> None:
    first = profile("publisher:a", "PUBLISHER")
    second = profile("publisher:b", "PUBLISHER")
    first = with_parents(first, (ProfileRef(second.profile_id, "1.0.0"),))
    second = with_parents(second, (ProfileRef(first.profile_id, "1.0.0"),))
    article = profile(
        "article-type:test/article", "ARTICLE_TYPE", (), (ProfileRef(first.profile_id, "1.0.0"),)
    )
    registry = _registry(first, second, article)
    with pytest.raises(ProfileResolutionError, match="inheritance cycle"):
        resolve_profile(
            registry,
            first.profile_id,
            first.profile_id,
            article.profile_id,
            {item.profile_id: "1.0.0" for item in (first, second, article)},
        )


def test_freshness_is_configurable_and_stale_blocks_verified_status() -> None:
    stale = profile(
        "publisher:test", "PUBLISHER", verified_at="2020-01-01T00:00:00Z", freshness_days=30
    )
    assert is_stale(stale, at=datetime(2020, 2, 1, tzinfo=UTC))
    publisher, journal, article = hierarchy()
    stale_publisher = replace(
        publisher, last_verified_at="2020-01-01T00:00:00Z", freshness_window_days=30
    )
    assert _resolve(_registry(stale_publisher, journal, article)).status == "STALE"
