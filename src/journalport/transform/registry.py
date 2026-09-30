"""Closed finding-to-transformation registry."""

from __future__ import annotations

from journalport.compliance.models import ComplianceFinding


def transformation_for(finding: ComplianceFinding) -> tuple[str, str, str]:
    if finding.rule_id == "file.name.normalized" and finding.rule_status == "VERIFIED":
        return "NORMALIZE_OUTPUT_FILENAME", "SAFE_AUTOMATIC", "SUPPORTED"
    if finding.autofix_class == "FORBIDDEN_AUTOMATIC":
        return "MANUAL_SCIENTIFIC_CHANGE", "FORBIDDEN_AUTOMATIC", "UNSUPPORTED"
    executable_finding = (
        finding.status in {"BLOCKED", "WARNING"} and finding.rule_status == "VERIFIED"
    )
    if finding.rule_id == "abstract.max_words" and executable_finding:
        return "REPLACE_ABSTRACT", "AUTHOR_APPROVAL_REQUIRED", "SUPPORTED"
    if (
        executable_finding
        and finding.rule_id.startswith("statements.")
        and finding.rule_id.rsplit(".", 1)[0]
        in {
            "statements.author_contributions",
            "statements.competing_interests",
            "statements.data_availability",
            "statements.code_availability",
        }
    ):
        return "INSERT_REQUIRED_SECTION", "AUTHOR_APPROVAL_REQUIRED", "SUPPORTED"
    if finding.rule_id.startswith(("title.", "main_text.")):
        return "MANUAL_TEXT_REVISION", "AUTHOR_APPROVAL_REQUIRED", "UNSUPPORTED"
    return "MANUAL_ACTION_REQUIRED", "AUTHOR_APPROVAL_REQUIRED", "UNSUPPORTED"
