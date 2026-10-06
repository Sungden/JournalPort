import json
import zipfile
from pathlib import Path

import pytest
from lxml import etree

from journalport.cli import main
from journalport.transform.full_docx import read_document, serialize
from journalport.transform.scientific_structure import (
    level,
    plan_scientific_structure,
    run_scientific_structure,
    verify_scientific_structure,
)
from journalport.transform.structure import StructureBlocked, W, text
from tests.transformation.test_nc_full_format import corpus


def manuscript(path: Path) -> Path:
    source = corpus.build_case(path, 1)
    parts, root, body = read_document(source)
    body[:] = []
    for title in [
        "Abstract",
        "I. Introduction",
        "II. Related work",
        "III. Methods",
        "IV. Results",
        "V. Discussion",
        "VI. Conclusion",
        "References",
    ]:
        p = etree.SubElement(body, W + "p")
        props = etree.SubElement(p, W + "pPr")
        etree.SubElement(props, W + "pStyle").set(W + "val", "Heading1")
        etree.SubElement(etree.SubElement(p, W + "r"), W + "t").text = title
        q = etree.SubElement(body, W + "p")
        etree.SubElement(etree.SubElement(q, W + "r"), W + "t").text = (
            title + " body: n=42, p=0.01, citation [1]."
        )
        if title == "II. Related work":
            p = etree.SubElement(body, W + "p")
            props = etree.SubElement(p, W + "pPr")
            etree.SubElement(props, W + "pStyle").set(W + "val", "Heading2")
            etree.SubElement(etree.SubElement(p, W + "r"), W + "t").text = "Prior methods"
    parts["word/document.xml"] = serialize(root)
    with zipfile.ZipFile(source, "w") as z:
        for k, v in parts.items():
            z.writestr(k, v)
    return source


def test_cli_plan_apply(tmp_path):
    source = manuscript(tmp_path / "source.docx")
    original = source.read_bytes()
    assert (
        main(
            [
                "restructure",
                str(source),
                "--recipe",
                "ieee-to-nature-communications",
                "--plan-only",
                "--output",
                str(tmp_path / "plan"),
            ]
        )
        == 0
    )
    assert (
        main(
            [
                "restructure",
                str(source),
                "--recipe",
                "ieee-to-nature-communications",
                "--reviewed-plan",
                str(tmp_path / "plan/structure_plan.json"),
                "--output",
                str(tmp_path / "result"),
            ]
        )
        == 0
    )
    _, _, body = read_document(tmp_path / "result/manuscript.docx")
    assert [text(n) for n in body if level(n) == 0] == [
        "Abstract",
        "I. Introduction",
        "IV. Results",
        "V. Discussion",
        "III. Methods",
        "References",
    ]
    assert [(text(n), level(n)) for n in body if text(n) == "Prior methods"] == [
        ("Prior methods", 2)
    ]
    assert source.read_bytes() == original
    report = json.loads((tmp_path / "result/structure_verification.json").read_text())
    assert all(report["preservation_checks"].values()) and not report["submission_ready"]


def test_requires_review_and_rejects_plan_tampering(tmp_path):
    source = manuscript(tmp_path / "source.docx")
    with pytest.raises(StructureBlocked):
        run_scientific_structure(source, tmp_path / "no")
    run_scientific_structure(source, tmp_path / "plan", plan_only=True)
    path = tmp_path / "plan/structure_plan.json"
    plan = json.loads(path.read_text())
    plan["moves"] = []
    path.write_text(json.dumps(plan))
    with pytest.raises(StructureBlocked):
        run_scientific_structure(source, tmp_path / "bad", reviewed_plan=path)


def test_verification_rejects_scientific_edits(tmp_path):
    source = manuscript(tmp_path / "source.docx")
    plan = plan_scientific_structure(source)
    run_scientific_structure(source, tmp_path / "plan", plan_only=True)
    run_scientific_structure(
        source, tmp_path / "out", reviewed_plan=tmp_path / "plan/structure_plan.json"
    )
    candidate = tmp_path / "out/manuscript.docx"
    parts, root, body = read_document(candidate)
    next(body.iter(W + "t")).text = "Fabricated claim"
    parts["word/document.xml"] = serialize(root)
    with zipfile.ZipFile(candidate, "w") as z:
        for k, v in parts.items():
            z.writestr(k, v)
    with pytest.raises(StructureBlocked):
        verify_scientific_structure(source, candidate, plan)


def test_unknown_section_blocked(tmp_path):
    source = manuscript(tmp_path / "source.docx")
    parts, root, body = read_document(source)
    heading = next(n for n in body if text(n) == "III. Methods")
    next(heading.iter(W + "t")).text = "Proposed Architecture"
    parts["word/document.xml"] = serialize(root)
    with zipfile.ZipFile(source, "w") as z:
        for k, v in parts.items():
            z.writestr(k, v)
    with pytest.raises(StructureBlocked):
        plan_scientific_structure(source)
