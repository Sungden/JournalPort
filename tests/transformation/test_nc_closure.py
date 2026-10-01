from __future__ import annotations

import copy
import json
import zipfile
from dataclasses import replace
from pathlib import Path

import pytest

from journalport.cli import _resolve_profile_version
from journalport.profiles.document_format import resolve_document_format
from journalport.profiles.loader import ProfileRegistry
from journalport.transform.closure import (
    closure_status,
    finalize_visual_validation,
    formatting_coverage,
)
from journalport.transform.format_engine import (
    apply_format_transformations,
    verify_format_transformations,
)
from journalport.transform.full_docx import read_document
from journalport.transform.full_format import m12_from_full_plan, plan_full_format
from journalport.transform.hashing import file_hash
from journalport.transform.references import (
    CitationRenderer,
    ReferenceRenderer,
    ReferenceStyleTarget,
    inspect_linkage,
    parse_reference,
    reference_nodes,
)
from tests.transformation.test_nc_full_format import ROOT, corpus, target


def style() -> ReferenceStyleTarget:
    value = json.loads(
        (ROOT / "journal_profiles/journals/nature-communications/article-1.3.1.json").read_text(
            encoding="utf-8"
        )
    )
    return ReferenceStyleTarget(
        **next(
            field["target_state"]
            for field in value["transformation_targets"]
            if field["rule_id"] == "references.style"
        )
    )


@pytest.mark.parametrize("doi,pages", [("", "1024"), (" https://doi.org/10.0000/synthetic", "1–3")])
def test_nature_identity_roundtrip(doi: str, pages: str) -> None:
    reference = parse_reference(
        f"1. Example, A.; Example, B. Synthetic measurement. Nature 12, {pages} (2026).{doi}"
    )
    rendered = ReferenceRenderer(style()).render(reference)
    reparsed = parse_reference(rendered)
    assert reference.parse_confidence == "HIGH"
    assert reparsed.identity() == reference.identity()
    assert reparsed.reference_id == reference.reference_id
    assert " & " in rendered


@pytest.mark.parametrize(
    "raw",
    [
        "malformed reference",
        "1. Example et al. Ambiguous. Nature 12, 1–3 (2026).",
        "1. Example, A. Preprint at https://arxiv.org/abs/2601.01234 (2026). arXiv:2601.01234",
        "1. Example, A. Synthetic book Ch. 3 (Synthetic Press, Synthetic City, 2026).",
    ],
)
def test_unsupported_references_fail_closed(raw: str) -> None:
    reference = parse_reference(raw)
    assert reference.parse_confidence != "HIGH"
    with pytest.raises(ValueError):
        ReferenceRenderer(style()).render(reference)


def test_long_authors_preserved_not_elided() -> None:
    authors = "; ".join(f"Example, {initial}." for initial in "ABCDEF")
    reference = parse_reference(f"1. {authors} Synthetic measurement. Nature 12, 1–3 (2026).")
    assert reference.parse_confidence == "HIGH"
    assert len(reference.authors) == 6
    with pytest.raises(ValueError, match="elided"):
        ReferenceRenderer(style()).render(reference)


def test_doi_url_presentation_preserved_and_issue_blocked() -> None:
    raw = "1. Example, A. Synthetic measurement. Nature 12, 1–3 (2026). http://doi.org/10.0000/synthetic."
    ref = parse_reference(raw)
    assert ReferenceRenderer(style()).render(ref).endswith("http://doi.org/10.0000/synthetic.")
    issue = parse_reference(raw.replace("Nature 12,", "Nature 12(2),"))
    assert issue.parse_confidence == "HIGH"
    with pytest.raises(ValueError, match="issue presentation"):
        ReferenceRenderer(style()).render(issue)


def test_core_reference_render_verify_and_tamper(tmp_path: Path) -> None:
    source = corpus.build_case(tmp_path / "source.docx", 3)
    registry = ProfileRegistry.from_directory(ROOT / "journal_profiles")
    profile = _resolve_profile_version(
        ROOT / "journal_profiles", "nature-communications", "article", "1.3.1"
    )
    resolved = resolve_document_format(
        registry,
        profile,
        journal="nature-communications",
        article_type="article",
        submission_stage="REVISION",
    )
    plan = m12_from_full_plan(plan_full_format(source, resolved))
    assert any(op.operation == "RENDER_REFERENCES" for op in plan.operations)
    result = apply_format_transformations(source, plan, tmp_path / "output")
    verification = verify_format_transformations(source, result, plan)
    assert verification.transformation_verification_status == "VERIFIED_CANDIDATE"
    assert not verification.unexpected_changes
    candidate = Path(result.candidate_path)
    for path in (source, candidate):
        body = read_document(path)[2]
        linked = inspect_linkage(body, ["".join(n.itertext()) for n in reference_nodes(body)])
        assert linked["linkage_confidence"] == "HIGH"
        for occurrence in linked["citations"]:
            assert (
                CitationRenderer.render(occurrence, tuple(linked["references"]))
                == occurrence.raw_marker
            )
    assert file_hash(source) == plan.source_hash
    with zipfile.ZipFile(candidate) as archive:
        parts = {name: archive.read(name) for name in archive.namelist()}
    parts["word/document.xml"] = parts["word/document.xml"].replace(
        b"10.0000/synthetic1", b"10.9999/synthetic1", 1
    )
    corrupted = candidate.parent / "corrupted.docx"
    with zipfile.ZipFile(corrupted, "w") as archive:
        for name, payload in parts.items():
            archive.writestr(name, payload)
    report = verify_format_transformations(
        source,
        replace(result, candidate_path=str(corrupted), candidate_hash=file_hash(corrupted)),
        plan,
    )
    assert report.transformation_verification_status == "VERIFICATION_FAILED"
    assert "references_preserved" in report.failure_reasons


def test_formatting_denominator_excludes_nonformatting(tmp_path: Path) -> None:
    source = corpus.build_case(tmp_path / "source.docx", 1)
    plan = m12_from_full_plan(plan_full_format(source, target()[2]))
    report = formatting_coverage(plan.transfer_matrix, {op.rule_id for op in plan.operations})
    assert report["formatting_target_count"] == 12
    assert report["formatting_target_coverage"] < 100
    assert not any(
        item["closure_critical"]
        for item in report["blockers"]
        if item["category"] == "non-formatting"
    )
    assert any(
        item["closure_critical"] and not item["resolved"]
        for item in report["blockers"]
        if item["rule_id"] == "availability.placement"
    )


def test_closure_all_gates_required() -> None:
    gates = {
        "unresolved_closure_critical_blockers": 0,
        "formatting_target_coverage": 100,
        "content_preservation": "VERIFIED_CANDIDATE",
        "target_format": "FORMAT_TARGET_VERIFIED",
        "render_validation": "RENDER_PASS",
        "visual_validation": "VISUAL_PASS_WITH_NOTES",
        "package_integrity": "PASS",
    }
    assert closure_status(**gates) == "NC_DOCX_CLOSED"
    for key, value in (
        ("unresolved_closure_critical_blockers", 1),
        ("formatting_target_coverage", 99),
        ("content_preservation", "VERIFICATION_FAILED"),
        ("target_format", "FORMAT_TARGET_PARTIAL"),
        ("render_validation", "NOT_AVAILABLE"),
        ("visual_validation", "NOT_PERFORMED"),
        ("package_integrity", "FAIL"),
    ):
        changed = copy.deepcopy(gates)
        changed[key] = value
        assert closure_status(**changed) == "NC_DOCX_NOT_CLOSED"


def test_visual_receipt_without_bound_artifacts_cannot_close(tmp_path: Path) -> None:
    from journalport.transform.full_format import run_full_format

    source = corpus.build_case(tmp_path / "source.docx", 1)
    registry, profile, _ = target()
    output = tmp_path / "output"
    run_full_format(
        source,
        output,
        registry,
        profile,
        journal="nature-communications",
        article_type="article",
        stage="REVISION",
        render_executable=str(tmp_path / "missing.exe"),
    )
    with pytest.raises(ValueError, match="binding"):
        finalize_visual_validation(
            output,
            {
                "status": "VISUAL_PASS",
                "candidate_hash": "sha256:" + "0" * 64,
                "reviewed_pages": [],
                "checks": {},
            },
        )
