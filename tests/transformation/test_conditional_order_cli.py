from pathlib import Path

import pytest

from journalport.cli import main
from journalport.transform.full_format import plan_full_format
from tests.transformation.test_conditional_section_order import source, target


def test_cli_condition_is_persisted_in_plan(tmp_path: Path) -> None:
    import json

    src = source(tmp_path / "source.docx")
    output = tmp_path / "plan"
    result = main(
        [
            "full-format",
            str(src),
            "--journal",
            "nature-communications",
            "--stage",
            "REVISION",
            "--confirm-condition",
            "availability.placement",
            "--plan-only",
            "--output",
            str(output),
        ]
    )
    assert result == 0
    plan = json.loads((output / "metadata/full_format_plan.json").read_text())
    assert plan["profile_version"] == "1.3.2"
    assert plan["conditional_applicability"] == {"availability.placement": True}
    assert any(
        op["operation"] == "ORDER_CONDITIONAL_SECTIONS" for op in plan["m12_plan"]["operations"]
    )


def test_unknown_condition_rejected(tmp_path: Path) -> None:
    src = source(tmp_path / "source.docx")
    with pytest.raises(ValueError, match="unknown_or_invalid"):
        plan_full_format(src, target()[2], conditional_applicability={"invented.rule": True})
