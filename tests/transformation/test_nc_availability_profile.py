from pathlib import Path

from journalport.cli import _resolve_profile_version
from journalport.profiles.document_format import resolve_document_format
from journalport.profiles.loader import ProfileRegistry


def test_current_availability_is_conditional_verified_executable() -> None:
    root = Path(__file__).resolve().parents[2] / "journal_profiles"
    registry = ProfileRegistry.from_directory(root)
    profile = _resolve_profile_version(root, "nature-communications", "article", "1.3.2")
    target = resolve_document_format(
        registry,
        profile,
        journal="nature-communications",
        article_type="article",
        submission_stage="REVISION",
    )
    field = next(item for item in target.fields if item.rule_id == "availability.placement")
    assert field.status == "VERIFIED"
    assert field.classification == "VERIFIED_EXECUTABLE"
    assert field.operation == "ORDER_CONDITIONAL_SECTIONS"
    assert field.value["data_availability_standalone_placement"] == "NOT_SPECIFIED"
    assert field.value["conditional_order"] == [
        "Data availability",
        "Code availability",
        "References",
    ]
    assert field.value["applicability_status"] == "AUTHOR_CONFIRMATION_REQUIRED"
    for rule in profile.effective_rules:
        if rule.rule_id in {
            "statements.data_availability.required",
            "statements.code_availability.required",
        }:
            assert rule.status == "VERIFIED"
            assert rule.applicability_mode == "CONDITIONAL"
