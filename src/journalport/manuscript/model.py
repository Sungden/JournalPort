"""Typed, format-neutral manuscript records for the M1 parsing boundary."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

SCHEMA_VERSION = "1.1.0"


@dataclass(slots=True)
class SourceLocator:
    format: str
    status: str
    source_file: str
    part: str | None = None
    index: int | None = None
    line_start: int | None = None
    line_end: int | None = None
    relationship_id: str | None = None
    environment: str | None = None
    command: str | None = None


@dataclass(slots=True)
class TextBlock:
    object_id: str
    text: str
    source_locator: SourceLocator


@dataclass(slots=True)
class Section:
    object_id: str
    title: str
    level: int
    source_locator: SourceLocator
    paragraphs: list[TextBlock] = field(default_factory=list)
    subsections: list[Section] = field(default_factory=list)


@dataclass(slots=True)
class Asset:
    object_id: str
    label: str
    legend: str
    file_refs: list[str]
    source_locator: SourceLocator
    content_hash: str | None = None
    content_text: str | None = None


@dataclass(slots=True)
class Equation:
    object_id: str
    representation: str
    value: str
    source_locator: SourceLocator
    label: str | None = None


@dataclass(slots=True)
class Citation:
    object_id: str
    reference_ids: list[str]
    raw_text: str
    source_locator: SourceLocator
    citation_keys: list[str] = field(default_factory=list)


@dataclass(slots=True)
class Reference:
    object_id: str
    raw_text: str
    source_locator: SourceLocator
    structured: dict[str, Any] | None = None
    doi: str | None = None


@dataclass(slots=True)
class Note:
    object_id: str
    text: str
    source_locator: SourceLocator


@dataclass(slots=True)
class UnsupportedContent:
    object_id: str
    object_type: str
    source_locator: SourceLocator
    reason: str
    severity: str
    preservation_possible: bool
    raw_fragment_preserved: bool
    source_fragment_hash: str
    raw_fragment: str | None = None


def empty_statements() -> dict[str, str | None]:
    return {
        "acknowledgements": None,
        "funding": None,
        "author_contributions": None,
        "competing_interests": None,
        "ethics": None,
        "consent": None,
        "data_availability": None,
        "code_availability": None,
    }


@dataclass(slots=True)
class CanonicalManuscript:
    manuscript_id: str
    source: dict[str, str]
    metadata: dict[str, Any]
    abstract: list[Section] = field(default_factory=list)
    main_body: list[Section] = field(default_factory=list)
    methods: list[Section] | None = None
    statements: dict[str, str | None] = field(default_factory=empty_statements)
    figures: list[Asset] = field(default_factory=list)
    tables: list[Asset] = field(default_factory=list)
    equations: list[Equation] = field(default_factory=list)
    citations: list[Citation] = field(default_factory=list)
    references: list[Reference] = field(default_factory=list)
    supplementary_materials: list[Asset] = field(default_factory=list)
    footnotes: list[Note] = field(default_factory=list)
    endnotes: list[Note] = field(default_factory=list)
    unsupported_content: list[UnsupportedContent] = field(default_factory=list)
    schema_version: str = SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> CanonicalManuscript:
        def locator(item: dict[str, Any]) -> SourceLocator:
            return SourceLocator(**item)

        def text(item: dict[str, Any]) -> TextBlock:
            return TextBlock(item["object_id"], item["text"], locator(item["source_locator"]))

        def section(item: dict[str, Any]) -> Section:
            return Section(
                item["object_id"],
                item["title"],
                item["level"],
                locator(item["source_locator"]),
                [text(x) for x in item.get("paragraphs", [])],
                [section(x) for x in item.get("subsections", [])],
            )

        return cls(
            manuscript_id=value["manuscript_id"],
            source=value["source"],
            metadata=value["metadata"],
            abstract=[section(x) for x in value.get("abstract", [])],
            main_body=[section(x) for x in value.get("main_body", [])],
            methods=None
            if value.get("methods") is None
            else [section(x) for x in value["methods"]],
            statements=value.get("statements", empty_statements()),
            figures=[
                Asset(**(x | {"source_locator": locator(x["source_locator"])}))
                for x in value.get("figures", [])
            ],
            tables=[
                Asset(**(x | {"source_locator": locator(x["source_locator"])}))
                for x in value.get("tables", [])
            ],
            equations=[
                Equation(**(x | {"source_locator": locator(x["source_locator"])}))
                for x in value.get("equations", [])
            ],
            citations=[
                Citation(**(x | {"source_locator": locator(x["source_locator"])}))
                for x in value.get("citations", [])
            ],
            references=[
                Reference(**(x | {"source_locator": locator(x["source_locator"])}))
                for x in value.get("references", [])
            ],
            supplementary_materials=[
                Asset(**(x | {"source_locator": locator(x["source_locator"])}))
                for x in value.get("supplementary_materials", [])
            ],
            footnotes=[
                Note(**(x | {"source_locator": locator(x["source_locator"])}))
                for x in value.get("footnotes", [])
            ],
            endnotes=[
                Note(**(x | {"source_locator": locator(x["source_locator"])}))
                for x in value.get("endnotes", [])
            ],
            unsupported_content=[
                UnsupportedContent(**(x | {"source_locator": locator(x["source_locator"])}))
                for x in value.get("unsupported_content", [])
            ],
            schema_version=value.get("schema_version", SCHEMA_VERSION),
        )
