"""Explicit, pinned, deterministic profile inheritance resolution."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import replace

from .freshness import is_stale
from .hashing import resolved_hash
from .loader import ProfileLoadError, ProfileRegistry
from .models import (
    Profile,
    ProfileConflict,
    ProfileRef,
    ProfileRule,
    ResolutionTrace,
    ResolvedJournalProfile,
    RuleCandidate,
)


class ProfileResolutionError(ValueError):
    pass


def _walk(registry: ProfileRegistry, root: Profile) -> tuple[Profile, ...]:
    ordered: list[Profile] = []
    complete: set[tuple[str, str]] = set()
    active: list[tuple[str, str]] = []

    def visit(profile: Profile) -> None:
        key = (profile.profile_id, profile.profile_version)
        if key in active:
            cycle = " -> ".join(f"{item[0]}@{item[1]}" for item in active + [key])
            raise ProfileResolutionError(f"inheritance cycle: {cycle}")
        if key in complete:
            return
        active.append(key)
        for reference in sorted(
            profile.parents, key=lambda item: (item.profile_id, item.profile_version)
        ):
            try:
                parent = registry.get(reference.profile_id, reference.profile_version)
            except ProfileLoadError as exc:
                raise ProfileResolutionError(str(exc)) from exc
            visit(parent)
            if parent.precedence >= profile.precedence:
                raise ProfileResolutionError(
                    "parent precedence must be lower than child precedence"
                )
        active.pop()
        complete.add(key)
        ordered.append(profile)

    visit(root)
    return tuple(
        sorted(ordered, key=lambda item: (item.precedence, item.profile_id, item.profile_version))
    )


def _source_dates(profile: Profile, rule: ProfileRule) -> tuple[str, ...]:
    sources = {source.source_id: source for source in profile.sources}
    return tuple(
        sorted(
            {
                sources[ref.source_id].retrieved_at
                for ref in rule.provenance
                if ref.source_id in sources
            }
        )
    )


def resolve_profile(
    registry: ProfileRegistry,
    publisher: str,
    journal: str,
    article_type: str,
    pinned_versions: dict[str, str],
) -> ResolvedJournalProfile:
    for required in (publisher, journal, article_type):
        if required not in pinned_versions:
            raise ProfileResolutionError(f"missing pinned version for {required}")
    root = registry.get(article_type, pinned_versions[article_type])
    chain = _walk(registry, root)
    chain_ids = {profile.profile_id for profile in chain}
    if publisher not in chain_ids or journal not in chain_ids:
        raise ProfileResolutionError(
            "requested publisher/journal are not ancestors of article type"
        )
    for profile in chain:
        pinned = pinned_versions.get(profile.profile_id)
        if pinned != profile.profile_version:
            raise ProfileResolutionError(f"unpinned or mismatched dependency {profile.profile_id}")

    grouped: dict[str, list[RuleCandidate]] = defaultdict(list)
    profile_lookup = {profile.profile_id: profile for profile in chain}
    for profile in chain:
        for rule in profile.rules:
            grouped[rule.rule_id].append(
                RuleCandidate(rule, profile.profile_id, profile.profile_version, profile.precedence)
            )

    effective: list[ProfileRule] = []
    traces: list[ResolutionTrace] = []
    conflicts: list[ProfileConflict] = []
    for rule_id in sorted(grouped):
        candidates = tuple(
            sorted(
                grouped[rule_id],
                key=lambda item: (
                    item.precedence,
                    item.profile_id,
                    item.profile_version,
                    item.rule.rule_version,
                ),
            )
        )
        highest_precedence = candidates[-1].precedence
        highest = tuple(item for item in candidates if item.precedence == highest_precedence)
        values = {repr(item.rule.value) for item in highest}
        classification = "SELECTED"
        selected: RuleCandidate | None = None
        conflict_messages: tuple[str, ...] = ()
        if len(values) > 1:
            classification = "CONFLICT"
            conflict_messages = ("equal-precedence authoritative definitions disagree",)
            provenance = tuple(ref for item in highest for ref in item.rule.provenance)
            dates = tuple(
                date
                for item in highest
                for date in _source_dates(profile_lookup[item.profile_id], item.rule)
            )
            conflicts.append(
                ProfileConflict(
                    rule_id,
                    tuple(item.rule.value for item in highest),
                    provenance,
                    tuple(sorted(set(dates))),
                    highest_precedence,
                    "effective value is unresolved",
                )
            )
        else:
            selected = highest[0]
            if len(highest) > 1:
                classification = "DUPLICATE"
            lower = [item for item in candidates if item.precedence < highest_precedence]
            if len(highest) == 1 and lower:
                previous = lower[-1]
                if previous.rule.value == selected.rule.value:
                    classification = "REDUNDANT_OVERRIDE"
                elif selected.rule.override_of == rule_id and selected.rule.override_reason:
                    classification = "VALID_OVERRIDE"
                else:
                    classification = "CONFLICT"
                    conflict_messages = (
                        "higher-precedence value lacks explicit override declaration",
                    )
                    provenance = previous.rule.provenance + selected.rule.provenance
                    dates = _source_dates(
                        profile_lookup[previous.profile_id], previous.rule
                    ) + _source_dates(profile_lookup[selected.profile_id], selected.rule)
                    conflicts.append(
                        ProfileConflict(
                            rule_id,
                            (previous.rule.value, selected.rule.value),
                            provenance,
                            tuple(sorted(set(dates))),
                            highest_precedence,
                            "invalid override is unresolved",
                        )
                    )
                    selected = None
        if selected is not None:
            effective.append(selected.rule)
        traces.append(
            ResolutionTrace(
                rule_id,
                candidates,
                selected.profile_id if selected else None,
                selected.profile_version if selected else None,
                selected.rule.rule_version if selected else None,
                classification,
                selected.rule.override_reason if selected else None,
                conflict_messages,
                selected.rule.provenance if selected else (),
            )
        )

    statuses = {rule.status for rule in effective}
    if conflicts:
        status = "CONFLICTED"
    elif any(is_stale(profile) for profile in chain) or "STALE" in statuses:
        status = "STALE"
    elif statuses <= {"VERIFIED", "NOT_APPLICABLE"}:
        status = "VERIFIED"
    elif "UNKNOWN" in statuses or "PARTIAL" in statuses:
        status = "PARTIAL"
    else:
        status = "UNKNOWN"

    pins = tuple(ProfileRef(profile.profile_id, profile.profile_version) for profile in chain)
    preliminary = ResolvedJournalProfile(
        "1.0.0",
        "1.0.0",
        root.profile_id,
        pins,
        tuple(effective),
        tuple(traces),
        tuple(conflicts),
        status,
    )
    digest = resolved_hash(preliminary)
    return replace(preliminary, resolved_profile_hash=digest)
