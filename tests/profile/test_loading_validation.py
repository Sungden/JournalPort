from __future__ import annotations

import json
from dataclasses import asdict, replace
from pathlib import Path

import pytest

from journalport.profiles.loader import ProfileLoadError, load_profile
from journalport.profiles.provenance import validate_profile_provenance
from journalport.profiles.validation import validate_profile
from tests.profile.factories import profile, rule


def _write(path: Path, value: object) -> Path:
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def test_valid_profile_schema_and_provenance_load(tmp_path: Path) -> None:
    source = profile("publisher:test", "PUBLISHER", (rule("abstract.max_words", 250),))
    loaded = load_profile(_write(tmp_path / "profile.json", asdict(source)))
    assert loaded == source
    assert not validate_profile_provenance(loaded)


def test_missing_provenance_unknown_source_and_bad_hash_are_rejected(tmp_path: Path) -> None:
    missing = profile(
        "publisher:test", "PUBLISHER", (rule("abstract.max_words", 250, provenance=False),)
    )
    with pytest.raises(ProfileLoadError, match="MISSING_PROVENANCE"):
        load_profile(_write(tmp_path / "missing.json", asdict(missing)))

    value = asdict(profile("publisher:test", "PUBLISHER", (rule("abstract.max_words", 250),)))
    value["rules"][0]["provenance"][0]["source_id"] = "src:absent"
    with pytest.raises(ProfileLoadError, match="UNKNOWN_SOURCE"):
        load_profile(_write(tmp_path / "unknown.json", value))

    value = asdict(profile("publisher:test", "PUBLISHER", (rule("abstract.max_words", 250),)))
    value["evidence"][0]["evidence_hash"] = "sha256:" + "0" * 64
    with pytest.raises(ProfileLoadError, match="EVIDENCE_HASH_MISMATCH"):
        load_profile(_write(tmp_path / "hash.json", value))


def test_schema_version_mismatch_and_oversized_payload_are_rejected(tmp_path: Path) -> None:
    value = asdict(profile("publisher:test", "PUBLISHER"))
    value["schema_version"] = "999.0.0"
    with pytest.raises(ProfileLoadError, match="schema validation failed"):
        load_profile(_write(tmp_path / "version.json", value))
    valid = _write(tmp_path / "large.json", asdict(profile("publisher:test", "PUBLISHER")))
    with pytest.raises(ProfileLoadError, match="size limit"):
        load_profile(valid, max_bytes=10)


def test_duplicate_rule_and_invalid_status_are_rejected(tmp_path: Path) -> None:
    duplicate = profile(
        "publisher:test",
        "PUBLISHER",
        (rule("abstract.max_words", 250), rule("abstract.max_words", 250)),
    )
    with pytest.raises(ProfileLoadError, match="DUPLICATE_RULE"):
        load_profile(_write(tmp_path / "duplicate.json", asdict(duplicate)))
    inflated = replace(
        profile(
            "publisher:test",
            "PUBLISHER",
            (rule("abstract.max_words", "UNKNOWN", status="UNKNOWN"),),
        ),
        status="VERIFIED",
    )
    with pytest.raises(ProfileLoadError, match="INFLATED_PROFILE_STATUS"):
        load_profile(_write(tmp_path / "inflated.json", asdict(inflated)))


def test_stale_profile_is_explicit_nonblocking_validation_issue() -> None:
    stale = profile(
        "publisher:test",
        "PUBLISHER",
        verified_at="2020-01-01T00:00:00Z",
        freshness_days=30,
    )
    issues = validate_profile(stale)
    assert [(item.code, item.blocking) for item in issues] == [("STALE_PROFILE", False)]
