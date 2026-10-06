import json
from pathlib import Path

import pytest

from journalport.agents.nature_rewrite import extract_source
from journalport.agents.rewrite_workflow import rewrite_manuscript
from journalport.manuscript.rewrite_input import prepare_rewrite_input
from tests.transformation.test_nature_rewrite import proposal
from tests.transformation.test_scientific_structure import manuscript


@pytest.mark.parametrize("suffix", [".txt", ".md", ".tex"])
def test_input_conversion_archives_and_extracts(tmp_path, suffix):
    pytest.importorskip("docx")
    if suffix != ".txt":
        pytest.importorskip("pypandoc")
    content = (
        "Abstract\n\nObserved 42 cells.\n\nIntroduction\n\nBackground [1]."
        if suffix == ".txt"
        else "# Abstract\n\nObserved 42 cells.\n\n# Introduction\n\nBackground [1]."
        if suffix == ".md"
        else r"\documentclass{article}\begin{document}\section{Abstract}Observed 42 cells.\section{Introduction}Background [1].\end{document}"
    )
    source = tmp_path / ("source" + suffix)
    source.write_text(content)
    normalized, report = prepare_rewrite_input(source, tmp_path / "converted")
    inventory = extract_source(normalized)[3]
    assert any("42" in p["text"] for p in inventory["paragraphs"])
    assert Path(report["original"]).read_bytes() == source.read_bytes()


def test_latex_file_io_rejected(tmp_path):
    pytest.importorskip("pypandoc")
    source = tmp_path / "unsafe.tex"
    source.write_text(r"\input{/etc/passwd}")
    with pytest.raises(ValueError, match="self-contained"):
        prepare_rewrite_input(source, tmp_path / "out")


def test_failed_attempt_repaired_with_evidence(tmp_path):
    source = manuscript(tmp_path / "source.docx")
    inventory = extract_source(source)[3]
    calls = []

    def writer(payload):
        calls.append(payload)
        return {} if len(calls) == 1 else proposal(inventory)

    result = rewrite_manuscript(
        source,
        tmp_path / "out",
        journal="nature-communications",
        writer=writer,
        reviewer=lambda _: {"verdict": "PASS", "issues": [], "rationale": "Synthetic check"},
        privacy_mode="LOCAL_MODEL",
        render_executable="/nonexistent",
    )
    assert result["attempts"] == 2 and result["render_status"] == "NOT_AVAILABLE"
    assert "previous_attempt_feedback" in calls[1]
    assert (
        json.loads((tmp_path / "out/rewrite_report.json").read_text())["submission_ready"] is False
    )


def test_exhausted_attempts_publish_no_draft(tmp_path):
    source = manuscript(tmp_path / "source.docx")
    result = rewrite_manuscript(
        source,
        tmp_path / "out",
        journal="nature-communications",
        writer=lambda _: {},
        reviewer=lambda _: {},
        privacy_mode="LOCAL_MODEL",
        max_attempts=2,
    )
    assert result["state"] == "BLOCKED" and len(result["failures"]) == 2
    assert not (tmp_path / "out/nature-draft.docx").exists()
