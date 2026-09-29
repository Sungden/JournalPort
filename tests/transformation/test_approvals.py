from dataclasses import replace

from journalport.transform.approvals import approval_is_valid, proposed_content_hash
from journalport.transform.executor import execute_plan
from journalport.transform.models import Approval
from journalport.transform.planner import create_plan
from tests.transformation.factories import context


def test_approval_is_bound_to_action_plan_and_proposal(tmp_path) -> None:
    artifact, manuscript, profile, report = context(tmp_path)
    plan = create_plan(manuscript, profile, report, artifact)
    action = plan.actions[0]
    approval = Approval(
        "1.0.0",
        action.action_id,
        plan.plan_hash,
        proposed_content_hash(action),
        "APPROVED",
        "fixture-author",
        "2026-09-29T00:00:00Z",
    )
    assert approval_is_valid(approval, plan, action)
    assert not approval_is_valid(replace(approval, plan_hash="sha256:" + "0" * 64), plan, action)
    assert not approval_is_valid(
        replace(approval, proposed_content_hash="sha256:" + "0" * 64), plan, action
    )
    assert not approval_is_valid(replace(approval, action_id="action:wrong"), plan, action)
    changed = replace(action, parameters={"proposal_available": True})
    assert not approval_is_valid(approval, plan, changed)
    result = execute_plan(
        plan, manuscript, profile, report, tmp_path / "candidate", approvals=(approval,)
    )
    assert result.logs[0].execution_status == "MANUAL_ACTION_REQUIRED"
    assert not result.manifest.applied_action_ids
