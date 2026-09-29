from __future__ import annotations

from pathlib import Path

from journalport.manuscript.fingerprints import NUMBER_RE, manuscript_texts
from journalport.manuscript.parser_docx import parse_docx
from journalport.manuscript.parser_latex import parse_latex
from journalport.manuscript.serialization import serialize_canonical
from tests.docx_fixture_factory import build_docx

ROOT = Path(__file__).resolve().parents[2]


def _tokens(manuscript) -> set[str]:
    return {
        match.group(0).replace(" ", "")
        for text in manuscript_texts(manuscript)
        for match in NUMBER_RE.finditer(text)
    }


def test_ground_truth_preservation_metrics_are_complete(tmp_path: Path) -> None:
    docx = parse_docx(build_docx(tmp_path / "metrics.docx"))
    latex = parse_latex(ROOT / "tests/fixtures/latex/basic_article/main.tex")
    assert {"42", "12.5%", "p<0.01", "2025", "3.14"} <= _tokens(docx)
    assert {"42", "12.5%", "p<0.01", "2025"} <= _tokens(latex)
    assert len(docx.citations) == 1 and len(latex.citations) == 1
    assert len(docx.equations) == 1 and len(latex.equations) == 2
    assert len(docx.figures) == len(docx.tables) == 1
    assert len(latex.figures) == len(latex.tables) == 1
    assert not [
        x for x in docx.unsupported_content + latex.unsupported_content if x.severity == "BLOCKING"
    ]
    docx_payload = serialize_canonical(docx).decode("utf-8")
    latex_payload = serialize_canonical(latex).decode("utf-8")
    docx_text_units = [
        "Synthetic DOCX study",
        "We summarize 6 observations.",
        "Results",
        "We measured 42 samples; response 12.5% and p < 0.01.",
        "Figure 1 Synthetic signal.",
        "Table 1 Synthetic values.",
        "A | 2",
        "Doe J. Synthetic reference. 2025.",
        "Synthetic footnote 3.14",
        "Synthetic endnote",
    ]
    latex_text_units = [
        "Synthetic reproducible study",
        "We measured 42 samples with 95\\\\% confidence.",
        "Results",
        "The response was 12.5\\\\% and p < 0.01",
        "Synthetic signal.",
        "Synthetic values.",
        "A & B",
        "Doe J. Synthetic reference. 2025.",
    ]
    assert all(value in docx_payload for value in docx_text_units)
    assert all(value in latex_payload for value in latex_text_units)
