import zipfile
from dataclasses import replace
from pathlib import Path

import pytest
from lxml import etree

from journalport.cli import _resolve_profile_version
from journalport.profiles.document_format import resolve_document_format
from journalport.profiles.loader import ProfileRegistry
from journalport.transform.closure import formatting_coverage
from journalport.transform.format_engine import (
    apply_format_transformations,
    verify_format_transformations,
)
from journalport.transform.full_docx import read_document, serialize
from journalport.transform.full_format import m12_from_full_plan, plan_full_format
from journalport.transform.structure import (
    W,
    conditional_blocks,
    digest,
    order_conditional_sections,
)
from tests.transformation.test_nc_full_format import ROOT, corpus

FACTS = {"availability.placement": True}


def target():
    registry = ProfileRegistry.from_directory(ROOT / "journal_profiles")
    profile = _resolve_profile_version(
        ROOT / "journal_profiles", "nature-communications", "article", "1.3.2"
    )
    resolved = resolve_document_format(
        registry,
        profile,
        journal="nature-communications",
        article_type="article",
        submission_stage="REVISION",
    )
    return registry, profile, resolved


def source(path: Path, labels=("Code Availability", "Data Availability"), ambiguous=False):
    corpus.build_case(path, 4)
    parts, document, body = read_document(path)
    # References already satisfy their independently verified format target.
    from journalport.transform.references import render_reference_nodes

    _, _, resolved = target()
    style = next(f.value for f in resolved.fields if f.rule_id == "references.style")
    render_reference_nodes(body, style)
    refs = next(b for b in conditional_reference_blocks(body) if b.label == "References")
    position = refs.start
    for label in labels:
        paragraph = etree.Element(W + "p")
        if not ambiguous:
            props = etree.SubElement(paragraph, W + "pPr")
            etree.SubElement(props, W + "pStyle").set(W + "val", "Heading1")
        etree.SubElement(etree.SubElement(paragraph, W + "r"), W + "t").text = label
        statement = etree.Element(W + "p")
        etree.SubElement(
            etree.SubElement(statement, W + "r"), W + "t"
        ).text = "Synthetic supplied statement 17."
        body.insert(position, paragraph)
        body.insert(position + 1, statement)
        position += 2
    parts["word/document.xml"] = serialize(document)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, payload in parts.items():
            archive.writestr(name, payload)
    return path


def conditional_reference_blocks(body):
    from journalport.transform.structure import detect_blocks

    return detect_blocks(body)


def test_wrong_order_core_verify_and_idempotence(tmp_path):
    src = source(tmp_path / "source.docx")
    original = src.read_bytes()
    _, _, resolved = target()
    full = plan_full_format(src, resolved, conditional_applicability=FACTS)
    plan = m12_from_full_plan(full)
    operation = next(op for op in plan.operations if op.operation == "ORDER_CONDITIONAL_SECTIONS")
    single = replace(
        plan,
        operations=(replace(operation, depends_on=()),),
        execution_order=(operation.operation_id,),
    )
    result = apply_format_transformations(src, single, tmp_path / "single")
    verified = verify_format_transformations(src, result, single)
    assert verified.transformation_verification_status == "VERIFIED_CANDIDATE"
    assert verified.unexpected_changes == ()
    assert verified.failure_reasons == ()
    assert (
        result.operation_records[0]["before_body_hashes"]
        == result.operation_records[0]["after_body_hashes"]
    )
    assert verified.operations[0].checks["only_authorized_block_ordering_changed"]
    assert src.read_bytes() == original
    next_plan = plan_full_format(
        Path(result.candidate_path), resolved, conditional_applicability=FACTS
    )
    assert (
        next(
            r
            for r in next_plan["m12_plan"]["transfer_matrix"]
            if r["rule_id"] == "availability.placement"
        )["status"]
        == "SATISFIED"
    )
    second = apply_format_transformations(src, single, tmp_path / "repeat")
    assert Path(result.candidate_path).read_bytes() == Path(second.candidate_path).read_bytes()
    # Full pipeline can coexist with layout and reference presentation operations.
    combined = apply_format_transformations(src, plan, tmp_path / "full")
    report = verify_format_transformations(src, combined, plan)
    assert report.transformation_verification_status == "VERIFIED_CANDIDATE", report.failure_reasons
    coverage = formatting_coverage(plan.transfer_matrix, {op.rule_id for op in plan.operations})
    assert coverage["unresolved_closure_critical_blockers"] == 0
    assert coverage["formatting_target_coverage"] == 100
    assert coverage["target_format_status"] == "FORMAT_TARGET_VERIFIED"


def test_correct_order_noop(tmp_path):
    src = source(tmp_path / "source.docx", ("Data Availability", "Code Availability"))
    _, _, resolved = target()
    plan = plan_full_format(src, resolved, conditional_applicability=FACTS)
    row = next(
        r for r in plan["m12_plan"]["transfer_matrix"] if r["rule_id"] == "availability.placement"
    )
    assert row["status"] == "SATISFIED"
    body = read_document(src)[2]
    before = digest(body)
    assert not order_conditional_sections(body, row["target_state"])
    assert digest(body) == before


@pytest.mark.parametrize("label", ["Data Availability", "Code Availability"])
def test_missing_statement_author_input(tmp_path, label):
    src = source(tmp_path / "source.docx", (label,))
    _, _, resolved = target()
    plan = plan_full_format(src, resolved, conditional_applicability=FACTS)
    requirement = next(
        r for r in plan["manual_requirements"] if r["rule_id"] == "availability.placement"
    )
    assert requirement["classification"] == "AUTHOR_INPUT_REQUIRED"


@pytest.mark.parametrize("kind", ["ambiguous", "duplicate", "missing_references"])
def test_unreliable_blocks_fail_closed(tmp_path, kind):
    src = source(tmp_path / "source.docx", ambiguous=kind == "ambiguous")
    _, _, resolved = target()
    target_value = next(f.value for f in resolved.fields if f.rule_id == "availability.placement")
    body = read_document(src)[2]
    if kind == "duplicate":
        import copy

        heading = next(n for n in body if "".join(n.itertext()) == "Code Availability")
        body.insert(0, copy.deepcopy(heading))
    if kind == "missing_references":
        block = next(b for b in conditional_reference_blocks(body) if b.label == "References")
        body.remove(body[block.start])
    before = digest(body)
    with pytest.raises(ValueError):
        conditional_blocks(body, target_value)
    assert digest(body) == before


def test_without_author_condition_never_executes(tmp_path):
    src = source(tmp_path / "source.docx")
    _, _, resolved = target()
    plan = plan_full_format(src, resolved)
    assert not any(
        op["operation"] == "ORDER_CONDITIONAL_SECTIONS" for op in plan["m12_plan"]["operations"]
    )
    assert (
        next(r for r in plan["manual_requirements"] if r["rule_id"] == "availability.placement")[
            "classification"
        ]
        == "AUTHOR_INPUT_REQUIRED"
    )


def test_tampered_statement_body_rejected(tmp_path):
    src = source(tmp_path / "source.docx")
    _, _, resolved = target()
    # Journal identity does not enter the ordering algorithm.
    resolved = replace(resolved, journal="synthetic-other-journal")
    plan = m12_from_full_plan(plan_full_format(src, resolved, conditional_applicability=FACTS))
    op = next(op for op in plan.operations if op.operation == "ORDER_CONDITIONAL_SECTIONS")
    plan = replace(
        plan, operations=(replace(op, depends_on=()),), execution_order=(op.operation_id,)
    )
    result = apply_format_transformations(src, plan, tmp_path / "output")
    candidate = Path(result.candidate_path)
    parts, document, body = read_document(candidate)
    block = conditional_blocks(body, op.parameters["target"])[0]
    next(body[block.start + 1].iter(W + "t")).text = "Tampered supplied statement 17."
    parts["word/document.xml"] = serialize(document)
    with zipfile.ZipFile(candidate, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, payload in parts.items():
            archive.writestr(name, payload)
    report = verify_format_transformations(src, result, plan)
    assert report.transformation_verification_status == "VERIFICATION_FAILED"
    assert "section_body_hashes_unchanged" in report.failure_reasons
    assert report.unexpected_changes
