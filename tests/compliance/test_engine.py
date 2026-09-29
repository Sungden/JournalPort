from __future__ import annotations

from dataclasses import replace

import pytest

from journalport.compliance.engine import audit_manuscript
from journalport.manuscript.serialization import logical_hash
from journalport.profiles.hashing import resolved_hash
from tests.compliance.factories import active_rule, manuscript, resolved_with


def test_pass_block_and_no_mutation() -> None:
    source = manuscript(abstract_words=4)
    before = logical_hash(source)
    passed = audit_manuscript(
        source, resolved_with(active_rule(value=5)), evaluation_timestamp="2026-09-29T00:00:00Z"
    )
    blocked = audit_manuscript(
        source, resolved_with(active_rule(value=3)), evaluation_timestamp="2026-09-29T00:00:00Z"
    )
    assert passed.findings[0].status == "PASS"
    assert blocked.findings[0].status == "BLOCKED"
    assert blocked.readiness_status == "BLOCKED"
    assert logical_hash(source) == before


def test_unknown_is_preserved_and_never_passes() -> None:
    profile = resolved_with(active_rule(status="UNKNOWN"))
    report = audit_manuscript(manuscript(), profile, evaluation_timestamp="2026-09-29T00:00:00Z")
    assert report.findings[0].status == "UNKNOWN"
    assert report.readiness_status == "REQUIRES_MANUAL_REVIEW"


def test_conditional_applicability_is_unknown() -> None:
    conditional = replace(active_rule(), applicability_mode="CONDITIONAL")
    report = audit_manuscript(manuscript(), resolved_with(conditional))
    assert report.findings[0].status == "UNKNOWN"
    assert "conditional applicability" in report.findings[0].message


def test_unsupported_operator_is_explicit() -> None:
    unsupported = active_rule(operator="CUSTOM")
    report = audit_manuscript(manuscript(), resolved_with(unsupported))
    assert report.findings[0].status == "EVALUATION_ERROR"
    assert report.coverage.unsupported_evaluator_rules == 1
    assert report.readiness_status == "EVALUATION_FAILED"


def test_wrong_resolved_hash_and_tampered_trace_fail_closed() -> None:
    profile = resolved_with(active_rule())
    with pytest.raises(ValueError, match="hash mismatch"):
        audit_manuscript(manuscript(), replace(profile, resolved_profile_hash="sha256:" + "0" * 64))
    tampered = replace(profile, resolution_trace=())
    assert resolved_hash(tampered) != profile.resolved_profile_hash
    with pytest.raises(ValueError, match="hash mismatch"):
        audit_manuscript(manuscript(), tampered)


def test_deterministic_findings_and_report_hash_ignore_timestamp() -> None:
    source = manuscript()
    profile = resolved_with(active_rule())
    first = audit_manuscript(source, profile, evaluation_timestamp="2026-09-29T00:00:00Z")
    second = audit_manuscript(source, profile, evaluation_timestamp="2030-01-01T00:00:00Z")
    assert first.findings == second.findings
    assert first.readiness_status == second.readiness_status
    assert first.report_hash == second.report_hash
