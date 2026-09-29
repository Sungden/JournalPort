import json
import socket
from pathlib import Path

import pytest

from journalport.cli import main


def test_offline_audit_cli_writes_json_and_html(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = Path(__file__).resolve().parents[2]
    source = root / "tests/fixtures/latex/basic_article/main.tex"
    original = source.read_bytes()
    monkeypatch.setattr(
        socket,
        "create_connection",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("network forbidden")),
    )
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("network forbidden")),
    )
    output = tmp_path / "audit"
    result = main(
        [
            "audit",
            str(source),
            "--journal",
            "nature-communications",
            "--profiles",
            str(root / "journal_profiles"),
            "--output",
            str(output),
            "--format",
            "both",
        ]
    )
    assert result == 0
    report = json.loads((output / "compliance_report.json").read_text(encoding="utf-8"))
    assert report["readiness_status"] == "EVALUATION_FAILED"
    assert (output / "evaluation_trace.json").is_file()
    assert (output / "compliance_report.html").is_file()
    assert source.read_bytes() == original
