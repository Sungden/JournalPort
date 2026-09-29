import json
from pathlib import Path

from journalport.cli import main


def test_plan_is_dry_run_and_apply_creates_candidate_without_source_mutation(
    tmp_path: Path,
) -> None:
    root = Path(__file__).resolve().parents[2]
    source = root / "tests/fixtures/latex/basic_article/main.tex"
    before = source.read_bytes()
    plan_dir = tmp_path / "plan"
    candidate_dir = tmp_path / "candidate"
    assert (
        main(
            [
                "plan",
                str(source),
                "--journal",
                "nature-communications",
                "--profiles",
                str(root / "journal_profiles"),
                "--output",
                str(plan_dir),
            ]
        )
        == 0
    )
    assert source.read_bytes() == before
    assert not candidate_dir.exists()
    plan = json.loads((plan_dir / "transformation_plan.json").read_text(encoding="utf-8"))
    assert plan["plan_status"] == "APPROVAL_REQUIRED"
    assert (
        main(
            [
                "apply",
                str(plan_dir / "transformation_plan.json"),
                "--profiles",
                str(root / "journal_profiles"),
                "--output",
                str(candidate_dir),
            ]
        )
        == 0
    )
    manifest = json.loads((candidate_dir / "candidate_manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "TRANSFORMED_CANDIDATE"
    assert source.read_bytes() == before
