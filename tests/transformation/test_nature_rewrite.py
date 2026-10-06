import copy
import json
import zipfile

import pytest
from lxml import etree

from journalport.agents.nature_rewrite import (
    compatible_model,
    extract_source,
    run_nature_rewrite,
    validate_proposal,
)
from journalport.transform.full_docx import read_document, serialize
from journalport.transform.structure import W, text
from tests.transformation.test_scientific_structure import manuscript


def proposal(inventory):
    sections = [
        {"heading": h, "blocks": []}
        for h in ("Abstract", "Introduction", "Results", "Discussion", "Methods")
    ]
    for record in inventory["paragraphs"]:
        name = record["source_section"]
        dest = (
            0
            if name == "Abstract"
            else 1
            if "Introduction" in name or "Related work" in name
            else 2
            if "Results" in name
            else 4
            if "Methods" in name
            else 3
        )
        block = {"source_ids": [record["id"]]}
        if record["editable"]:
            block["text"] = "Reframed evidence: " + record["text"]
        else:
            block["copy_id"] = record["id"]
        sections[dest]["blocks"].append(block)
    return {"sections": sections, "author_questions": []}


def test_full_rewrite_preserves_source_and_media(tmp_path):
    source = manuscript(tmp_path / "source.docx")
    original = source.read_bytes()
    _, _, _, inventory = extract_source(source)
    calls = []

    def writer(payload):
        calls.append(payload)
        return proposal(inventory)

    def reviewer(payload):
        calls.append(payload)
        return {"verdict": "PASS", "issues": [], "rationale": "Source-grounded synthetic rewrite."}

    result = run_nature_rewrite(
        source,
        tmp_path / "out",
        journal="nature-communications",
        writer=writer,
        reviewer=reviewer,
        privacy_mode="LOCAL_MODEL",
    )
    assert result["state"] == "DRAFT_REQUIRES_AUTHOR_REVIEW" and not result["submission_ready"]
    assert len(calls) == 2 and source.read_bytes() == original
    before, _, _ = read_document(source)
    after, _, body = read_document(tmp_path / "out/nature-draft.docx")
    assert all(after[k] == v for k, v in before.items() if k != "word/document.xml")
    assert any(text(n).startswith("Reframed evidence:") for n in body)
    assert text(body[-1]) == "References body: n=42, p=0.01, citation [1]."


@pytest.mark.parametrize("damage", ["number", "citation", "omission", "duplicate"])
def test_damage_blocks_before_review(tmp_path, damage):
    source = manuscript(tmp_path / "s.docx")
    _, _, _, inventory = extract_source(source)
    value = proposal(inventory)
    blocks = value["sections"][1]["blocks"]
    if damage == "number":
        blocks[0]["text"] = blocks[0]["text"].replace("n=42", "n=43")
    if damage == "citation":
        blocks[0]["text"] = blocks[0]["text"].replace("[1]", "[2]")
    if damage == "omission":
        blocks.pop()
    if damage == "duplicate":
        blocks.append(copy.deepcopy(blocks[0]))
    with pytest.raises(ValueError):
        validate_proposal(inventory, value)


def test_semantic_failure_never_publishes_candidate(tmp_path):
    source = manuscript(tmp_path / "s.docx")
    _, _, _, inventory = extract_source(source)
    with pytest.raises(ValueError, match="Semantic review failed"):
        run_nature_rewrite(
            source,
            tmp_path / "out",
            journal="nature-communications",
            writer=lambda _: proposal(inventory),
            reviewer=lambda _: {
                "verdict": "FAIL",
                "issues": ["Invented interpretation"],
                "rationale": "Unsupported",
            },
            privacy_mode="LOCAL_MODEL",
        )
    assert not (tmp_path / "out/nature-draft.docx").exists()
    assert json.loads((tmp_path / "out/rewrite_status.json").read_text())["state"] == "BLOCKED"


def test_opaque_equation_must_be_copied(tmp_path):
    source = manuscript(tmp_path / "s.docx")
    parts, root, body = read_document(source)
    node = next(n for n in body if text(n).startswith("III. Methods body"))
    etree.SubElement(node, "{http://schemas.openxmlformats.org/officeDocument/2006/math}oMath")
    parts["word/document.xml"] = serialize(root)
    with zipfile.ZipFile(source, "w") as z:
        for k, v in parts.items():
            z.writestr(k, v)
    _, _, _, inventory = extract_source(source)
    value = proposal(inventory)
    validate_proposal(inventory, value)
    block = value["sections"][4]["blocks"][0]
    del block["copy_id"]
    block["text"] = "Changed equation"
    with pytest.raises(ValueError):
        validate_proposal(inventory, value)


def test_remote_requires_explicit_permission_and_https():
    with pytest.raises(ValueError):
        compatible_model("https://example.com/v1", "model", allow_remote=False)
    with pytest.raises(ValueError):
        compatible_model("http://example.com/v1", "model", allow_remote=True)
    assert callable(compatible_model("http://127.0.0.1:8000/v1", "model", allow_remote=False))


def test_missing_author_facts_prevent_publication(tmp_path):
    source = manuscript(tmp_path / "s.docx")
    _, _, _, inventory = extract_source(source)
    value = proposal(inventory)
    value["author_questions"] = ["Confirm experimental sampling details."]
    report = run_nature_rewrite(
        source,
        tmp_path / "out",
        journal="nature-communications",
        writer=lambda _: value,
        reviewer=lambda _: {"verdict": "PASS", "issues": [], "rationale": "Needs author input."},
        privacy_mode="LOCAL_MODEL",
    )
    assert report["state"] == "WAITING_FOR_AUTHOR_INPUT"
    assert not (tmp_path / "out/nature-draft.docx").exists()


def test_numbered_references_are_not_rewritten(tmp_path):
    source = manuscript(tmp_path / "s.docx")
    parts, root, body = read_document(source)
    node = next(n for n in body if text(n) == "References")
    next(node.iter(W + "t")).text = "VII. References"
    parts["word/document.xml"] = serialize(root)
    with zipfile.ZipFile(source, "w") as z:
        for k, v in parts.items():
            z.writestr(k, v)
    _, _, _, inventory = extract_source(source)
    assert all("References" not in r["source_section"] for r in inventory["paragraphs"])


def test_malformed_model_proposal_is_rejected(tmp_path):
    source = manuscript(tmp_path / "s.docx")
    _, _, _, inventory = extract_source(source)
    for value in (None, [], {"sections": [None]}):
        with pytest.raises(ValueError):
            validate_proposal(inventory, value)
