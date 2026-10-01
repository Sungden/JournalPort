from __future__ import annotations

import importlib.util
import json
from dataclasses import replace
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from journalport.cli import _resolve_profile_version
from journalport.manuscript.parser_docx import parse_docx
from journalport.profiles.document_format import resolve_document_format
from journalport.profiles.loader import ProfileRegistry
from journalport.transform.format_engine import (
    apply_format_transformations,
    verify_format_transformations,
)
from journalport.transform.full_docx import read_document
from journalport.transform.full_format import m12_from_full_plan, plan_full_format, run_full_format
from journalport.transform.hashing import file_hash
from journalport.transform.references import (
    expand_numeric_marker,
    parse_reference,
    render_reference,
)
from journalport.transform.structure import W, semantic_roles
from journalport.transform.supplements import package_supplements, supplement_inventory
from journalport.verify.assets import figure_technical_metadata
from journalport.verify.render import LibreOfficeRenderBackend

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "nc_corpus", ROOT / "examples/public-synthetic/nc_docx_corpus.py"
)
assert spec and spec.loader
corpus = importlib.util.module_from_spec(spec)
spec.loader.exec_module(corpus)


def target(stage: str = "REVISION"):
    registry = ProfileRegistry.from_directory(ROOT / "journal_profiles")
    profile = _resolve_profile_version(
        ROOT / "journal_profiles", "nature-communications", "article", "1.3.0"
    )
    return (
        registry,
        profile,
        resolve_document_format(
            registry,
            profile,
            journal="nature-communications",
            article_type="article",
            submission_stage=stage,
        ),
    )


@pytest.mark.parametrize("case", (1, 2, 3, 4))
def test_synthetic_structure_layout_preservation_and_reports(tmp_path: Path, case: int) -> None:
    source = corpus.build_case(tmp_path / "source.docx", case)
    original = source.read_bytes()
    registry, profile, resolved = target()
    plan = plan_full_format(source, resolved)
    m12 = m12_from_full_plan(plan)
    result = apply_format_transformations(source, m12, tmp_path / "direct")
    verification = verify_format_transformations(source, result, m12)
    assert verification.transformation_verification_status == "VERIFIED_CANDIDATE", (
        verification.failure_reasons
    )
    assert result.source_hash != result.candidate_hash
    assert source.read_bytes() == original
    assert all(verification.preservation_checks.values())
    assert read_document(source)[1].nsmap == read_document(Path(result.candidate_path))[1].nsmap
    summary = run_full_format(
        source,
        tmp_path / "output",
        registry,
        profile,
        journal="nature-communications",
        article_type="article",
        stage="REVISION",
    )
    assert summary["status"] == "VERIFIED_CANDIDATE"
    assert summary["coverage"]["full_format_verified"] is False
    for name in (
        "full_format_plan.json",
        "verification_report.json",
        "render_validation_report.json",
        "format_coverage_report.json",
        "package_integrity_report.json",
        "disclosure_ledger.json",
    ):
        assert (tmp_path / "output/metadata" / name).is_file()
    for name, schema in (
        ("full_format_plan.json", "full_format_plan.schema.json"),
        ("format_coverage_report.json", "format_coverage_report.schema.json"),
        ("render_validation_report.json", "render_validation_report.schema.json"),
    ):
        Draft202012Validator(json.loads((ROOT / "schemas" / schema).read_text())).validate(
            json.loads((tmp_path / "output/metadata" / name).read_text())
        )
    serialized = (tmp_path / "output/metadata/full_format_plan.json").read_text()
    assert "42 samples" not in serialized
    assert summary["package_status"] == "PACKAGE_REQUIRES_MANUAL_REVIEW"


def test_complex_fields_and_tracked_changes_fail_closed(tmp_path: Path) -> None:
    source = corpus.build_case(tmp_path / "complex.docx", 5)
    _, _, resolved = target()
    plan = plan_full_format(source, resolved)
    assert plan["m12_plan"]["operations"] == [] or plan["m12_plan"]["operations"] == ()
    assert plan["citation_linkage"]["live_fields"] is True
    assert plan["citation_linkage"]["linkage_confidence"] == "LOW"
    assert any(
        item["reason"] == "unsupported_document_objects" for item in plan["manual_requirements"]
    )


def test_unknown_and_stale_targets_cannot_execute(tmp_path: Path) -> None:
    source = corpus.build_case(tmp_path / "source.docx", 1)
    _, _, resolved = target()
    for state in ("UNKNOWN", "PARTIAL", "STALE", "CONFLICTED"):
        changed = replace(
            resolved,
            fields=tuple(
                replace(field, status=state, classification=state) for field in resolved.fields
            ),
        )
        assert not plan_full_format(source, changed)["m12_plan"]["operations"]


def test_numeric_linkage_ranges_and_identity_renderer() -> None:
    assert expand_numeric_marker("[1, 3–5]") == (1, 3, 4, 5)
    with pytest.raises(ValueError):
        expand_numeric_marker("[5–1]")
    raw = "1. Example, A.; Example, B. Synthetic measurement. Example Journal 12, 1–3 (2026). https://doi.org/10.0000/synthetic"
    ref = parse_reference(raw)
    assert ref.parse_confidence == "HIGH"
    assert (
        parse_reference(render_reference(ref, {"syntax": "NUMBERED_JOURNAL_ARTICLE"})).identity()
        == ref.identity()
    )
    assert parse_reference("1. Ambiguous incomplete citation").parse_confidence == "LOW"


def test_core_numeric_citations_are_linked_to_canonical_references(tmp_path: Path) -> None:
    source = corpus.build_case(tmp_path / "citation-heavy.docx", 3)
    manuscript = parse_docx(source)
    reference_ids = {reference.object_id for reference in manuscript.references}
    assert len(manuscript.references) == 30
    assert len(manuscript.citations) == 4
    assert all(
        set(citation.reference_ids) <= reference_ids and len(citation.reference_ids) == 4
        for citation in manuscript.citations
    )
    assert all(citation.source_locator.status == "EXACT" for citation in manuscript.citations)


def test_inline_title_page_reorders_only_explicit_identity_paragraphs(tmp_path: Path) -> None:
    source = corpus.build_case(tmp_path / "messy.docx", 2)
    _, _, resolved = target()
    plan = m12_from_full_plan(plan_full_format(source, resolved))
    assert "TITLE_PAGE_RESTRUCTURE" in {operation.operation for operation in plan.operations}
    result = apply_format_transformations(source, plan, tmp_path / "output")
    report = verify_format_transformations(source, result, plan)
    assert report.preservation_checks["title_author_affiliation_contact_preserved"]
    assert report.transformation_verification_status == "VERIFIED_CANDIDATE"


def test_figure_validation_reads_metadata_without_changing_pixels(tmp_path: Path) -> None:
    image = tmp_path / "synthetic.png"
    image.write_bytes(corpus.PNG)
    before = file_hash(image)
    report = figure_technical_metadata(image)
    assert report["format"] == "PNG"
    assert (report["width"], report["height"]) == (100, 60)
    assert report["dpi"] is None
    assert report["technical_validation_status"] == "MANUAL_REVIEW_REQUIRED"
    assert file_hash(image) == before


def test_stage_resolution_and_render_unavailability(tmp_path: Path) -> None:
    source = corpus.build_case(tmp_path / "source.docx", 1)
    _, _, initial = target("INITIAL_SUBMISSION")
    assert not plan_full_format(source, initial)["m12_plan"]["operations"]
    _, _, accepted = target("ACCEPTED")
    assert all(field.status != "VERIFIED" for field in accepted.fields)
    report = LibreOfficeRenderBackend(str(tmp_path / "nonexistent.exe")).render(
        source, tmp_path / "render"
    )
    assert report.status == "NOT_AVAILABLE"
    assert "manual_visual_validation_required" in report.warnings


def test_reviewed_plan_binding_and_tamper_detection(tmp_path: Path) -> None:
    source = corpus.build_case(tmp_path / "source.docx", 1)
    registry, profile, resolved = target()
    plan = plan_full_format(source, resolved)
    plan["source_hash"] = file_hash(source) + "tampered"
    path = tmp_path / "tampered.json"
    path.write_text(json.dumps(plan))
    with pytest.raises(ValueError, match="binding"):
        run_full_format(
            source,
            tmp_path / "output",
            registry,
            profile,
            journal="nature-communications",
            article_type="article",
            stage="REVISION",
            approved_plan=path,
        )


def test_replanned_candidate_is_byte_idempotent(tmp_path: Path) -> None:
    source = corpus.build_case(tmp_path / "source.docx", 4)
    _, _, resolved = target()
    original_plan = m12_from_full_plan(plan_full_format(source, resolved))
    first = apply_format_transformations(source, original_plan, tmp_path / "first")
    candidate = Path(first.candidate_path)
    second_plan = m12_from_full_plan(plan_full_format(candidate, resolved))
    second = apply_format_transformations(candidate, second_plan, tmp_path / "second")
    assert candidate.read_bytes() == Path(second.candidate_path).read_bytes()
    assert len(second.artifacts) == 6
    roles = semantic_roles(read_document(candidate)[2])
    assert "JP_FIGURE_LEGEND" in roles.values()
    assert "JP_REFERENCES" in roles.values()


def test_verifier_detects_scientific_mutation_and_asset_tampering(tmp_path: Path) -> None:
    from zipfile import ZipFile

    source = corpus.build_case(tmp_path / "source.docx", 1)
    _, _, resolved = target()
    plan = m12_from_full_plan(plan_full_format(source, resolved))
    result = apply_format_transformations(source, plan, tmp_path / "output")
    path = Path(result.candidate_path)
    with ZipFile(path) as archive:
        parts = {item.filename: archive.read(item) for item in archive.infolist()}
    parts["word/document.xml"] = parts["word/document.xml"].replace(b"42 samples", b"43 samples")
    with ZipFile(path, "w") as archive:
        for name, payload in parts.items():
            archive.writestr(name, payload)
    report = verify_format_transformations(source, result, plan)
    assert report.transformation_verification_status == "VERIFICATION_FAILED"
    assert not report.preservation_checks["numbers_preserved"]


def test_supplement_inventory_preserves_bytes_and_blocks_unsafe_paths(tmp_path: Path) -> None:
    supplement = corpus.build_case(tmp_path / "supplement.docx", 1)
    inventory = supplement_inventory((supplement,))
    manifest = package_supplements(inventory, tmp_path / "supplements")
    assert manifest[0]["sha256"] == file_hash(supplement)
    assert (
        tmp_path / "supplements/Supplementary_Information.docx"
    ).read_bytes() == supplement.read_bytes()
    with pytest.raises(ValueError, match="single file"):
        supplement_inventory((supplement, supplement))
    registry, profile, _ = target()
    summary = run_full_format(
        corpus.build_case(tmp_path / "source.docx", 1),
        tmp_path / "output",
        registry,
        profile,
        journal="nature-communications",
        article_type="article",
        stage="REVISION",
        supplements=(supplement,),
    )
    assert summary["status"] == "VERIFIED_CANDIDATE"
    assert (
        tmp_path / "output/package/supplements/Supplementary_Information.docx"
    ).read_bytes() == supplement.read_bytes()


def test_page_property_schema_order_and_undefined_dimensions_preserved(tmp_path: Path) -> None:
    source = corpus.build_case(tmp_path / "source.docx", 1)
    _, _, resolved = target()
    plan = m12_from_full_plan(plan_full_format(source, resolved))
    before = read_document(source)[2].find(W + "sectPr")
    result = apply_format_transformations(source, plan, tmp_path / "output")
    after = read_document(Path(result.candidate_path))[2].find(W + "sectPr")
    assert before is not None and after is not None
    assert dict(before.find(W + "pgSz").attrib) == dict(after.find(W + "pgSz").attrib)
    assert dict(before.find(W + "pgMar").attrib) == dict(after.find(W + "pgMar").attrib)
    names = [node.tag for node in after]
    assert names.index(W + "pgNumType") < names.index(W + "cols")
