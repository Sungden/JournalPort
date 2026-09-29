"""Configurable profile freshness calculation."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from .models import Profile


def parse_timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise ValueError("timestamps must include a UTC offset")
    return parsed.astimezone(UTC)


def is_stale(profile: Profile, *, at: datetime | None = None) -> bool:
    now = (at or datetime.now(UTC)).astimezone(UTC)
    verified = parse_timestamp(profile.last_verified_at)
    return now > verified + timedelta(days=profile.freshness_window_days)
