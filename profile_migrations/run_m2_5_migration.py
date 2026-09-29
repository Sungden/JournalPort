from pathlib import Path

from journalport.profiles.migration import migrate_tree

ROOT = Path(__file__).resolve().parents[1]

if __name__ == "__main__":
    files = migrate_tree(
        ROOT / "journal_profiles",
        ROOT / "profile_migrations/m2_5_semantic_decisions.json",
        ROOT / "profile_migrations/profile_migration_report.json",
    )
    print(f"migrated {len(files)} profiles")
