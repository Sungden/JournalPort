from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from journalport.verify.render import LibreOfficeRenderBackend
from tests.transformation.test_nc_full_format import corpus


def backend(tmp_path: Path) -> LibreOfficeRenderBackend:
    executable = tmp_path / "fake-soffice.exe"
    executable.touch()
    return LibreOfficeRenderBackend(str(executable))


def test_invalid_docx_fails_before_conversion(tmp_path: Path) -> None:
    source = tmp_path / "invalid.docx"
    source.write_bytes(b"not a zip")
    with patch("journalport.verify.render.subprocess.run") as runner:
        report = backend(tmp_path).render(source, tmp_path / "render")
    assert report.status == "RENDER_FAILED"
    runner.assert_not_called()


@pytest.mark.parametrize("conversion_exit", [0, 1])
def test_empty_or_missing_pdf_is_not_render_pass(tmp_path: Path, conversion_exit: int) -> None:
    source = corpus.build_case(tmp_path / "source.docx", 1)

    def execute(args, **kwargs):
        if "--version" in args:
            return subprocess.CompletedProcess(
                args, 0, stdout=b"Synthetic test backend", stderr=b""
            )
        if conversion_exit == 0:
            output = Path(args[args.index("--outdir") + 1]) / "source.pdf"
            output.write_bytes(b"")
        return subprocess.CompletedProcess(args, conversion_exit, stdout=b"", stderr=b"")

    with patch("journalport.verify.render.subprocess.run", side_effect=execute):
        report = backend(tmp_path).render(source, tmp_path / "render")
    assert report.status == "RENDER_FAILED"
    assert report.output_pdf_hash is None
    assert report.conversion_exit_code == conversion_exit


def test_numeric_linkage_duplicate_number_and_live_fields(tmp_path: Path) -> None:
    from journalport.transform.full_docx import read_document
    from journalport.transform.references import inspect_linkage, reference_nodes
    from journalport.transform.structure import text

    source = corpus.build_case(tmp_path / "source.docx", 1)
    body = read_document(source)[2]
    refs = [text(node) for node in reference_nodes(body)]
    duplicate = refs + [refs[0]]
    assert inspect_linkage(body, duplicate)["linkage_confidence"] == "LOW"
    complex_source = corpus.build_case(tmp_path / "live.docx", 5)
    live_body = read_document(complex_source)[2]
    assert inspect_linkage(live_body, [text(n) for n in reference_nodes(live_body)])["live_fields"]
