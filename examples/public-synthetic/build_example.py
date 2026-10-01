from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT))

from journalport.package.format_adapter import build_format_package, verify_format_package
from journalport.transform.format_engine import (
    apply_format_transformations,
    verify_format_transformations,
    write_format_reports,
)
from journalport.transform.format_models import FormatRuleTarget
from journalport.transform.format_planner import plan_format_transformations, write_format_plan
from tests.transformation.test_m12_format_engine import _m12_docx

ROOT = Path(__file__).resolve().parent
SOURCE = _m12_docx(ROOT / "synthetic_manuscript.docx")
TARGETS = (
    FormatRuleTarget(
        "figures.separate_files",
        True,
        "VERIFIED",
        ({"source_id": "synthetic-official-source", "evidence_id": "synthetic-rule"},),
        "HIGH",
        ("REVISION",),
    ),
)
PLAN = plan_format_transformations(
    SOURCE,
    current_state={"figures.separate_files": False},
    targets=TARGETS,
    target_journal="Synthetic Journal",
    profile_version="1.0.0",
    submission_stage="REVISION",
)
write_format_plan(PLAN, ROOT)
RESULT = apply_format_transformations(SOURCE, PLAN, ROOT / "transformed")
REPORT = verify_format_transformations(SOURCE, RESULT, PLAN)
write_format_reports(ROOT / "transformed", PLAN, RESULT, REPORT)
MANIFEST = build_format_package(RESULT, REPORT, ROOT / "submission-package")
PACKAGE_REPORT = verify_format_package(ROOT / "submission-package")
(ROOT / "audit_result.json").write_text(
    json.dumps(
        {
            "schema_version": "1.0.0",
            "source": "synthetic_manuscript.docx",
            "target_journal": "Synthetic Journal",
            "submission_stage": "REVISION",
            "finding": "embedded figures require separate-file extraction",
        },
        indent=2,
    )
    + "\n",
    encoding="utf-8",
)
(ROOT / "package_verification.json").write_text(
    json.dumps(PACKAGE_REPORT, indent=2) + "\n", encoding="utf-8"
)
assert REPORT.transformation_verification_status == "VERIFIED_CANDIDATE"
assert REPORT.unexpected_changes == () and REPORT.failure_reasons == ()
assert MANIFEST["package_status"] == "PACKAGE_READY"
assert PACKAGE_REPORT["package_integrity"] == "PASS"
