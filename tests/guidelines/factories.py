from journalport.guidelines.hashing import digest_text
from journalport.guidelines.models import DiscoveredSource
from journalport.guidelines.retrieval import RetrievalSnapshot


def snapshot(
    text: str,
    *,
    url: str = "https://www.nature.com/test/content",
    authority: int = 1,
    status: str = "RETRIEVED",
) -> RetrievalSnapshot:
    source = DiscoveredSource(
        "1.0.0",
        "source:test",
        url,
        "OFFICIAL_ARTICLE_TYPE_GUIDELINE",
        "test-journal",
        "Nature Portfolio",
        "article",
        "2026-09-29T00:00:00Z",
        status,
        authority,
        "JOURNAL_OWNED",
    )
    return RetrievalSnapshot(
        "1.0.0",
        source,
        "2026-09-29T00:00:00Z",
        200,
        "text/html",
        "Fixture",
        digest_text(text),
        status,
        text,
    )
