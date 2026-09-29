from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _shared.runtime import fail, run_cli, write_record


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the approval-gated JournalPort transfer flow")
    parser.add_argument("manuscript", type=Path)
    parser.add_argument("--journal", required=True)
    parser.add_argument("--article-type", default="article")
    parser.add_argument("--profile-version", default="1.1.0")
    parser.add_argument("--profiles", type=Path, default=Path("journal_profiles"))
    parser.add_argument("--output", type=Path, default=Path("journalport-transfer"))
    parser.add_argument("--record", type=Path)
    args = parser.parse_args()
    record = args.record or args.output / "skill_run.json"
    common = [
        "--journal",
        args.journal,
        "--article-type",
        args.article_type,
        "--profile-version",
        args.profile_version,
        "--profiles",
        str(args.profiles),
    ]
    audit_dir, plan_dir, candidate_dir, verify_dir = (
        args.output / "audit",
        args.output / "plan",
        args.output / "candidate",
        args.output / "verification",
    )
    commands: list[list[str]] = []
    audit = ["audit", str(args.manuscript), *common, "--output", str(audit_dir), "--format", "json"]
    commands.append(audit)
    result = run_cli(audit)
    if result.returncode:
        write_record(
            record,
            skill_id="journal-transfer",
            inputs=[args.manuscript],
            outputs=[args.output],
            commands=commands,
            final_status="AUDIT_BLOCKED",
            manual_review_items=["audit failed closed"],
        )
        fail(result)
    plan = ["plan", str(args.manuscript), *common, "--output", str(plan_dir)]
    commands.append(plan)
    result = run_cli(plan)
    if result.returncode:
        fail(result)
    plan_path = plan_dir / "transformation_plan.json"
    plan_value = json.loads(plan_path.read_text(encoding="utf-8"))
    manual = [
        item["action_id"]
        for item in plan_value["actions"]
        if item["classification"] in {"AUTHOR_APPROVAL_REQUIRED", "FORBIDDEN_AUTOMATIC"}
    ]
    if manual:
        write_record(
            record,
            skill_id="journal-transfer",
            inputs=[args.manuscript],
            outputs=[audit_dir, plan_dir],
            commands=commands,
            final_status="APPROVAL_REQUIRED",
            manual_review_items=manual,
            profile_hash=plan_value["resolved_profile_hash"],
        )
        return 2
    apply_command = [
        "apply",
        str(plan_path),
        "--profiles",
        str(args.profiles),
        "--output",
        str(candidate_dir),
    ]
    commands.append(apply_command)
    result = run_cli(apply_command)
    if result.returncode:
        fail(result)
    candidates = list(candidate_dir.glob("*.docx")) + list(candidate_dir.glob("*.tex"))
    if len(candidates) != 1:
        raise SystemExit("expected exactly one transformed candidate")
    verify = [
        "verify",
        "--source",
        str(args.manuscript),
        "--candidate",
        str(candidates[0]),
        "--plan",
        str(plan_path),
        "--log",
        str(candidate_dir / "transformation_log.json"),
        "--manifest",
        str(candidate_dir / "candidate_manifest.json"),
        "--report-before",
        str(plan_dir / "compliance_report.json"),
        "--profiles",
        str(args.profiles),
        "--output",
        str(verify_dir),
    ]
    commands.append(verify)
    result = run_cli(verify)
    status = "VERIFIED_CANDIDATE" if result.returncode == 0 else "VERIFICATION_FAILED"
    write_record(
        record,
        skill_id="journal-transfer",
        inputs=[args.manuscript],
        outputs=[args.output],
        commands=commands,
        final_status=status,
        manual_review_items=[] if result.returncode == 0 else ["independent verification failed"],
        profile_hash=plan_value["resolved_profile_hash"],
    )
    if result.returncode:
        fail(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
