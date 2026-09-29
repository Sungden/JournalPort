from __future__ import annotations

from dataclasses import replace

from journalport.manuscript.model import CanonicalManuscript, Section, SourceLocator, TextBlock
from journalport.profiles.loader import ProfileRegistry
from journalport.profiles.models import ProfileRule
from journalport.profiles.resolver import resolve_profile
from tests.profile.factories import hierarchy, rule


def manuscript(*, abstract_words: int = 3, data: str | None = "Available.") -> CanonicalManuscript:
    locator = SourceLocator("synthetic", "PARSED", "fixture.json")
    abstract = Section(
        "sec:abstract",
        "Abstract",
        1,
        locator,
        [TextBlock("p:abstract", " ".join(["word"] * abstract_words), locator)],
    )
    return CanonicalManuscript(
        "manuscript:synthetic",
        {"sha256": "sha256:" + "a" * 64},
        {
            "title": "A deterministic title",
            "article_type": "Article",
            "cover_letter": True,
        },
        abstract=[abstract],
        main_body=[
            Section(
                "sec:introduction",
                "Introduction",
                1,
                locator,
                [TextBlock("p:introduction", "Synthetic main text.", locator)],
            )
        ],
        statements={
            "acknowledgements": None,
            "funding": None,
            "author_contributions": "A.B. wrote the manuscript.",
            "competing_interests": "None.",
            "ethics": None,
            "consent": None,
            "data_availability": data,
            "code_availability": None,
        },
    )


def active_rule(
    rule_id: str = "abstract.max_words",
    value: object = 5,
    *,
    operator: str = "LTE",
    status: str = "VERIFIED",
    critical: bool = True,
) -> ProfileRule:
    base = rule(rule_id, value, status=status, override=True)
    return replace(
        base,
        operator=operator,
        applicability_mode="ALWAYS",
        critical_for_readiness=critical,
        evaluation_scope="ABSTRACT_TEXT",
    )


def resolved_with(profile_rule: ProfileRule):
    profiles = hierarchy(journal_rule=profile_rule)
    registry = ProfileRegistry()
    for item in profiles:
        registry.add(item)
    return resolve_profile(
        registry,
        "publisher:test",
        "journal:test",
        "article-type:test/article",
        {item.profile_id: item.profile_version for item in profiles},
    )
