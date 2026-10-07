"""Deterministic M2.5 semantic profile migration."""

from __future__ import annotations

import json
from typing import Any


class ProfileMigrationError(ValueError):
    pass


def migrate_profile(
    value: dict[str, Any], decisions: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    if value["profile_version"] != "1.0.0" or value["schema_version"] != "2.0.0":
        raise ProfileMigrationError("migration accepts only profile 1.0.0 / schema 2.0.0")
    migrated = json.loads(json.dumps(value))
    migrated["schema_version"] = decisions["target_schema_version"]
    migrated["profile_version"] = decisions["target_profile_version"]
    migrated["source_snapshot_version"] = decisions["target_profile_version"]
    for parent in migrated["parents"]:
        parent["profile_version"] = decisions["target_profile_version"]
    changes: list[dict[str, Any]] = []
    overrides = decisions.get("profile_overrides", {}).get(value["profile_id"], {})
    for rule in migrated["rules"]:
        rule_id = rule["rule_id"]
        if rule_id not in decisions["rules"]:
            raise ProfileMigrationError(f"missing semantic decision for {rule_id}")
        policy = decisions["rules"][rule_id] | overrides.get(rule_id, {})
        fields = {
            name: policy[name]
            for name in (
                "applicability_mode",
                "critical_for_readiness",
                "machine_checkable",
                "evaluation_scope",
            )
        }
        before = {name: rule.get(name, "<absent>") for name in fields}
        rule.update(fields)
        changes.append(
            {
                "rule_id": rule_id,
                "fields_before": before,
                "fields_after": fields,
                "journalport_policy_decision": policy["decision"],
                "evidence_changed": False,
                "status_changed": False,
            }
        )
    report = {
        "schema_version": "1.0.0",
        "migration_id": decisions["migration_id"],
        "profile_id": value["profile_id"],
        "old_version": value["profile_version"],
        "new_version": migrated["profile_version"],
        "old_schema_version": value["schema_version"],
        "new_schema_version": migrated["schema_version"],
        "rules_changed": changes,
        "fields_added": ["applicability_mode", "critical_for_readiness", "evaluation_scope"],
        "evidence_changes": [],
        "manual_decisions": [item["journalport_policy_decision"] for item in changes],
    }
    return migrated, report
