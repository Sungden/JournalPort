"""Deterministic M2.5 semantic profile migration."""

from __future__ import annotations

import json
from pathlib import Path
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


def migrate_tree(root: Path, decisions_path: Path, report_path: Path) -> list[Path]:
    decisions = json.loads(decisions_path.read_text(encoding="utf-8"))
    written: list[Path] = []
    reports: list[dict[str, Any]] = []
    for source in sorted(root.rglob("*1.0.0.json")):
        if source.name not in {"1.0.0.json", "journal-1.0.0.json", "article-1.0.0.json"}:
            continue
        value = json.loads(source.read_text(encoding="utf-8"))
        migrated, report = migrate_profile(value, decisions)
        target = source.with_name(source.name.replace("1.0.0", "1.1.0"))
        target.write_text(
            json.dumps(migrated, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        written.append(target)
        reports.append(report)
    report_path.write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "migration_id": decisions["migration_id"],
                "profiles": reports,
            },
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return written
