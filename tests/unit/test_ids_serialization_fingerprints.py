from __future__ import annotations

from copy import deepcopy

import pytest

from journalport.manuscript.fingerprints import fingerprint
from journalport.manuscript.ids import StableIdFactory
from journalport.manuscript.model import CanonicalManuscript, Section, SourceLocator, TextBlock
from journalport.manuscript.serialization import (
    deserialize_canonical,
    logical_hash,
    serialize_canonical,
)


def manuscript() -> CanonicalManuscript:
    loc = SourceLocator("LATEX", "EXACT", "main.tex", line_start=1, line_end=1)
    section = Section("sec_1234567890abcdef", "Results", 1, loc)
    section.paragraphs.append(TextBlock("para_1234567890abcdef", "Value 12.5% (p < 0.01).", loc))
    return CanonicalManuscript(
        manuscript_id="doc_1234567890abcdef",
        source={"format": "LATEX", "filename": "main.tex", "sha256": "sha256:" + "0" * 64},
        metadata={
            "title": "Study",
            "short_title": None,
            "article_type": "UNKNOWN",
            "authors": [],
            "author_order": [],
            "affiliations": [],
            "keywords": [],
        },
        main_body=[section],
    )


def test_stable_ids_are_deterministic_unique_and_content_sensitive() -> None:
    first = StableIdFactory()
    second = StableIdFactory()
    assert first.make("paragraph", "main.tex:1", "same") == second.make(
        "paragraph", "main.tex:1", "same"
    )
    duplicate = first.make("paragraph", "main.tex:1", "same")
    assert duplicate.endswith(".2")
    assert StableIdFactory().make("paragraph", "main.tex:1", "changed") != duplicate.removesuffix(
        ".2"
    )


def test_canonical_round_trip_and_hash_ignore_dict_order_and_newlines() -> None:
    original = manuscript()
    payload = serialize_canonical(original)
    reloaded = deserialize_canonical(payload)
    assert reloaded == original
    reordered = deepcopy(original.to_dict())
    reordered["metadata"] = dict(reversed(list(reordered["metadata"].items())))
    reordered["metadata"]["title"] = "Study\r\n"
    baseline = original.to_dict()
    baseline["metadata"]["title"] = "Study\n"
    assert logical_hash(reordered) == logical_hash(baseline)


def test_nonfinite_float_is_rejected() -> None:
    value = manuscript().to_dict()
    value["metadata"]["score"] = float("nan")
    with pytest.raises(ValueError):
        serialize_canonical(value)


def test_numeric_fingerprint_changes_independently() -> None:
    original = manuscript()
    changed = manuscript()
    changed.main_body[0].paragraphs[0].text = "Value 12.6% (p < 0.01)."
    assert fingerprint(original).numeric != fingerprint(changed).numeric
