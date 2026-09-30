"""LLM-free, offline, read-only compliance engine."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import replace
from datetime import UTC, datetime

from journalport import __version__
from journalport.manuscript.model import CanonicalManuscript
from journalport.manuscript.serialization import logical_hash
from journalport.profiles.hashing import resolved_hash
from journalport.profiles.models import ProfileRule, ResolvedJournalProfile

from .findings import action_for, finding_id, message_for
from .hashing import report_hash
from .integrity import integrity_findings
from .models import ComplianceFinding, ComplianceReport, Coverage, Selection
from .operators import OPERATORS, evaluate_operator
from .readiness import derive_readiness
from .selectors import select_target

ENGINE_VERSION = "1.0.0"
DISCLAIMER = (
    "Submission readiness covers only machine-readable requirements in the active Journal Profile; "
    "it does not imply editorial acceptance or complete publisher-requirement coverage."
)
SUPPORTED_SCOPES = {
    "METADATA_ARTICLE_TYPE",
    "TITLE_TEXT",
    "ABSTRACT_TEXT",
    "MAIN_BODY_EXCLUDING_ABSTRACT_METHODS_REFERENCES_FIGURE_LEGENDS_TABLES_SUPPLEMENT",
    "FIGURE_AND_TABLE_OBJECTS",
    "METADATA_COVER_LETTER_PRESENT",
    "STATEMENT_AUTHOR_CONTRIBUTIONS",
    "STATEMENT_COMPETING_INTERESTS",
    "STATEMENT_DATA_AVAILABILITY",
}


def _origin(profile: ResolvedJournalProfile, rule: ProfileRule) -> str:
    trace = next(item for item in profile.resolution_trace if item.rule_id == rule.rule_id)
    return trace.selected_profile_id or profile.root_profile_id


def _status_before_evaluation(rule: ProfileRule) -> tuple[str, str] | None:
    if rule.target == "cover_letter":
        return "NOT_APPLICABLE", "submission artifact is evaluated at package layer"
    if rule.status in {"UNKNOWN", "PARTIAL", "STALE", "CONFLICTED"}:
        return "UNKNOWN", f"rule status is {rule.status}"
    if rule.status == "NOT_APPLICABLE" or rule.applicability_mode == "NOT_APPLICABLE":
        return "NOT_APPLICABLE", "profile marks the rule not applicable"
    if rule.applicability_mode == "UNKNOWN":
        return "UNKNOWN", "formal applicability is UNKNOWN"
    if rule.applicability_mode == "CONDITIONAL":
        return "UNKNOWN", "conditional applicability could not be deterministically established"
    if not rule.machine_checkable:
        return "UNKNOWN", "profile marks the rule as manual review"
    if rule.evaluation_scope not in SUPPORTED_SCOPES:
        return "EVALUATION_ERROR", f"unsupported or unspecified scope {rule.evaluation_scope}"
    return None


def _finding(
    rule: ProfileRule,
    profile: ResolvedJournalProfile,
    selection: Selection,
    status: str,
    reason: str = "",
) -> ComplianceFinding:
    origin = _origin(profile, rule)
    context = f"{selection.method}:{status}:{selection.value!r}"
    return ComplianceFinding(
        "1.0.0",
        finding_id(rule.rule_id, selection.object_ids, profile.resolved_profile_hash, context),
        rule.rule_id,
        rule.rule_version,
        origin,
        profile.resolved_profile_hash,
        status,
        rule.severity,
        selection.target_type,
        selection.object_ids,
        selection.value,
        rule.value,
        rule.operator,
        rule.unit,
        message_for(status, rule, selection.value, reason),
        action_for(status),
        rule.machine_checkable,
        rule.autofix_class,
        False,
        rule.status,
        rule.critical_for_readiness,
        rule.provenance,
        f"resolution_trace:{rule.rule_id}",
        selection.method,
        ENGINE_VERSION,
    )


def _evaluate_rule(
    manuscript: CanonicalManuscript,
    profile: ResolvedJournalProfile,
    rule: ProfileRule,
) -> ComplianceFinding:
    pre = _status_before_evaluation(rule)
    if pre is not None:
        status, reason = pre
        return _finding(
            rule, profile, Selection(rule.target, (), None, "policy-gate"), status, reason
        )
    if rule.operator not in OPERATORS:
        return _finding(
            rule,
            profile,
            Selection(rule.target, (), None, "operator-registry"),
            "EVALUATION_ERROR",
            f"unsupported operator {rule.operator}",
        )
    if rule.target == "article_type":
        target_article_type = profile.root_profile_id.rsplit("/", 1)[-1].replace("-", " ").title()
        selection = Selection(
            "article_type",
            (),
            target_article_type,
            "resolved_submission_context.article_type",
        )
    else:
        selection = select_target(manuscript, rule)
    if selection.error:
        return _finding(rule, profile, selection, "EVALUATION_ERROR", selection.error)
    try:
        passed = evaluate_operator(rule.operator, selection.value, rule.value)
    except (TypeError, ValueError, KeyError, re.error) as exc:
        return _finding(rule, profile, selection, "EVALUATION_ERROR", type(exc).__name__)
    status = "PASS" if passed else ("BLOCKED" if rule.severity == "BLOCKING" else "WARNING")
    return _finding(rule, profile, selection, status)


def audit_manuscript(
    manuscript: CanonicalManuscript,
    profile: ResolvedJournalProfile,
    *,
    evaluation_timestamp: str | None = None,
) -> ComplianceReport:
    before = logical_hash(manuscript)
    if resolved_hash(profile) != profile.resolved_profile_hash:
        raise ValueError("resolved profile hash mismatch")
    rule_findings = tuple(
        _evaluate_rule(manuscript, profile, rule)
        for rule in sorted(profile.effective_rules, key=lambda item: item.rule_id)
    )
    findings = rule_findings + integrity_findings(manuscript, profile.resolved_profile_hash)
    after = logical_hash(manuscript)
    if before != after:
        raise RuntimeError("M3 invariant violated: manuscript was modified")
    counts = Counter(item.status for item in findings)
    unsupported = sum(
        item.status == "EVALUATION_ERROR" and item.evaluation_method == "operator-registry"
        for item in findings
    )
    coverage = Coverage(
        len(profile.effective_rules),
        sum(x.status == "VERIFIED" for x in profile.effective_rules),
        sum(x.status == "PARTIAL" for x in profile.effective_rules),
        sum(x.status == "UNKNOWN" for x in profile.effective_rules),
        sum(x.machine_checkable for x in profile.effective_rules),
        sum(x.status in {"PASS", "WARNING", "BLOCKED"} for x in findings),
        sum(x.status == "UNKNOWN" for x in findings),
        unsupported,
    )
    timestamp = evaluation_timestamp or datetime.now(UTC).isoformat()
    root_version = next(
        item.profile_version
        for item in profile.pinned_profiles
        if item.profile_id == profile.root_profile_id
    )
    report = ComplianceReport(
        "2.0.0",
        __version__,
        ENGINE_VERSION,
        manuscript.source.get("sha256", before),
        before,
        profile.root_profile_id,
        root_version,
        profile.resolved_profile_hash,
        timestamp,
        derive_readiness(findings, profile.status),
        {
            name.lower(): counts.get(name, 0)
            for name in (
                "PASS",
                "WARNING",
                "BLOCKED",
                "UNKNOWN",
                "NOT_APPLICABLE",
                "EVALUATION_ERROR",
            )
        },
        coverage,
        findings,
        (f"Resolved profile status is {profile.status}.",),
        tuple(item.object_id for item in manuscript.unsupported_content),
        tuple(item.message for item in findings if item.status in {"UNKNOWN", "EVALUATION_ERROR"}),
        DISCLAIMER,
    )
    return replace(report, report_hash=report_hash(report))
