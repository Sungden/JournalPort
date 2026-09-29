"""Evaluation trace projection from authoritative findings."""

from __future__ import annotations

from dataclasses import asdict

from .models import ComplianceReport


def evaluation_trace(report: ComplianceReport) -> dict[str, object]:
    return {
        "schema_version": "1.0.0",
        "report_hash": report.report_hash,
        "entries": [
            {
                "finding_id": item.finding_id,
                "rule_id": item.rule_id,
                "manuscript_object_ids": list(item.affected_object_ids),
                "profile_id": item.profile_id,
                "source_provenance": [asdict(ref) for ref in item.source_provenance],
                "evaluation_method": item.evaluation_method,
                "evaluator_version": item.evaluator_version,
                "status": item.status,
            }
            for item in report.findings
        ],
    }
