"""Profile-driven artifact requirement extraction without journal-specific branches."""

from __future__ import annotations

from journalport.profiles.models import ProfileRule, ResolvedJournalProfile

from .models import ArtifactRequirement

TARGET_ARTIFACT_MAP = {
    "cover_letter": "COVER_LETTER",
    "title_page": "TITLE_PAGE",
    "title_page_requirements": "TITLE_PAGE",
    "figure_files": "FIGURE",
    "supplementary_information": "SUPPLEMENTARY_INFORMATION",
    "reporting_checklist": "REPORTING_CHECKLIST",
    "data_availability_document": "DATA_AVAILABILITY_DOCUMENT",
    "code_availability_document": "CODE_AVAILABILITY_DOCUMENT",
    "ethics_document": "ETHICS_DOCUMENT",
    "consent_document": "CONSENT_DOCUMENT",
}


def _artifact_type(rule: ProfileRule) -> str | None:
    normalized = rule.target.replace(".", "_")
    if normalized in TARGET_ARTIFACT_MAP:
        return TARGET_ARTIFACT_MAP[normalized]
    for key, value in TARGET_ARTIFACT_MAP.items():
        if key in normalized:
            return value
    return None


def _status(rule: ProfileRule) -> str:
    if rule.status in {"UNKNOWN", "PARTIAL", "STALE", "CONFLICTED"}:
        return "UNKNOWN"
    if rule.applicability_mode == "CONDITIONAL":
        return "CONDITIONAL"
    if rule.value is True or str(rule.value).upper() in {"REQUIRED", "TRUE"}:
        return "REQUIRED"
    if str(rule.value).upper() in {"OPTIONAL", "ALLOWED", "FALSE"}:
        return "OPTIONAL"
    return "UNKNOWN"


def requirements_from_profile(profile: ResolvedJournalProfile) -> tuple[ArtifactRequirement, ...]:
    requirements = [
        ArtifactRequirement(
            "requirement:main-manuscript",
            "MAIN_MANUSCRIPT",
            "REQUIRED",
            None,
            (".docx", ".tex"),
            1,
            1,
            None,
            True,
            False,
            "system.main_manuscript",
            (),
            True,
        )
    ]
    for rule in profile.effective_rules:
        artifact_type = _artifact_type(rule)
        if artifact_type is None:
            continue
        status = _status(rule)
        requirements.append(
            ArtifactRequirement(
                f"requirement:{rule.rule_id}",
                artifact_type,
                status,
                rule.applicability if status in {"CONDITIONAL", "UNKNOWN"} else None,
                (),
                1 if status == "REQUIRED" else 0,
                None,
                None,
                bool(rule.value is True),
                status != "REQUIRED",
                rule.rule_id,
                rule.provenance,
                rule.critical_for_readiness,
            )
        )
    return tuple(requirements)
