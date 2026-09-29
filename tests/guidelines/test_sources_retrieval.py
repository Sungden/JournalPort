from pathlib import Path

import pytest

from journalport.guidelines.discovery import discover_sources
from journalport.guidelines.retrieval import retrieve_source
from journalport.guidelines.sources import validate_officiality


def test_three_journal_discovery_returns_only_official_navigation_sources() -> None:
    for slug in (
        "nature-communications",
        "nature-computational-science",
        "nature-machine-intelligence",
    ):
        sources = discover_sources(slug, "article", discovered_at="2026-09-29T00:00:00Z")
        assert len(sources) == 2
        assert all(validate_officiality(item.source_url) for item in sources)
        assert [item.authority_level for item in sources] == [1, 2]


@pytest.mark.parametrize(
    "url",
    (
        "http://www.nature.com/test",
        "https://nature.example/test",
        "https://blog.example.org/nature",
        "https://www.nature.com.evil.example/test",
        "https://user@www.nature.com/test",
    ),
)
def test_third_party_and_ambiguous_domains_are_not_official(url: str) -> None:
    assert not validate_officiality(url)


@pytest.mark.parametrize(
    ("response", "expected"),
    [
        ((404, "text/html", "", "missing"), "NOT_FOUND"),
        ((403, "text/html", "", "blocked"), "BLOCKED"),
        ((200, "application/pdf", "", "pdf"), "BLOCKED"),
        ((200, "text/html", "", ""), "PARTIAL_RETRIEVAL"),
        ((200, "text/html", "Title", "Article limits: abstract 200 words."), "RETRIEVED"),
    ],
)
def test_retrieval_statuses_and_immutable_cache(tmp_path: Path, response, expected: str) -> None:
    source = discover_sources("nature-communications", "article")[0]
    result = retrieve_source(source, tmp_path, fetcher=lambda _url: response)
    assert result.retrieval_status == expected
    assert len(list(tmp_path.glob("*.json"))) == 1


def test_timeout_is_explicitly_blocked(tmp_path: Path) -> None:
    source = discover_sources("nature-communications", "article")[0]

    def timeout(_url: str):
        raise TimeoutError

    assert retrieve_source(source, tmp_path, fetcher=timeout).retrieval_status == "BLOCKED"


def test_redirect_to_unrelated_domain_is_blocked(tmp_path: Path) -> None:
    source = discover_sources("nature-communications", "article")[0]
    response = (
        200,
        "text/html",
        "Fake",
        "Article limits: abstract 1 word.",
        "https://evil.example/rules",
    )
    assert (
        retrieve_source(source, tmp_path, fetcher=lambda _url: response).retrieval_status
        == "BLOCKED"
    )
