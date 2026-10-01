"""Explicit front-matter identities; never inferred from author sequence or scientific prose."""

from __future__ import annotations

from dataclasses import dataclass

from lxml import etree

from .structure import StructureBlocked, W, detect_blocks, text


@dataclass(frozen=True)
class FrontMatterIdentity:
    title: str
    authors: tuple[str, ...]
    affiliations: tuple[str, ...]
    correspondence: tuple[str, ...]
    paragraph_roles: tuple[tuple[int, str], ...]
    confidence: str


def identify_front_matter(body: etree._Element) -> FrontMatterIdentity:
    front = next((block for block in detect_blocks(body) if block.role == "FrontMatterBlock"), None)
    if front is None or front.confidence != "HIGH":
        raise StructureBlocked("author_input_required_front_matter_boundary")
    values: dict[str, list[str]] = {
        "title": [],
        "authors": [],
        "affiliations": [],
        "correspondence": [],
    }
    roles: list[tuple[int, str]] = []
    labels = {
        "Title": "title",
        "Authors": "authors",
        "Affiliations": "affiliations",
        "Correspondence": "correspondence",
    }
    styles = {
        "title": "title",
        "jp_title": "title",
        "author": "authors",
        "jp_author": "authors",
        "affiliation": "affiliations",
        "jp_affiliation": "affiliations",
        "correspondence": "correspondence",
    }
    for index, paragraph in enumerate(list(body)[: front.end]):
        value = text(paragraph).strip()
        if not value:
            continue
        role = None
        payload = value
        for label, candidate in labels.items():
            if value.startswith(label + ":"):
                role, payload = candidate, value[len(label) + 1 :].strip()
                break
        style = paragraph.find(W + "pPr/" + W + "pStyle")
        if role is None and style is not None:
            role = styles.get(str(style.get(W + "val", "")).casefold())
        if role is not None and payload:
            values[role].append(payload)
            roles.append((index, role))
        else:
            raise StructureBlocked("author_input_required_unclassified_front_matter")
    if len(values["title"]) != 1 or not all(
        values[key] for key in ("authors", "affiliations", "correspondence")
    ):
        raise StructureBlocked("author_input_required_front_matter_identity")
    if not any("@" in value for value in values["correspondence"]) or not any(
        "*" in value for value in values["authors"]
    ):
        raise StructureBlocked("author_input_required_corresponding_author_marker_or_contact")
    return FrontMatterIdentity(
        values["title"][0],
        tuple(values["authors"]),
        tuple(values["affiliations"]),
        tuple(values["correspondence"]),
        tuple(roles),
        "HIGH",
    )


def restructure_inline(body: etree._Element) -> None:
    identity = identify_front_matter(body)
    order = {"title": 0, "authors": 1, "affiliations": 2, "correspondence": 3}
    nodes = list(body)
    selected = [
        nodes[index]
        for index, _ in sorted(identity.paragraph_roles, key=lambda item: order[item[1]])
    ]
    for index, _ in identity.paragraph_roles:
        body.remove(nodes[index])
    for index, paragraph in enumerate(selected):
        body.insert(index, paragraph)
