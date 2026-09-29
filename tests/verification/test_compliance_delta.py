from dataclasses import replace

from journalport.compliance.engine import audit_manuscript
from journalport.compliance.hashing import report_hash
from journalport.verify.compliance_delta import compare_compliance
from tests.compliance.factories import active_rule, manuscript, resolved_with


def test_new_blocker_and_resolved_finding_are_classified() -> None:
    profile = resolved_with(active_rule(value=5))
    before = audit_manuscript(manuscript(abstract_words=4), profile)
    after = audit_manuscript(manuscript(abstract_words=6), profile)
    delta = compare_compliance(before, after)
    assert delta.items[0].change == "WORSENED_FINDING"
    assert delta.new_blocking_findings
    reverse = compare_compliance(after, before)
    assert reverse.items[0].change == "RESOLVED_FINDING"
    assert not reverse.new_blocking_findings


def test_profile_change_is_explicit() -> None:
    profile = resolved_with(active_rule(value=5))
    report = audit_manuscript(manuscript(), profile)
    changed = replace(report, resolved_profile_hash="sha256:" + "0" * 64, report_hash="")
    changed = replace(changed, report_hash=report_hash(changed))
    assert not compare_compliance(report, changed).profile_unchanged
