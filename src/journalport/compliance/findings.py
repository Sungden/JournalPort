"""Stable IDs and template-only finding explanations."""

from __future__ import annotations

import hashlib
import json

from journalport.profiles.models import JSONValue, ProfileRule


def finding_id(rule_id: str, object_ids: tuple[str, ...], profile_hash: str, context: str) -> str:
    payload = json.dumps(
        [rule_id, sorted(object_ids), profile_hash, context],
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode()
    return "finding:" + hashlib.sha256(payload).hexdigest()[:24]


def message_for(status: str, rule: ProfileRule, current: JSONValue, reason: str = "") -> str:
    if status == "PASS":
        return f"{rule.target} satisfies {rule.operator} {rule.value!r}; observed {current!r}."
    if status in {"BLOCKED", "WARNING"}:
        return (
            f"{rule.target} does not satisfy {rule.operator} {rule.value!r}; observed {current!r}."
        )
    if status == "NOT_APPLICABLE":
        return f"{rule.rule_id} is explicitly not applicable."
    if status == "UNKNOWN":
        return f"{rule.rule_id} could not be determined: {reason}. Manual review is required."
    return f"{rule.rule_id} evaluation failed: {reason}."


def action_for(status: str) -> str:
    if status == "PASS" or status == "NOT_APPLICABLE":
        return "No action required."
    if status == "UNKNOWN":
        return "Review the rule, applicability, and missing evidence manually."
    if status == "EVALUATION_ERROR":
        return "Correct the profile or canonical input before claiming readiness."
    return "Review the manuscript against the cited official requirement; no change is applied."
