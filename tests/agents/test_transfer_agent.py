from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from journalport.agents.transfer import (
    TransferSession,
    append_disclosure,
    build_proposal,
    classify_finding,
    load_session,
    minimize_abstract_context,
    save_session,
    scientific_diff,
    verification_allows_packaging,
)

ROOT = Path(__file__).resolve().parents[2]


def _session() -> TransferSession:
    return TransferSession(
        schema_version="1.0.0",
        session_id="synthetic-session",
        created_at=datetime.now(UTC).isoformat(),
        source_manuscript_path="private/synthetic.docx",
        source_manuscript_hash="sha256:" + "a" * 64,
        source_journal="Synthetic Journal",
        target_journal="Nature Communications",
        article_type="Article",
        privacy_mode="CODEX_HOSTED",
        profile_version="1.1.0",
        disclosure_ledger_path="sessions/synthetic/disclosure.json",
    )


def test_session_is_schema_valid_and_resumable_from_waiting_states(tmp_path: Path) -> None:
    schema = json.loads((ROOT / "schemas/transfer_session.schema.json").read_text(encoding="utf-8"))
    waiting_input = (
        _session()
        .transition("AUDITED")
        .transition("PLAN_READY")
        .transition("WAITING_FOR_AUTHOR_INPUT")
    )
    path = tmp_path / "session.json"
    save_session(waiting_input, path)
    resumed = load_session(path)
    assert resumed == waiting_input
    waiting_approval = resumed.transition("WAITING_FOR_APPROVAL")
    save_session(waiting_approval, path)
    Draft202012Validator(schema).validate(load_session(path).to_dict())
    assert load_session(path).status == "WAITING_FOR_APPROVAL"


def test_invalid_session_transition_fails_closed() -> None:
    with pytest.raises(ValueError, match="invalid session transition"):
        _session().transition("VERIFIED")


@pytest.mark.parametrize(
    ("original", "proposed", "field"),
    [
        ("n=42", "n=43", "numeric_changes"),
        ("response was 12%", "response was 13%", "percentage_changes"),
        ("supported [4]", "supported [5]", "citation_changes"),
        ("shown in Figure 2", "shown in Figure 3", "figure_reference_changes"),
        ("doi:10.1000/ABC1", "doi:10.1000/ABC2", "doi_changes"),
    ],
)
def test_scientific_diff_detects_protected_changes(
    original: str, proposed: str, field: str
) -> None:
    report = scientific_diff(original, proposed)
    assert report.status == "REVIEW_REQUIRED"
    assert getattr(report, field)


def test_scientific_diff_safe_case_and_proposal_escalation() -> None:
    unchanged = "In 2024, n=42 yielded 12% (p<0.05), as shown in Figure 2 [4]."
    assert scientific_diff(unchanged, unchanged).status == "SAFE"
    proposal, report = build_proposal(
        proposal_id="p1",
        session_id="s1",
        rule_id="abstract.max_words",
        target_object_id="abstract",
        operation="REPLACE_ABSTRACT",
        original_text="n=42 yielded 12% [4]. Additional background wording.",
        proposed_text="n=42 yielded 13% [4].",
        rationale="Synthetic shortening proposal",
        source_evidence=("rule:abstract.max_words",),
        created_by="mock-agent",
    )
    assert report.percentage_changes
    assert proposal.risk_level == "HIGH"
    assert proposal.approval_status == "PENDING"


def test_proposal_and_diff_validate_against_schemas() -> None:
    proposal, report = build_proposal(
        proposal_id="p-safe",
        session_id="s1",
        rule_id="abstract.max_words",
        target_object_id="abstract",
        operation="REPLACE_ABSTRACT",
        original_text="Result ALPHA was stable.",
        proposed_text="Result ALPHA was stable.",
        rationale="No-op synthetic contract test",
        source_evidence=("synthetic",),
        created_by="mock-agent",
    )
    for name, value in (
        ("agent_proposal", proposal.to_dict()),
        ("scientific_diff", report.to_dict()),
    ):
        schema = json.loads((ROOT / f"schemas/{name}.schema.json").read_text(encoding="utf-8"))
        Draft202012Validator(schema).validate(value)


def test_prompt_minimization_and_hash_only_disclosure_ledger(tmp_path: Path) -> None:
    result_marker = "CONFIDENTIAL_RESULT_" + "A7F9"
    secret_abstract = f"{result_marker} was observed in 42 samples."
    context = minimize_abstract_context(
        secret_abstract,
        target_words=200,
        target_journal="Nature Communications",
        rule_text="Abstract maximum 200 words.",
    )
    assert set(context) == {
        "abstract",
        "current_word_count",
        "target_word_count",
        "target_journal",
        "rule",
    }
    ledger = tmp_path / "disclosure.json"
    append_disclosure(
        ledger,
        session_id="s1",
        task_type="ABSTRACT_REVISION",
        model_host="codex",
        model_name="mock",
        privacy_mode="CODEX_HOSTED",
        disclosed_objects={"abstract": secret_abstract, "rule": str(context["rule"])},
        purpose="Shorten synthetic abstract",
    )
    text = ledger.read_text(encoding="utf-8")
    assert result_marker not in text
    schema = json.loads(
        (ROOT / "schemas/disclosure_ledger.schema.json").read_text(encoding="utf-8")
    )
    Draft202012Validator(schema).validate(json.loads(text))


def test_local_only_rejects_external_host(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="LOCAL_ONLY"):
        append_disclosure(
            tmp_path / "ledger.json",
            session_id="s1",
            task_type="ABSTRACT_REVISION",
            model_host="remote",
            model_name=None,
            privacy_mode="LOCAL_ONLY",
            disclosed_objects={"abstract": "synthetic"},
            purpose="test",
        )


def test_plan_interpretation_unsupported_and_author_input() -> None:
    assert classify_finding("abstract.max_words", "FAIL") == "LLM_PROPOSAL_ALLOWED"
    assert classify_finding("author_contributions.required", "FAIL") == "AUTHOR_INPUT_REQUIRED"
    assert classify_finding("equation.edit", "FAIL") == "FORBIDDEN_AUTOMATIC"
    assert classify_finding("figures.separate", "FAIL") == "MANUAL_REVIEW_REQUIRED"
    assert classify_finding("references.max_count", "PARTIAL") == "PROFILE_UNCERTAIN"


def test_verification_gate_stops_packaging() -> None:
    good = {
        "transformation_verification_status": "VERIFIED_CANDIDATE",
        "unexpected_changes": [],
        "failure_reasons": [],
    }
    assert verification_allows_packaging(good)
    assert not verification_allows_packaging(good | {"unexpected_changes": ["body changed"]})
    assert not verification_allows_packaging(
        good | {"transformation_verification_status": "FAILED"}
    )


def test_private_workspace_patterns_and_public_secret_scan() -> None:
    ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    for directory in ("/private/", "/sessions/", "/payloads/", "/approvals/", "/real-run/"):
        assert directory in ignore
    tracked_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in (ROOT / "docs").rglob("*")
        if path.is_file()
    )
    assert "CONFIDENTIAL_RESULT_" + "A7F9" not in tracked_text
    assert "PRIVATE_AUTHOR_EMAIL_" + "X91" not in tracked_text
