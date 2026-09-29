from dataclasses import replace

from journalport.compliance.engine import audit_manuscript
from journalport.profiles.hashing import resolved_hash
from tests.compliance.factories import active_rule, manuscript, resolved_with


def test_conflicted_and_stale_profiles_never_ready() -> None:
    profile = resolved_with(active_rule())
    conflicted_profile = replace(profile, status="CONFLICTED", resolved_profile_hash="")
    conflicted_profile = replace(
        conflicted_profile, resolved_profile_hash=resolved_hash(conflicted_profile)
    )
    stale_profile = replace(profile, status="STALE", resolved_profile_hash="")
    stale_profile = replace(stale_profile, resolved_profile_hash=resolved_hash(stale_profile))
    conflicted = audit_manuscript(manuscript(), conflicted_profile)
    stale = audit_manuscript(manuscript(), stale_profile)
    assert conflicted.readiness_status == "PROFILE_NOT_VERIFIABLE"
    assert stale.readiness_status == "PROFILE_NOT_VERIFIABLE"
