from dataclasses import replace
from pathlib import Path

import pytest

from journalport.package.builder import PackageBuildBlocked, build_package
from journalport.package.hashing import package_plan_hash
from journalport.package.safety import UnsafePackagePath, validate_relative_path
from tests.package.factories import package_context


@pytest.mark.parametrize("value", ("../x", "/absolute", "C:/escape", "a/../../b"))
def test_path_traversal_is_rejected(value: str) -> None:
    with pytest.raises(UnsafePackagePath):
        validate_relative_path(value)


def test_duplicate_identity_and_changed_source_block_build(tmp_path: Path) -> None:
    plan, _, _, _ = package_context(tmp_path)
    duplicate = replace(plan.artifacts[0], target_relative_path="other/copy.tex")
    changed = replace(plan, artifacts=plan.artifacts + (duplicate,), plan_hash="")
    changed = replace(changed, plan_hash=package_plan_hash(changed))
    with pytest.raises(PackageBuildBlocked, match="duplicate"):
        build_package(changed, tmp_path / "duplicate")
    Path(plan.artifacts[0].source_path).write_text("changed", encoding="utf-8")
    with pytest.raises(PackageBuildBlocked, match="changed"):
        build_package(plan, tmp_path / "changed")
