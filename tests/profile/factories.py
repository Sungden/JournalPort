from __future__ import annotations

from dataclasses import replace

from journalport.profiles.evidence import evidence_hash
from journalport.profiles.models import (
    EvidenceRecord,
    JournalIdentity,
    Profile,
    ProfileRef,
    ProfileRule,
    ProvenanceRef,
    SourceRecord,
)


def rule(
    rule_id: str,
    value: object,
    *,
    status: str = "VERIFIED",
    override: bool = False,
    provenance: bool = True,
) -> ProfileRule:
    return ProfileRule(
        rule_id=rule_id,
        rule_version="1.0.0",
        category="LIMIT",
        target=rule_id.rsplit(".", 1)[0],
        operator="LTE",
        value=value,  # type: ignore[arg-type]
        unit="words",
        severity="BLOCKING",
        applicability="Article",
        machine_checkable=True,
        autofix_class="AUTHOR_APPROVAL_REQUIRED",
        provenance=(ProvenanceRef("src:test", "ev:test"),) if provenance else (),
        confidence="HIGH" if status == "VERIFIED" else "UNKNOWN",
        status=status,
        override_of=rule_id if override else None,
        override_reason="more specific official instruction" if override else None,
    )


def profile(
    profile_id: str,
    kind: str,
    rules: tuple[ProfileRule, ...] = (),
    parents: tuple[ProfileRef, ...] = (),
    *,
    verified_at: str = "2026-09-29T00:00:00Z",
    freshness_days: int = 365,
) -> Profile:
    text = "Synthetic official evidence for deterministic testing."
    source = SourceRecord(
        "src:test",
        "https://example.org/official",
        "OFFICIAL_JOURNAL_GUIDELINE",
        "2026-09-29T00:00:00Z",
        "Synthetic official source",
        "Example Publisher",
        "sha256:" + "1" * 64,
        "EVIDENCE_EXTRACT",
        False,
        "VERIFIED",
    )
    evidence = EvidenceRecord("ev:test", "src:test", "section:test", text, evidence_hash(text))
    precedence = {"PUBLISHER": 100, "JOURNAL": 200, "ARTICLE_TYPE": 300}[kind]
    journal = (
        None
        if kind == "PUBLISHER"
        else JournalIdentity("Test Journal", "Example Publisher", (), "https://example.org/journal")
    )
    return Profile(
        "2.0.0",
        profile_id,
        profile_id,
        "1.0.0",
        "1.0.0",
        kind,
        precedence,
        parents,
        journal,
        "Article" if kind == "ARTICLE_TYPE" else None,
        (source,),
        (evidence,),
        rules,
        verified_at,
        freshness_days,
        "PARTIAL",
    )


def hierarchy(*, journal_rule: ProfileRule | None = None) -> tuple[Profile, Profile, Profile]:
    publisher = profile("publisher:test", "PUBLISHER", (rule("abstract.max_words", 250),))
    journal_rules = (journal_rule,) if journal_rule else ()
    journal = profile(
        "journal:test",
        "JOURNAL",
        journal_rules,
        (ProfileRef(publisher.profile_id, publisher.profile_version),),
    )
    article = profile(
        "article-type:test/article",
        "ARTICLE_TYPE",
        (),
        (ProfileRef(journal.profile_id, journal.profile_version),),
    )
    return publisher, journal, article


def with_parents(item: Profile, parents: tuple[ProfileRef, ...]) -> Profile:
    return replace(item, parents=parents)
