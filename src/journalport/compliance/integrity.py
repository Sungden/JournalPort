"""Profile-independent canonical integrity checks for references, figures, and tables."""

from __future__ import annotations

from journalport.manuscript.model import CanonicalManuscript

from .findings import finding_id
from .models import ComplianceFinding


def _finding(
    manuscript: CanonicalManuscript,
    profile_hash: str,
    rule_id: str,
    status: str,
    object_ids: tuple[str, ...],
    message: str,
    *,
    critical: bool = False,
) -> ComplianceFinding:
    return ComplianceFinding(
        "1.0.0",
        finding_id(rule_id, object_ids, profile_hash, message),
        rule_id,
        "1.0.0",
        "engine:canonical-integrity",
        profile_hash,
        status,
        "BLOCKING" if critical else "WARNING",
        "canonical_integrity",
        object_ids,
        None,
        None,
        "CUSTOM",
        None,
        message,
        "Correct the canonical source inconsistency manually; M3 does not modify it.",
        True,
        "FORBIDDEN_AUTOMATIC",
        False,
        "VERIFIED",
        critical,
        (),
        "engine:canonical-integrity",
        "canonical-integrity@1.0.0",
        "1.0.0",
    )


def integrity_findings(
    manuscript: CanonicalManuscript, profile_hash: str
) -> tuple[ComplianceFinding, ...]:
    findings: list[ComplianceFinding] = []
    reference_ids = {item.object_id for item in manuscript.references}
    cited_ids = {
        reference_id for item in manuscript.citations for reference_id in item.reference_ids
    }
    missing = tuple(sorted(cited_ids - reference_ids))
    uncited = tuple(sorted(reference_ids - cited_ids))
    if missing:
        findings.append(
            _finding(
                manuscript,
                profile_hash,
                "integrity.citation_missing_reference",
                "BLOCKED",
                missing,
                f"Citations reference missing bibliography objects: {missing!r}.",
                critical=True,
            )
        )
    if uncited:
        findings.append(
            _finding(
                manuscript,
                profile_hash,
                "integrity.uncited_reference",
                "WARNING",
                uncited,
                f"Bibliography objects are not cited: {uncited!r}.",
            )
        )
    raw_groups: dict[str, list[str]] = {}
    doi_groups: dict[str, list[str]] = {}
    for item in manuscript.references:
        raw_groups.setdefault(" ".join(item.raw_text.casefold().split()), []).append(item.object_id)
        if item.doi:
            doi_groups.setdefault(item.doi.casefold().removeprefix("https://doi.org/"), []).append(
                item.object_id
            )
    for ids in raw_groups.values():
        if len(ids) > 1:
            findings.append(
                _finding(
                    manuscript,
                    profile_hash,
                    "integrity.duplicate_reference",
                    "WARNING",
                    tuple(sorted(ids)),
                    "Duplicate normalized bibliography entries were detected.",
                )
            )
    for ids in doi_groups.values():
        if len(ids) > 1:
            findings.append(
                _finding(
                    manuscript,
                    profile_hash,
                    "integrity.duplicate_doi",
                    "WARNING",
                    tuple(sorted(ids)),
                    "Duplicate DOI values were detected.",
                )
            )
    for kind, assets in (("figure", manuscript.figures), ("table", manuscript.tables)):
        for asset in assets:
            if kind == "figure" and not asset.file_refs:
                findings.append(
                    _finding(
                        manuscript,
                        profile_hash,
                        "integrity.figure_missing_asset",
                        "BLOCKED",
                        (asset.object_id,),
                        "A figure has no referenced asset file.",
                        critical=True,
                    )
                )
            if not asset.legend.strip():
                findings.append(
                    _finding(
                        manuscript,
                        profile_hash,
                        f"integrity.{kind}_missing_caption",
                        "WARNING",
                        (asset.object_id,),
                        f"A {kind} has no caption.",
                    )
                )
    return tuple(sorted(findings, key=lambda item: item.finding_id))
