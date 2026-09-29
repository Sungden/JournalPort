from __future__ import annotations

import hashlib
import inspect
import json
import subprocess
import sys
from pathlib import Path

import journalport
from journalport import api

ROOT = Path(__file__).resolve().parents[2]


def test_release_version_is_single_sourced_and_synchronized() -> None:
    assert journalport.__version__ == "0.1.0rc1"
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'dynamic = ["version"]' in pyproject
    assert 'path = "src/journalport/_version.py"' in pyproject
    assert "version: 0.1.0rc1" in (ROOT / "CITATION.cff").read_text(encoding="utf-8")


def test_public_api_surface_is_typed_and_documented() -> None:
    expected = {
        "apply",
        "audit",
        "package_build",
        "package_plan",
        "package_verify",
        "plan",
        "refresh_profile_draft",
        "verify",
    }
    assert set(api.__all__) == expected
    for name in expected:
        function = getattr(api, name)
        signature = inspect.signature(function)
        assert signature.return_annotation is not inspect.Signature.empty
        assert function.__doc__ or api.__doc__


def test_cli_version_help_and_benchmark_contract(tmp_path: Path) -> None:
    version = subprocess.run(
        [sys.executable, "-m", "journalport.cli", "--version"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert version.returncode == 0
    assert version.stdout.strip() == "journalport 0.1.0rc1"
    output = tmp_path / "benchmark.json"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "journalport.cli",
            "benchmark",
            "guideline-extraction",
            "--output",
            str(output),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    value = json.loads(output.read_text(encoding="utf-8"))
    assert value["benchmark_version"] == "1.0.0"
    assert value["journalport_version_verified_with"] == "0.1.0rc1"


def test_profile_registry_hashes_and_statuses() -> None:
    registry = json.loads((ROOT / "journal_profiles/registry.yaml").read_text(encoding="utf-8"))
    assert registry["registry_version"] == "1.0.0"
    assert len(registry["profiles"]) == 3
    for item in registry["profiles"]:
        slug = item["profile_id"].removeprefix("article-type:").removesuffix("/article")
        path = ROOT / "journal_profiles/journals" / slug / f"article-{item['version']}.json"
        assert hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"]
        assert item["status"] == "PARTIAL"


def test_citation_is_provisional_without_invented_hosting_metadata() -> None:
    text = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    for required in (
        "cff-version: 1.2.0",
        "title: JournalPort",
        "name: Sungden",
        "version: 0.1.0rc1",
        "license: Apache-2.0",
    ):
        assert required in text
    assert "repository-code:" not in text
    assert "doi:" not in text.lower()


def test_documentation_and_release_structure() -> None:
    required = (
        "docs/API.md",
        "docs/CLI.md",
        "docs/PRIVACY.md",
        "docs/THREAT_MODEL.md",
        "docs/CONTRIBUTING_PROFILES.md",
        "docs/CONTRIBUTING_SKILLS.md",
        "docs/RELEASE.md",
        "docs/releases/0.1.0rc1.md",
        "docs/adr/README.md",
        "docs/adr/ADR-025-skill-distribution-strategy.md",
        "docs/adr/ADR-026-profile-distribution-strategy.md",
        "RELEASE_CHECKLIST.md",
        "THIRD_PARTY_NOTICES.md",
    )
    assert all((ROOT / path).is_file() for path in required)
