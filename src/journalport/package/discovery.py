"""Bounded discovery for explicitly supplied author artifacts."""

from __future__ import annotations

from pathlib import Path


def classify_artifact(path: Path) -> str:
    name = path.stem.lower().replace("-", "_").replace(" ", "_")
    patterns = (
        ("cover", "COVER_LETTER"),
        ("title_page", "TITLE_PAGE"),
        ("figure", "FIGURE"),
        ("fig", "FIGURE"),
        ("table", "TABLE"),
        ("supp", "SUPPLEMENTARY_INFORMATION"),
        ("checklist", "REPORTING_CHECKLIST"),
        ("graphical", "GRAPHICAL_ABSTRACT"),
        ("highlight", "HIGHLIGHTS"),
        ("ethics", "ETHICS_DOCUMENT"),
        ("consent", "CONSENT_DOCUMENT"),
    )
    for token, artifact_type in patterns:
        if token in name:
            return artifact_type
    return "OTHER_REQUIRED_FILE"


def discover_explicit(paths: tuple[Path, ...]) -> tuple[tuple[Path, str], ...]:
    found: list[tuple[Path, str]] = []
    for supplied in paths:
        path = supplied.resolve()
        candidates = sorted(path.iterdir()) if path.is_dir() else [path]
        for candidate in candidates:
            if candidate.is_file() and not candidate.is_symlink():
                found.append((candidate, classify_artifact(candidate)))
    return tuple(found)
