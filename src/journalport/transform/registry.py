"""Closed finding-to-transformation registry."""

from __future__ import annotations

from journalport.compliance.models import ComplianceFinding


def transformation_for(finding: ComplianceFinding) -> tuple[str, str, str]:
    if finding.rule_id == "file.name.normalized" and finding.rule_status == "VERIFIED":
        return "NORMALIZE_OUTPUT_FILENAME", "SAFE_AUTOMATIC", "SUPPORTED"
    if finding.autofix_class == "FORBIDDEN_AUTOMATIC":
        return "MANUAL_SCIENTIFIC_CHANGE", "FORBIDDEN_AUTOMATIC", "UNSUPPORTED"
    if finding.rule_id.startswith("statements."):
        return "MANUAL_CONTENT_REQUIRED", "AUTHOR_APPROVAL_REQUIRED", "UNSUPPORTED"
    if finding.rule_id.startswith(("abstract.", "title.", "main_text.")):
        return "MANUAL_TEXT_REVISION", "AUTHOR_APPROVAL_REQUIRED", "UNSUPPORTED"
    return "MANUAL_ACTION_REQUIRED", "AUTHOR_APPROVAL_REQUIRED", "UNSUPPORTED"
