from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _shared.runtime import ensure_draft_destination, fail, run_cli, write_record


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a JournalPort draft profile review bundle")
    parser.add_argument("--journal", required=True)
    parser.add_argument("--article-type", default="article")
    parser.add_argument("--snapshot", type=Path)
    parser.add_argument("--profiles", type=Path, default=Path("journal_profiles"))
    parser.add_argument("--output", type=Path, default=Path("profile_drafts"))
    parser.add_argument("--record", type=Path, default=Path("skill_run.json"))
    args = parser.parse_args()
    ensure_draft_destination(args.output, args.profiles)
    command = [
        "profile",
        "refresh-draft",
        "--journal",
        args.journal,
        "--article-type",
        args.article_type,
        "--profiles",
        str(args.profiles),
        "--output",
        str(args.output),
    ]
    if args.snapshot:
        command.extend(["--snapshot", str(args.snapshot)])
    result = run_cli(command)
    if result.returncode:
        write_record(
            args.record,
            skill_id="journal-profile",
            inputs=[args.snapshot] if args.snapshot else [],
            outputs=[],
            commands=[command],
            final_status="MANUAL_REVIEW_REQUIRED",
            manual_review_items=[result.stderr.strip() or "profile refresh failed closed"],
        )
        fail(result)
    write_record(
        args.record,
        skill_id="journal-profile",
        inputs=[args.snapshot] if args.snapshot else [],
        outputs=[args.output],
        commands=[command],
        final_status="DRAFT_REVIEW_REQUIRED",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
