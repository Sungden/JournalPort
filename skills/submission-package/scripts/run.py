from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _shared.runtime import fail, run_cli, write_record


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build and verify a JournalPort submission package"
    )
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--verification-report", type=Path, required=True)
    parser.add_argument("--compliance-report", type=Path, required=True)
    parser.add_argument("--journal", required=True)
    parser.add_argument("--article-type", default="article")
    parser.add_argument("--profile-version", default="1.1.0")
    parser.add_argument("--profiles", type=Path, default=Path("journal_profiles"))
    parser.add_argument("--artifact", type=Path, action="append", default=[])
    parser.add_argument("--output", type=Path, default=Path("journalport-package"))
    parser.add_argument("--record", type=Path)
    args = parser.parse_args()
    record = args.record or args.output / "skill_run.json"
    plan_dir, package_dir = args.output / "plan", args.output / "package"
    plan = [
        "package",
        "plan",
        "--candidate",
        str(args.candidate),
        "--verification-report",
        str(args.verification_report),
        "--compliance-report",
        str(args.compliance_report),
        "--journal",
        args.journal,
        "--article-type",
        args.article_type,
        "--profile-version",
        args.profile_version,
        "--profiles",
        str(args.profiles),
        "--output",
        str(plan_dir),
    ]
    for artifact in args.artifact:
        plan.extend(["--artifact", str(artifact)])
    commands = [plan]
    result = run_cli(plan)
    if result.returncode:
        write_record(
            record,
            skill_id="submission-package",
            inputs=[
                args.candidate,
                args.verification_report,
                args.compliance_report,
                *args.artifact,
            ],
            outputs=[plan_dir],
            commands=commands,
            final_status="PACKAGE_BLOCKED",
            manual_review_items=[result.stderr.strip() or "author input or review required"],
        )
        return 2
    plan_path = plan_dir / "submission_package_plan.json"
    build = ["package", "build", str(plan_path), "--output", str(package_dir)]
    commands.append(build)
    result = run_cli(build)
    if result.returncode:
        fail(result)
    verify = ["package", "verify", str(package_dir), "--profiles", str(args.profiles)]
    commands.append(verify)
    result = run_cli(verify)
    report_path = package_dir / "package_readiness_report.json"
    status = "PACKAGE_VERIFICATION_FAILED"
    if report_path.exists():
        status = json.loads(report_path.read_text(encoding="utf-8"))["final_package_status"]
    write_record(
        record,
        skill_id="submission-package",
        inputs=[args.candidate, args.verification_report, args.compliance_report, *args.artifact],
        outputs=[package_dir],
        commands=commands,
        final_status=status,
        manual_review_items=[] if result.returncode == 0 else ["package verification failed"],
    )
    if result.returncode:
        fail(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
