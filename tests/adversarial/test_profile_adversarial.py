from __future__ import annotations

import json
from pathlib import Path

import pytest

from journalport.manuscript.parser_docx import DocxParseError, DocxResourceLimits, parse_docx
from journalport.profiles.conflicts import conflict_report
from journalport.profiles.loader import ProfileLoadError, ProfileRegistry
from journalport.profiles.models import ProfileRef
from journalport.profiles.resolver import ProfileResolutionError, resolve_profile
from tests.docx_fixture_factory import build_docx
from tests.profile.factories import profile, rule


def test_article_type_override_and_publisher_journal_collision() -> None:
    publisher = profile("publisher:test", "PUBLISHER", (rule("abstract.max_words", 250),))
    journal = profile(
        "journal:test",
        "JOURNAL",
        (rule("abstract.max_words", 200, override=True),),
        (ProfileRef(publisher.profile_id, "1.0.0"),),
    )
    article = profile(
        "article-type:test/article",
        "ARTICLE_TYPE",
        (rule("abstract.max_words", 150, override=True),),
        (ProfileRef(journal.profile_id, "1.0.0"),),
    )
    registry = ProfileRegistry()
    for item in (publisher, journal, article):
        registry.add(item)
    resolved = resolve_profile(
        registry,
        publisher.profile_id,
        journal.profile_id,
        article.profile_id,
        {item.profile_id: item.profile_version for item in (publisher, journal, article)},
    )
    assert resolved.effective_rules[0].value == 150
    assert len(resolved.resolution_trace[0].candidates) == 3


def test_unexpected_extension_and_missing_pin_are_rejected(tmp_path: Path) -> None:
    source = tmp_path / "profile.py"
    source.write_text("raise RuntimeError('must not execute')", encoding="utf-8")
    from journalport.profiles.loader import load_profile

    with pytest.raises(ProfileLoadError, match="JSON profiles only"):
        load_profile(source)

    registry = ProfileRegistry()
    article = profile("article-type:test/article", "ARTICLE_TYPE")
    registry.add(article)
    with pytest.raises(ProfileResolutionError, match="missing pinned version"):
        resolve_profile(registry, "publisher:test", "journal:test", article.profile_id, {})


def test_conflict_report_is_structured() -> None:
    report = conflict_report(())
    assert json.dumps(report, sort_keys=True)
    assert report == {"schema_version": "1.0.0", "status": "CLEAR", "conflicts": []}


def test_docx_resource_limits_reject_member_count_and_xml_size(tmp_path: Path) -> None:
    source = build_docx(tmp_path / "limits.docx")
    with pytest.raises(DocxParseError, match="member count"):
        parse_docx(source, limits=DocxResourceLimits(max_zip_members=1))
    with pytest.raises(DocxParseError, match="XML part exceeds"):
        parse_docx(source, limits=DocxResourceLimits(max_xml_bytes=10))
