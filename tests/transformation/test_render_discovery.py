"""Backend discovery is local, explicit and fail closed."""

from pathlib import Path
from unittest.mock import patch

from journalport.verify.render import LibreOfficeRenderBackend


def test_configured_environment_path(tmp_path: Path, monkeypatch) -> None:
    executable = tmp_path / "soffice.exe"
    executable.touch()
    monkeypatch.setenv("JOURNALPORT_LIBREOFFICE_PATH", str(executable))
    assert LibreOfficeRenderBackend().executable == str(executable)


def test_invalid_explicit_path_does_not_fallback(tmp_path: Path, monkeypatch) -> None:
    executable = tmp_path / "soffice.exe"
    executable.touch()
    monkeypatch.setenv("JOURNALPORT_LIBREOFFICE_PATH", str(executable))
    with patch("journalport.verify.render.shutil.which", return_value=str(executable)):
        backend = LibreOfficeRenderBackend(str(tmp_path / "missing.exe"))
    assert backend.executable is None
    source = tmp_path / "input.docx"
    source.write_bytes(b"synthetic")
    report = backend.render(source, tmp_path / "render")
    assert report.status == "NOT_AVAILABLE"
    assert report.input_hash and report.input_hash.startswith("sha256:")
    assert report.output_pdf_hash is None
    assert report.conversion_exit_code is None


def test_explicit_path_overrides_environment(tmp_path: Path, monkeypatch) -> None:
    executable = tmp_path / "configured.exe"
    executable.touch()
    monkeypatch.setenv("JOURNALPORT_LIBREOFFICE_PATH", str(tmp_path / "missing.exe"))
    assert LibreOfficeRenderBackend(str(executable)).executable == str(executable)
