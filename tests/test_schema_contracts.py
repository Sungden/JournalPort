"""M0 contract tests; the core subset runs with the Python standard library."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "schemas"
EXPECTED = {
    "canonical_manuscript.schema.json",
    "journal_profile.schema.json",
    "compliance_rule.schema.json",
    "compliance_report.schema.json",
    "transformation_plan.schema.json",
    "manifest.schema.json",
    "resolved_journal_profile.schema.json",
    "profile_conflict_report.schema.json",
    "compliance_finding.schema.json",
    "evaluation_trace.schema.json",
    "transformation_action.schema.json",
    "approval.schema.json",
    "transformation_log.schema.json",
    "candidate_manifest.schema.json",
    "verification_report.schema.json",
    "verification_finding.schema.json",
    "compliance_delta.schema.json",
    "submission_artifact.schema.json",
    "submission_package_plan.schema.json",
    "submission_manifest.schema.json",
    "package_readiness_report.schema.json",
    "source_record.schema.json",
    "evidence_unit.schema.json",
    "candidate_rule.schema.json",
    "candidate_profile.schema.json",
    "extraction_run.schema.json",
    "profile_review_queue.schema.json",
    "profile_diff.schema.json",
    "skill_registry.schema.json",
    "skill_run.schema.json",
    "transfer_session.schema.json",
    "agent_proposal.schema.json",
    "scientific_diff.schema.json",
    "disclosure_ledger.schema.json",
    "transfer_matrix.schema.json",
    "format_transformation_plan.schema.json",
    "format_transformation_report.schema.json",
    "full_format_plan.schema.json",
    "format_coverage_report.schema.json",
    "render_validation_report.schema.json",
}


def load_schemas() -> dict[str, dict]:
    return {
        path.name: json.loads(path.read_text(encoding="utf-8"))
        for path in SCHEMA_DIR.glob("*.json")
    }


class SchemaContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schemas = load_schemas()

    def test_exact_m0_schema_set_exists_and_parses(self) -> None:
        self.assertEqual(set(self.schemas), EXPECTED)

    def test_all_schemas_use_draft_2020_12_and_versioned_ids(self) -> None:
        for name, schema in self.schemas.items():
            with self.subTest(schema=name):
                self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
                self.assertTrue(schema["$id"].startswith("https://journalport.org/schemas/v"))
                self.assertEqual(schema["type"], "object")
                self.assertFalse(schema["additionalProperties"])
                self.assertIn("schema_version", schema["required"])

    def test_local_and_cross_schema_references_have_targets(self) -> None:
        ids = {schema["$id"] for schema in self.schemas.values()}
        names = set(self.schemas)

        def walk(value: object, root: dict) -> None:
            if isinstance(value, dict):
                ref = value.get("$ref")
                if isinstance(ref, str):
                    if ref.startswith("#/$defs/"):
                        self.assertIn(ref.removeprefix("#/$defs/"), root.get("$defs", {}))
                    elif not ref.startswith("https://"):
                        self.assertIn(ref, names)
                    else:
                        self.assertIn(ref.split("#", 1)[0], ids)
                for child in value.values():
                    walk(child, root)
            elif isinstance(value, list):
                for child in value:
                    walk(child, root)

        for schema in self.schemas.values():
            walk(schema, schema)

    def test_safety_vocabularies_are_closed(self) -> None:
        rule = self.schemas["compliance_rule.schema.json"]
        self.assertEqual(
            set(rule["properties"]["autofix_class"]["enum"]),
            {
                "SAFE_AUTOMATIC",
                "CONTENT_PRESERVING_AUTOMATIC",
                "AUTHOR_APPROVAL_REQUIRED",
                "FORBIDDEN_AUTOMATIC",
                "NONE",
            },
        )
        profile = self.schemas["journal_profile.schema.json"]
        self.assertEqual(
            set(profile["properties"]["status"]["enum"]),
            {"VERIFIED", "PARTIAL", "STALE", "CONFLICTED", "UNKNOWN"},
        )
        manifest = self.schemas["manifest.schema.json"]
        self.assertEqual(
            manifest["properties"]["verification"]["properties"]["independent"], {"const": True}
        )

    def test_metaschema_and_approval_condition_when_jsonschema_available(self) -> None:
        try:
            from jsonschema import Draft202012Validator
        except ImportError:
            self.skipTest("install the dev extra to enable Draft 2020-12 meta-schema validation")

        for name, schema in self.schemas.items():
            with self.subTest(schema=name):
                Draft202012Validator.check_schema(schema)

        action_schema = self.schemas["transformation_action.schema.json"]
        unsafe_action = {
            "action_id": "action_001",
            "rule_id": "abstract.max_words",
            "source_object_ids": ["sec_abstract"],
            "current_state": {"words": 238},
            "target_state": {"words": 200},
            "proposed_action": "Shorten scientific prose",
            "classification": "AUTHOR_APPROVAL_REQUIRED",
            "reason": "Journal limit",
            "journal_evidence": ["src:instructions"],
            "approval_required": False,
            "approval_status": "NOT_REQUIRED",
        }
        errors = list(Draft202012Validator(action_schema).iter_errors(unsafe_action))
        self.assertGreaterEqual(len(errors), 1, "semantic action must not bypass approval")


if __name__ == "__main__":
    unittest.main()
