"""Local-first contracts and safeguards for agent-orchestrated journal transfer.

This module does not generate prose or edit manuscripts.  It validates agent proposals,
records minimized disclosure metadata, and persists resumable session state.  M10 remains
the only authoritative approval, execution, and verification path.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal, cast

from journalport.transform.hashing import canonical_hash

PrivacyMode = Literal["LOCAL_ONLY", "CODEX_HOSTED", "REMOTE_AGENT"]
SessionStatus = Literal[
    "INITIALIZED",
    "AUDITED",
    "PLAN_READY",
    "WAITING_FOR_AUTHOR_INPUT",
    "WAITING_FOR_APPROVAL",
    "APPROVED",
    "APPLIED",
    "VERIFIED",
    "PACKAGE_READY",
    "COMPLETE",
    "BLOCKED",
]

_TRANSITIONS: dict[str, set[str]] = {
    "INITIALIZED": {"AUDITED", "BLOCKED"},
    "AUDITED": {"PLAN_READY", "BLOCKED"},
    "PLAN_READY": {"WAITING_FOR_AUTHOR_INPUT", "WAITING_FOR_APPROVAL", "APPROVED", "BLOCKED"},
    "WAITING_FOR_AUTHOR_INPUT": {"WAITING_FOR_AUTHOR_INPUT", "WAITING_FOR_APPROVAL", "BLOCKED"},
    "WAITING_FOR_APPROVAL": {"WAITING_FOR_APPROVAL", "APPROVED", "BLOCKED"},
    "APPROVED": {"APPLIED", "BLOCKED"},
    "APPLIED": {"VERIFIED", "BLOCKED"},
    "VERIFIED": {"PACKAGE_READY", "COMPLETE", "BLOCKED"},
    "PACKAGE_READY": {"COMPLETE", "BLOCKED"},
    "COMPLETE": set(),
    "BLOCKED": set(),
}


def _now() -> str:
    return datetime.now(UTC).isoformat()


@dataclass(frozen=True, slots=True)
class TransferSession:
    schema_version: str
    session_id: str
    created_at: str
    source_manuscript_path: str
    source_manuscript_hash: str
    source_journal: str | None
    target_journal: str
    article_type: str
    privacy_mode: PrivacyMode
    profile_version: str
    compliance_report_path: str | None = None
    transformation_plan_path: str | None = None
    agent_proposals: tuple[str, ...] = ()
    author_inputs: tuple[str, ...] = ()
    approvals: tuple[str, ...] = ()
    execution_result: str | None = None
    verification_result: str | None = None
    package_result: str | None = None
    disclosure_ledger_path: str | None = None
    status: SessionStatus = "INITIALIZED"

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], json.loads(json.dumps(asdict(self))))

    def transition(self, status: SessionStatus) -> TransferSession:
        if status not in _TRANSITIONS[self.status]:
            raise ValueError(f"invalid session transition: {self.status} -> {status}")
        return replace(self, status=status)


def save_session(session: TransferSession, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(session.to_dict(), indent=2) + "\n", encoding="utf-8")
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def load_session(path: Path) -> TransferSession:
    value = json.loads(path.read_text(encoding="utf-8"))
    for field in ("agent_proposals", "author_inputs", "approvals"):
        value[field] = tuple(value[field])
    return TransferSession(**value)


@dataclass(frozen=True, slots=True)
class ScientificDiffReport:
    schema_version: str
    original_hash: str
    proposed_hash: str
    numeric_changes: tuple[str, ...]
    percentage_changes: tuple[str, ...]
    p_value_changes: tuple[str, ...]
    confidence_interval_changes: tuple[str, ...]
    date_changes: tuple[str, ...]
    gene_protein_changes: tuple[str, ...]
    accession_changes: tuple[str, ...]
    doi_changes: tuple[str, ...]
    url_changes: tuple[str, ...]
    citation_changes: tuple[str, ...]
    figure_reference_changes: tuple[str, ...]
    table_reference_changes: tuple[str, ...]
    equation_changes: tuple[str, ...]
    reference_identifier_changes: tuple[str, ...]
    status: Literal["SAFE", "REVIEW_REQUIRED"]

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], json.loads(json.dumps(asdict(self))))


_TOKEN_PATTERNS = {
    "percentage_changes": r"\b\d+(?:\.\d+)?\s?%",
    "p_value_changes": r"\bp\s*[<=>]\s*\.?\d+(?:\.\d+)?(?:e-?\d+)?",
    "confidence_interval_changes": r"\b(?:95%\s*)?CI\s*[:=]?\s*[\[(]?[-+]?\d+(?:\.\d+)?\s*[,–-]\s*[-+]?\d+(?:\.\d+)?",
    "date_changes": r"\b(?:19|20)\d{2}(?:[-/]\d{1,2}(?:[-/]\d{1,2})?)?\b",
    "accession_changes": r"\b(?:GSE|SRR|ERR|DRR|PRJNA|NCT)\d+\b",
    "doi_changes": r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+",
    "url_changes": r"https?://[^\s)>]+",
    "citation_changes": r"(?:\[(?:\d+(?:\s*[-,]\s*\d+)*)\]|\([A-Z][A-Za-z-]+(?:\s+et\s+al\.)?,?\s+(?:19|20)\d{2}\))",
    "figure_reference_changes": r"\b(?:Fig(?:ure)?\.?)\s*[A-Z]?\d+[A-Za-z]?\b",
    "table_reference_changes": r"\bTable\s+[A-Z]?\d+[A-Za-z]?\b",
    "equation_changes": r"(?:[=±×÷]|\b(?:alpha|beta|gamma|delta|theta|lambda)\b)",
    "reference_identifier_changes": r"\b(?:PMID|ISBN|arXiv)\s*[:#]?\s*[\w./-]+",
    "gene_protein_changes": r"\b[A-Z][A-Z0-9-]{2,9}\b",
    "numeric_changes": r"(?<![\w.])[-+]?\d+(?:\.\d+)?(?:e[-+]?\d+)?(?![\w.])",
}


def _changed_tokens(original: str, proposed: str, pattern: str) -> tuple[str, ...]:
    flags = re.IGNORECASE if "doi" in pattern.lower() or "http" in pattern.lower() else 0
    before = set(re.findall(pattern, original, flags))
    after = set(re.findall(pattern, proposed, flags))
    return tuple(
        sorted({f"removed:{v}" for v in before - after} | {f"added:{v}" for v in after - before})
    )


def scientific_diff(original: str, proposed: str) -> ScientificDiffReport:
    values = {
        name: _changed_tokens(original, proposed, pattern)
        for name, pattern in _TOKEN_PATTERNS.items()
    }
    status: Literal["SAFE", "REVIEW_REQUIRED"] = (
        "REVIEW_REQUIRED" if any(values.values()) else "SAFE"
    )
    return ScientificDiffReport(
        schema_version="1.0.0",
        original_hash=canonical_hash(original),
        proposed_hash=canonical_hash(proposed),
        status=status,
        **values,
    )


@dataclass(frozen=True, slots=True)
class AgentProposal:
    schema_version: str
    proposal_id: str
    session_id: str
    rule_id: str
    target_object_id: str
    operation: str
    original_hash: str
    proposed_text: str
    proposed_text_hash: str
    rationale: str
    source_evidence: tuple[str, ...]
    risk_level: Literal["LOW", "MEDIUM", "HIGH", "PROHIBITED"]
    scientific_diff_flags: tuple[str, ...]
    requires_author_approval: bool
    approval_status: Literal["PENDING", "APPROVED", "REJECTED"]
    created_by: str
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], json.loads(json.dumps(asdict(self))))


def build_proposal(
    *,
    proposal_id: str,
    session_id: str,
    rule_id: str,
    target_object_id: str,
    operation: str,
    original_text: str,
    proposed_text: str,
    rationale: str,
    source_evidence: tuple[str, ...],
    created_by: str,
    baseline_risk: Literal["LOW", "MEDIUM", "HIGH"] = "MEDIUM",
) -> tuple[AgentProposal, ScientificDiffReport]:
    report = scientific_diff(original_text, proposed_text)
    risk: Literal["LOW", "MEDIUM", "HIGH", "PROHIBITED"] = baseline_risk
    if report.status == "REVIEW_REQUIRED":
        risk = "HIGH"
    flags = tuple(
        name for name, value in report.to_dict().items() if name.endswith("_changes") and value
    )
    proposal = AgentProposal(
        schema_version="1.0.0",
        proposal_id=proposal_id,
        session_id=session_id,
        rule_id=rule_id,
        target_object_id=target_object_id,
        operation=operation,
        original_hash=canonical_hash(original_text),
        proposed_text=proposed_text,
        proposed_text_hash=canonical_hash(proposed_text),
        rationale=rationale,
        source_evidence=source_evidence,
        risk_level=risk,
        scientific_diff_flags=flags,
        requires_author_approval=True,
        approval_status="PENDING",
        created_by=created_by,
        created_at=_now(),
    )
    return proposal, report


@dataclass(frozen=True, slots=True)
class DisclosureEntry:
    timestamp: str
    session_id: str
    task_type: str
    model_host: str
    model_name_if_known: str | None
    privacy_mode: PrivacyMode
    disclosed_object_ids: tuple[str, ...]
    disclosed_content_hashes: tuple[str, ...]
    purpose: str
    approximate_size_or_token_count: int
    full_document_disclosed: bool


def append_disclosure(
    ledger_path: Path,
    *,
    session_id: str,
    task_type: str,
    model_host: str,
    model_name: str | None,
    privacy_mode: PrivacyMode,
    disclosed_objects: dict[str, str],
    purpose: str,
    full_document_disclosed: bool = False,
) -> DisclosureEntry:
    if privacy_mode == "LOCAL_ONLY" and model_host != "local":
        raise ValueError("LOCAL_ONLY forbids external model disclosure")
    entry = DisclosureEntry(
        timestamp=_now(),
        session_id=session_id,
        task_type=task_type,
        model_host=model_host,
        model_name_if_known=model_name,
        privacy_mode=privacy_mode,
        disclosed_object_ids=tuple(disclosed_objects),
        disclosed_content_hashes=tuple(
            canonical_hash(value) for value in disclosed_objects.values()
        ),
        purpose=purpose,
        approximate_size_or_token_count=sum(
            len(value.split()) for value in disclosed_objects.values()
        ),
        full_document_disclosed=full_document_disclosed,
    )
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    ledger: dict[str, Any] = (
        json.loads(ledger_path.read_text(encoding="utf-8"))
        if ledger_path.exists()
        else {"schema_version": "1.0.0", "entries": []}
    )
    entries = cast(list[dict[str, Any]], ledger["entries"])
    entries.append(asdict(entry))
    ledger_path.write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8")
    return entry


def minimize_abstract_context(
    abstract: str, *, target_words: int, target_journal: str, rule_text: str
) -> dict[str, Any]:
    """Return only task-required context; callers must separately record disclosure."""
    return {
        "abstract": abstract,
        "current_word_count": len(abstract.split()),
        "target_word_count": target_words,
        "target_journal": target_journal,
        "rule": rule_text,
    }


def classify_finding(rule_id: str, status: str) -> str:
    lowered = rule_id.lower()
    if status in {"UNKNOWN", "PARTIAL", "STALE", "CONFLICTED"}:
        return "PROFILE_UNCERTAIN"
    if any(
        term in lowered
        for term in (
            "author_contribution",
            "competing_interest",
            "data_availability",
            "code_availability",
        )
    ):
        return "AUTHOR_INPUT_REQUIRED"
    if any(term in lowered for term in ("equation", "reference.removal", "scientific_content")):
        return "FORBIDDEN_AUTOMATIC"
    if any(term in lowered for term in ("title.max_words", "abstract.max_words")):
        return "LLM_PROPOSAL_ALLOWED"
    if status == "PASS":
        return "DETERMINISTIC_AUTOMATIC"
    return "MANUAL_REVIEW_REQUIRED"


def verification_allows_packaging(report: dict[str, Any]) -> bool:
    return (
        report.get("transformation_verification_status") == "VERIFIED_CANDIDATE"
        and report.get("unexpected_changes") == []
        and report.get("failure_reasons") == []
    )
