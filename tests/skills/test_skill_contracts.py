from __future__ import annotations

import importlib
import json
import subprocess
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
SKILLS = ("journal-profile", "journal-audit", "journal-transfer", "submission-package")


def test_registry_and_skill_run_schemas() -> None:
    registry = json.loads((ROOT / "skills/registry.yaml").read_text(encoding="utf-8"))
    schema = json.loads((ROOT / "schemas/skill_registry.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(registry)
    assert {item["skill_id"] for item in registry["skills"]} == set(SKILLS)
    assert {item["version"] for item in registry["skills"]} == {"1.0.0"}


def test_skills_are_thin_and_progressively_disclosed() -> None:
    forbidden = ("def count_words", "SUBMISSION_READY", "auto-verify profile")
    for skill in SKILLS:
        text = (ROOT / "skills" / skill / "SKILL.md").read_text(encoding="utf-8")
        assert text.startswith("---\nname:")
        assert len(text.splitlines()) < 45
        assert "journalport" in text.lower()
        assert not any(term in text for term in forbidden)
        assert (ROOT / "skills" / skill / "scripts/run.py").is_file()


def test_public_api_exists_and_core_does_not_import_skills() -> None:
    api = importlib.import_module("journalport.api")
    assert set(api.__all__) == {
        "apply",
        "audit",
        "package_build",
        "package_plan",
        "package_verify",
        "plan",
        "refresh_profile_draft",
        "verify",
    }
    for path in (ROOT / "src/journalport").rglob("*.py"):
        assert "import skills" not in path.read_text(encoding="utf-8")


def test_all_skill_scripts_have_working_help() -> None:
    for skill in SKILLS:
        result = subprocess.run(
            [sys.executable, str(ROOT / "skills" / skill / "scripts/run.py"), "--help"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        assert "usage:" in result.stdout


def test_profile_skill_cannot_write_to_production_profiles(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "skills/journal-profile/scripts/run.py"),
            "--journal",
            "x",
            "--profiles",
            str(tmp_path / "journal_profiles"),
            "--output",
            str(tmp_path / "journal_profiles/drafts"),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert "must not be journal_profiles" in result.stderr


def test_adversarial_safety_contracts_are_explicit() -> None:
    corpus = "\n".join(path.read_text(encoding="utf-8") for path in (ROOT / "skills").rglob("*.md"))
    for terms in (
        ("draft", "verified", "review"),
        ("overwrite", "production"),
        ("unknown", "pass"),
        ("author_approval_required", "stop"),
        ("shorten an abstract", "never"),
        ("fabricate", "never"),
        ("verification failure", "stop"),
    ):
        assert all(term in corpus.lower() for term in terms)


def test_skill_run_record_schema(tmp_path: Path) -> None:
    sys.path.insert(0, str(ROOT / "skills"))
    from _shared.runtime import write_record

    source = tmp_path / "source.txt"
    source.write_text("synthetic", encoding="utf-8")
    record = tmp_path / "skill_run.json"
    write_record(
        record,
        skill_id="journal-audit",
        inputs=[source],
        outputs=[],
        commands=[["audit"]],
        final_status="UNKNOWN",
        manual_review_items=["review"],
    )
    schema = json.loads((ROOT / "schemas/skill_run.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(json.loads(record.read_text(encoding="utf-8")))
