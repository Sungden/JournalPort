import json
from pathlib import Path

from journalport.cli import main

ROOT = Path(__file__).resolve().parents[2]


def test_discover_and_offline_extract_cli(tmp_path: Path) -> None:
    discovery = tmp_path / "sources.json"
    assert (
        main(
            [
                "profile",
                "discover",
                "--journal",
                "Nature Communications",
                "--output",
                str(discovery),
            ]
        )
        == 0
    )
    sources = json.loads(discovery.read_text(encoding="utf-8"))["sources"]
    assert len(sources) == 2
    output = tmp_path / "drafts"
    assert (
        main(
            [
                "profile",
                "extract-from-snapshot",
                str(ROOT / "tests/fixtures/guidelines/nature-communications.json"),
                "--journal",
                "nature-communications",
                "--profiles",
                str(ROOT / "journal_profiles"),
                "--output",
                str(output),
            ]
        )
        == 0
    )
    candidate = next(output.rglob("candidate_profile.json"))
    assert json.loads(candidate.read_text(encoding="utf-8"))["status"] == "DRAFT"
