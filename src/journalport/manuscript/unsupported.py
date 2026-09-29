"""Fail-closed unsupported-content registry helpers."""

from __future__ import annotations

import hashlib

from .ids import StableIdFactory
from .model import SourceLocator, UnsupportedContent


def register_unsupported(
    ids: StableIdFactory,
    *,
    object_type: str,
    locator: SourceLocator,
    reason: str,
    severity: str,
    raw_fragment: str | bytes | None,
    preservation_possible: bool = True,
) -> UnsupportedContent:
    if severity not in {"WARNING", "BLOCKING"}:
        raise ValueError("unsupported severity must be WARNING or BLOCKING")
    raw = raw_fragment.encode("utf-8") if isinstance(raw_fragment, str) else raw_fragment
    digest = hashlib.sha256(raw or b"").hexdigest()
    anchor = f"{locator.source_file}:{locator.part}:{locator.index}:{locator.line_start}"
    return UnsupportedContent(
        object_id=ids.make("unsupported", anchor, object_type + reason),
        object_type=object_type,
        source_locator=locator,
        reason=reason,
        severity=severity,
        preservation_possible=preservation_possible,
        raw_fragment_preserved=raw_fragment is not None,
        source_fragment_hash=f"sha256:{digest}",
        raw_fragment=(raw.decode("utf-8", errors="replace") if raw is not None else None),
    )
