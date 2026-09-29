from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _shared.runtime import fail, run_cli, write_record


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a read-only JournalPort audit")
    parser.add_argument("manuscript", type=Path)
    parser.add_argument("--journal", required=True)
    parser.add_argument("--article-type", default="article")
    parser.add_argument("--profile-version", default="1.1.0")
    parser.add_argument("--profiles", type=Path, default=Path("journal_profiles"))
    parser.add_argument("--output", type=Path, default=Path("journalport-audit"))
    parser.add_argument("--record", type=Path, default=Path("skill_run.json"))
    args = parser.parse_args()
    command = [
        "audit",
        str(args.manuscript),
        "--journal",
        args.journal,
        "--article-type",
        args.article_type,
        "--profile-version",
        args.profile_version,
        "--profiles",
        str(args.profiles),
        "--output",
        str(args.output),
        "--format",
        "both",
    ]
    result = run_cli(command)
    status = "AUDIT_COMPLETE" if result.returncode == 0 else "AUDIT_BLOCKED"
    write_record(
        args.record,
        skill_id="journal-audit",
        inputs=[args.manuscript],
        outputs=[args.output],
        commands=[command],
        final_status=status,
        manual_review_items=[]
        if result.returncode == 0
        else [result.stderr.strip() or "audit failed closed"],
    )
    if result.returncode:
        fail(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
