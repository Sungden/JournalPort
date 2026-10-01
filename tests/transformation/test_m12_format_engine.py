from __future__ import annotations

import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import pytest

from journalport.package.format_adapter import build_format_package, verify_format_package
from journalport.transform.format_engine import (
    FormatTransformationBlocked,
    apply_format_transformations,
    verify_format_transformations,
    write_format_reports,
)
from journalport.transform.format_models import FormatOperation, FormatRuleTarget
from journalport.transform.format_planner import (
    FormatPlanBlocked,
    _topological_order,
    plan_format_transformations,
    targets_from_profile_document,
    write_format_plan,
)
from journalport.transform.hashing import file_hash
from tests.docx_fixture_factory import A, M, R, W, _paragraph

ROOT = Path(__file__).resolve().parents[2]


def _m12_docx(path: Path) -> Path:
    image_paragraphs = "".join(
        f'<w:p><w:r><w:drawing><a:blip r:embed="rIdImage{number}"/></w:drawing></w:r></w:p>'
        + _paragraph(caption, "Caption")
        for number, caption in (
            (1, "Fig. 1. First synthetic signal."),
            (2, "Fig 2: Second synthetic signal."),
            (3, "FIGURE 3 Third synthetic signal."),
        )
    )
    abstract = " ".join(f"word{number}" for number in range(1, 281))
    references = "".join(
        _paragraph(f"{number}. Example A. Synthetic reference {number}. 2026.")
        for number in range(1, 26)
    )
    document = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
    <w:document xmlns:w="{W}" xmlns:m="{M}" xmlns:a="{A}" xmlns:r="{R}"><w:body>
      {_paragraph("Synthetic format-transfer study", "Title")}
      {_paragraph("Ada Example; Charles Example")}
      {_paragraph("Example Institute")}
      {_paragraph("Abstract", "Heading1")}{_paragraph(abstract)}
      {_paragraph("Results", "Heading1")}
      {_paragraph("We measured 42 samples; response was 12.5% and p &lt; 0.01.")}
      <w:p><m:oMath><m:r><m:t>y=2x+1</m:t></m:r></m:oMath></w:p>
      {_paragraph("Discussion", "Heading1")}{_paragraph("Synthetic discussion [1–3].")}
      {image_paragraphs}
      <w:tbl><w:tr><w:tc>{_paragraph("A")}</w:tc><w:tc>{_paragraph("2")}</w:tc></w:tr></w:tbl>
      {_paragraph("Table 1. Synthetic values.", "Caption")}
      {_paragraph("Data Availability", "Heading1")}{_paragraph("Synthetic data statement.")}
      {_paragraph("Author Contributions", "Heading1")}{_paragraph("Synthetic roles statement.")}
      {_paragraph("Acknowledgements", "Heading1")}{_paragraph("Synthetic acknowledgement.")}
      {_paragraph("Competing Interests", "Heading1")}{_paragraph("Synthetic interests statement.")}
      {_paragraph("References", "Heading1")}{references}
      <w:sectPr/>
    </w:body></w:document>"""
    relationships = """<?xml version="1.0" encoding="UTF-8"?>
    <Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
      <Relationship Id="rIdImage1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/image1.png"/>
      <Relationship Id="rIdImage2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/image2.png"/>
      <Relationship Id="rIdImage3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/image3.png"/>
    </Relationships>"""
    core = """<?xml version="1.0" encoding="UTF-8"?>
    <cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:title>Synthetic format-transfer study</dc:title><dc:creator>Ada Example; Charles Example</dc:creator></cp:coreProperties>"""
    with ZipFile(path, "w", ZIP_DEFLATED) as archive:
        archive.writestr("word/document.xml", document)
        archive.writestr("word/_rels/document.xml.rels", relationships)
        archive.writestr("docProps/core.xml", core)
        for number in range(1, 4):
            archive.writestr(f"word/media/image{number}.png", f"image-{number}".encode())
    return path


def _targets(status: str = "VERIFIED") -> tuple[FormatRuleTarget, ...]:
    evidence = ({"source_id": "synthetic-target", "evidence_id": "synthetic-rule"},)
    return (
        FormatRuleTarget(
            "manuscript_structure.admin_section_order",
            [
                "Acknowledgements",
                "Author Contributions",
                "Data Availability",
                "Competing Interests",
            ],
            status,
            evidence,
        ),
        FormatRuleTarget("title_page.mode", "SEPARATE_TITLE_PAGE", status, evidence),
        FormatRuleTarget(
            "figures.caption_format",
            {"prefix": "Figure", "separator": " | "},
            status,
            evidence,
        ),
        FormatRuleTarget("figures.separate_files", True, status, evidence),
    )


def _current() -> dict[str, object]:
    return {
        "manuscript_structure.admin_section_order": [
            "Data Availability",
            "Author Contributions",
            "Acknowledgements",
            "Competing Interests",
        ],
        "title_page.mode": "INLINE_TITLE_PAGE",
        "figures.caption_format": {"prefix": "MIXED", "separator": "MIXED"},
        "figures.separate_files": False,
    }


def _rewrite_member(path: Path, member: str, old: bytes, new: bytes) -> None:
    with ZipFile(path) as archive:
        values = [(item.filename, archive.read(item)) for item in archive.infolist()]
    with ZipFile(path, "w", ZIP_DEFLATED) as archive:
        for name, payload in values:
            archive.writestr(name, payload.replace(old, new) if name == member else payload)


def test_m12_four_operations_verify_preservation_and_are_idempotent(tmp_path: Path) -> None:
    source = _m12_docx(tmp_path / "journal-a.docx")
    source_hash = file_hash(source)
    plan = plan_format_transformations(
        source,
        current_state=_current(),
        targets=_targets(),
        source_journal="Synthetic Journal A",
        target_journal="Synthetic Journal B",
        profile_version="1.0.0",
    )
    plan_root, output = tmp_path / "plan", tmp_path / "output"
    write_format_plan(plan, plan_root)
    first = apply_format_transformations(source, plan, output)
    first_hashes = {item.relative_path: item.sha256 for item in first.artifacts}
    candidate_hash = first.candidate_hash
    second = apply_format_transformations(source, plan, output)
    assert second.candidate_hash == candidate_hash
    assert {item.relative_path: item.sha256 for item in second.artifacts} == first_hashes
    report = verify_format_transformations(source, second, plan)
    write_format_reports(output, plan, second, report)
    assert file_hash(source) == source_hash
    assert report.transformation_verification_status == "VERIFIED_CANDIDATE"
    assert report.unexpected_changes == ()
    assert report.failure_reasons == ()
    assert all(report.preservation_checks.values())
    assert {item.operation for item in report.operations} == {
        "REORDER_ADMIN_SECTIONS",
        "TITLE_PAGE_RESTRUCTURE",
        "FIGURE_CAPTION_NORMALIZATION",
        "EXTRACT_FIGURES_TO_SEPARATE_FILES",
    }
    assert len([item for item in second.artifacts if item.artifact_type == "FIGURE"]) == 3
    for number in range(1, 4):
        assert (output / f"figures/Figure_{number}.png").read_bytes() == f"image-{number}".encode()
    matrix = json.loads((plan_root / "transfer_matrix.json").read_text(encoding="utf-8"))
    assert {row["action"] for row in matrix["rows"]} == {"MODIFY", "SPLIT"}
    serialized_report = (output / "format_transformation_report.json").read_text(encoding="utf-8")
    assert "Synthetic roles statement" not in serialized_report
    package = tmp_path / "submission-package"
    manifest = build_format_package(second, report, package)
    package_report = verify_format_package(package)
    assert manifest["package_status"] == "PACKAGE_READY"
    assert package_report == {
        "schema_version": "1.0.0",
        "package_integrity": "PASS",
        "package_status": "PACKAGE_READY",
        "failure_reasons": [],
    }


def test_extraction_only_keeps_candidate_byte_identical(tmp_path: Path) -> None:
    source = _m12_docx(tmp_path / "source.docx")
    source_bytes = source.read_bytes()
    figure_target = tuple(item for item in _targets() if item.rule_id == "figures.separate_files")
    plan = plan_format_transformations(
        source,
        current_state={"figures.separate_files": False},
        targets=figure_target,
        target_journal="Synthetic Journal B",
        profile_version="1.0.0",
    )

    result = apply_format_transformations(source, plan, tmp_path / "output")
    candidate = Path(result.candidate_path)
    report = verify_format_transformations(source, result, plan)

    assert source.read_bytes() == source_bytes
    assert candidate.read_bytes() == source_bytes
    assert result.candidate_hash == result.source_hash
    assert report.preservation_checks["artifact_only_candidate_byte_identical"] is True
    assert report.transformation_verification_status == "VERIFIED_CANDIDATE"
    assert report.unexpected_changes == ()
    assert report.failure_reasons == ()
    assert len(result.artifacts) == 3


def test_uncertain_rules_never_enter_executor(tmp_path: Path) -> None:
    source = _m12_docx(tmp_path / "journal-a.docx")
    plan = plan_format_transformations(
        source,
        current_state=_current(),
        targets=_targets("PARTIAL"),
        target_journal="Synthetic Journal B",
        profile_version="1.0.0",
    )
    assert plan.operations == ()
    assert all(row.risk == "PROFILE_UNCERTAIN" for row in plan.transfer_matrix)
    assert all(row.status == "BLOCKED" for row in plan.transfer_matrix)


def test_ncomms_targets_are_submission_stage_aware_and_fail_closed(tmp_path: Path) -> None:
    source = _m12_docx(tmp_path / "synthetic.docx")
    profile = json.loads(
        (ROOT / "journal_profiles/journals/nature-communications/article-1.2.0.json").read_text(
            encoding="utf-8"
        )
    )
    targets = targets_from_profile_document(profile)
    initial = plan_format_transformations(
        source,
        current_state=_current(),
        targets=targets,
        target_journal="Nature Communications",
        profile_version="1.2.0",
        submission_stage="INITIAL_SUBMISSION",
    )
    assert initial.operations == ()
    assert initial.transfer_matrix == ()
    assert initial.submission_stage == "INITIAL_SUBMISSION"

    revision_state = _current() | {"title_page.mode": "SEPARATE_TITLE_PAGE"}
    revision = plan_format_transformations(
        source,
        current_state=revision_state,
        targets=targets,
        target_journal="Nature Communications",
        profile_version="1.2.0",
        submission_stage="REVISION",
    )
    assert {item.operation for item in revision.operations} == {"EXTRACT_FIGURES_TO_SEPARATE_FILES"}
    by_rule = {row.rule_id: row for row in revision.transfer_matrix}
    assert by_rule["manuscript_structure.admin_section_order"].executor_support == "UNSUPPORTED"
    assert by_rule["manuscript_structure.admin_section_order"].risk == "FORBIDDEN_AUTOMATIC"
    assert by_rule["figures.caption_format"].risk == "PROFILE_UNCERTAIN"
    assert by_rule["title_page.mode"].executor_support == "UNSUPPORTED"
    assert by_rule["title_page.mode"].risk == "FORBIDDEN_AUTOMATIC"


def test_ncomms_hardened_profile_does_not_retain_200_word_abstract_rule() -> None:
    profile = json.loads(
        (ROOT / "journal_profiles/journals/nature-communications/article-1.2.0.json").read_text(
            encoding="utf-8"
        )
    )
    rule = next(item for item in profile["rules"] if item["rule_id"] == "abstract.max_words")
    assert rule["value"] == 150
    assert rule["status"] == "PARTIAL"
    assert rule["submission_stages"] == ["REVISION", "FINAL_SUBMISSION"]


def test_dependency_cycle_fails_closed() -> None:
    common = {
        "rule_id": "synthetic",
        "target_object": "synthetic",
        "parameters": {},
        "evidence": (),
        "classification": "SAFE_FORMAT_AUTOMATIC",
        "executor_support": "SUPPORTED",
        "approval_requirement": "NOT_REQUIRED",
        "confidence": "HIGH",
        "profile_status": "VERIFIED",
        "preconditions": (),
        "expected_delta": {},
        "conflicts_with": (),
    }
    one = FormatOperation("one", operation="ONE", depends_on=("two",), **common)  # type: ignore[arg-type]
    two = FormatOperation("two", operation="TWO", depends_on=("one",), **common)  # type: ignore[arg-type]
    with pytest.raises(FormatPlanBlocked, match="dependency cycle"):
        _topological_order((one, two))


@pytest.mark.parametrize(
    ("member", "old", "new", "message"),
    (
        (
            "word/document.xml",
            _paragraph("References", "Heading1").encode(),
            (_paragraph("References", "Heading1") * 2).encode(),
            "ambiguous References location",
        ),
        (
            "word/document.xml",
            b"Fig. 1. First synthetic signal.",
            b"Fig. 1",
            "figure caption body is missing",
        ),
        (
            "word/_rels/document.xml.rels",
            b"media/image1.png",
            b"media/missing.png",
            "embedded figure asset is missing",
        ),
    ),
)
def test_m12_malformed_or_ambiguous_input_fails_closed(
    tmp_path: Path, member: str, old: bytes, new: bytes, message: str
) -> None:
    source = _m12_docx(tmp_path / "journal-a.docx")
    _rewrite_member(source, member, old, new)
    plan = plan_format_transformations(
        source,
        current_state=_current(),
        targets=_targets(),
        target_journal="Synthetic Journal B",
        profile_version="1.0.0",
    )
    with pytest.raises(FormatTransformationBlocked, match=message):
        apply_format_transformations(source, plan, tmp_path / "output")
