"""Secure JSON profile loading and pinned-version registry."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from .models import Profile, profile_from_dict
from .validation import validate_profile

MAX_PROFILE_BYTES = 1_000_000


class ProfileLoadError(ValueError):
    pass


def _default_schema_path() -> Path:
    installed = Path(__file__).resolve().parents[1] / "schemas" / "journal_profile.schema.json"
    source_checkout = (
        Path(__file__).resolve().parents[3] / "schemas" / "journal_profile.schema.json"
    )
    return installed if installed.is_file() else source_checkout


def load_profile(
    path: str | Path, *, schema_path: str | Path | None = None, max_bytes: int = MAX_PROFILE_BYTES
) -> Profile:
    source = Path(path)
    if source.suffix.lower() != ".json":
        raise ProfileLoadError(
            "M2 accepts JSON profiles only; executable or ambiguous formats are rejected"
        )
    if source.stat().st_size > max_bytes:
        raise ProfileLoadError("profile exceeds configured size limit")
    try:
        value = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ProfileLoadError(f"cannot load profile {source}: {exc}") from exc
    schema_file = Path(schema_path) if schema_path else _default_schema_path()
    schema = json.loads(schema_file.read_text(encoding="utf-8"))
    errors = sorted(
        Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(value),
        key=lambda item: list(item.path),
    )
    if errors:
        raise ProfileLoadError(
            "schema validation failed: " + "; ".join(error.message for error in errors[:10])
        )
    profile = profile_from_dict(value)
    blocking = [
        issue for issue in validate_profile(profile, check_freshness=False) if issue.blocking
    ]
    if blocking:
        raise ProfileLoadError(
            "semantic validation failed: " + "; ".join(issue.code for issue in blocking)
        )
    return profile


@dataclass(slots=True)
class ProfileRegistry:
    _profiles: dict[tuple[str, str], Profile] = field(default_factory=dict)

    def add(self, profile: Profile) -> None:
        key = (profile.profile_id, profile.profile_version)
        if key in self._profiles:
            raise ProfileLoadError(f"duplicate pinned profile: {key}")
        self._profiles[key] = profile

    def get(self, profile_id: str, profile_version: str) -> Profile:
        try:
            return self._profiles[(profile_id, profile_version)]
        except KeyError as exc:
            raise ProfileLoadError(
                f"missing pinned profile {profile_id}@{profile_version}"
            ) from exc

    @classmethod
    def from_directory(cls, root: str | Path) -> ProfileRegistry:
        base = Path(root).resolve()
        registry = cls()
        for path in sorted(base.rglob("*.json")):
            if not path.resolve().is_relative_to(base):
                raise ProfileLoadError("profile path escaped registry root")
            registry.add(load_profile(path))
        return registry
