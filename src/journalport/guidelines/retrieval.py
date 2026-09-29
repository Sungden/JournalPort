"""Network-isolated retrieval with immutable cache records."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime
from pathlib import Path

from .hashing import digest_text
from .models import DiscoveredSource
from .sources import validate_officiality


@dataclass(frozen=True, slots=True)
class RetrievalSnapshot:
    schema_version: str
    source: DiscoveredSource
    retrieved_at: str
    http_status: int | None
    content_type: str
    page_title: str
    content_hash: str
    retrieval_status: str
    content: str


FetchResponse = tuple[int, str, str, str] | tuple[int, str, str, str, str]
Fetcher = Callable[[str], FetchResponse]


def _stdlib_fetch(url: str) -> FetchResponse:
    request = urllib.request.Request(
        url, headers={"User-Agent": "JournalPort/0.0 guideline-research"}
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        content_type = response.headers.get_content_type()
        body = response.read(2_000_000).decode(
            response.headers.get_content_charset() or "utf-8", "replace"
        )
        return response.status, content_type, "", body, response.geturl()


def retrieve_source(
    source: DiscoveredSource,
    cache_root: Path,
    *,
    fetcher: Fetcher = _stdlib_fetch,
    retrieved_at: str | None = None,
) -> RetrievalSnapshot:
    now = retrieved_at or datetime.now(UTC).isoformat()
    if not validate_officiality(source.source_url, relationship=source.official_relationship):
        return RetrievalSnapshot("1.0.0", source, now, None, "", "", digest_text(""), "BLOCKED", "")
    try:
        response = fetcher(source.source_url)
        status, content_type, title, content = response[:4]
        final_url = response[4] if len(response) == 5 else source.source_url
        if status == 404:
            state = "NOT_FOUND"
        elif (
            status != 200
            or not validate_officiality(final_url, relationship=source.official_relationship)
            or content_type not in {"text/html", "text/plain", "application/xhtml+xml"}
        ):
            state = "BLOCKED"
        elif not content.strip():
            state = "PARTIAL_RETRIEVAL"
        else:
            state = "RETRIEVED"
    except (TimeoutError, urllib.error.URLError, OSError):
        status, content_type, title, content, state = None, "", "", "", "BLOCKED"
    digest = digest_text(content)
    snapshot = RetrievalSnapshot(
        "1.0.0",
        replace(source, retrieval_status=state),
        now,
        status,
        content_type,
        title,
        digest,
        state,
        content,
    )
    cache_root.mkdir(parents=True, exist_ok=True)
    target = cache_root / f"{digest.split(':', 1)[1]}.json"
    if not target.exists():
        target.write_text(
            json.dumps(asdict(snapshot), ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
    return snapshot
