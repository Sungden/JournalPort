"""Reviewed, lossless IEEE-to-NC scientific section migration for DOCX.

This is an author-selected editorial recipe, not a verified journal obligation.
"""

from __future__ import annotations

import copy
import json
import re
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any

from lxml import etree

from .full_docx import read_document, serialize
from .hashing import file_hash
from .structure import StructureBlocked, W, digest, text

RECIPE = "ieee-to-nature-communications-v1"
ORDER = ["Introduction", "Results", "Discussion", "Methods"]
ALIASES = {
    "introduction": "Introduction",
    "related work": "Related work",
    "related works": "Related work",
    "background and related work": "Related work",
    "methods": "Methods",
    "methodology": "Methods",
    "materials and methods": "Methods",
    "results": "Results",
    "discussion": "Discussion",
    "conclusion": "Conclusion",
    "conclusions": "Conclusion",
}
PREFIX = re.compile(r"^(?:(?:[IVXLCDM]+|\d+)[.)]?\s+)", re.IGNORECASE)


def level(node: etree._Element) -> int | None:
    if node.tag != W + "p":
        return None
    outline = node.find(W + "pPr/" + W + "outlineLvl")
    if outline is not None:
        return int(str(outline.get(W + "val")))
    style = node.find(W + "pPr/" + W + "pStyle")
    match = re.fullmatch(
        r"(?:Heading|JP_HEADING_)[ _]?(\d+)",
        str(style.get(W + "val", "")) if style is not None else "",
        re.IGNORECASE,
    )
    return int(match[1]) - 1 if match else None


def sections(
    body: etree._Element,
) -> tuple[list[etree._Element], dict[str, list[etree._Element]], list[etree._Element]]:
    nodes = list(body)
    if any(list(body.iter(W + tag)) for tag in ("ins", "del", "altChunk", "sdt")):
        raise StructureBlocked("Tracked changes and content controls require manual resolution")
    if any(list(n.iter(W + "sectPr")) for n in nodes if n.tag != W + "sectPr"):
        raise StructureBlocked("Embedded section breaks require manual layout review")
    markers = [
        (i, PREFIX.sub("", text(n).strip().rstrip(":")).casefold())
        for i, n in enumerate(nodes)
        if level(n) == 0
    ]
    selected = [(i, ALIASES[label]) for i, label in markers if label in ALIASES]
    if not selected:
        raise StructureBlocked("No explicit level-1 scientific headings found")
    labels = [label for _, label in selected]
    if len(labels) != len(set(labels)):
        raise StructureBlocked("Duplicate scientific sections")
    if set(labels) != set(ALIASES.values()):
        raise StructureBlocked(
            "Require Introduction, Related work, Methods, Results, Discussion, Conclusion"
        )
    start = selected[0][0]
    last = selected[-1][0]
    if any(start < i < last and label not in ALIASES for i, label in markers):
        raise StructureBlocked("Unknown top-level section interrupts scientific sections")
    tail_start = next(
        (i for i, label in markers if i > last and label not in ALIASES),
        len(nodes) - (1 if nodes and nodes[-1].tag == W + "sectPr" else 0),
    )
    chunks = {}
    for j, (i, label) in enumerate(selected):
        end = selected[j + 1][0] if j + 1 < len(selected) else tail_start
        chunk = nodes[i:end]
        if len(chunk) < 2 or not any(
            text(n).strip() or n.tag == W + "tbl" or list(n.iter(W + "drawing")) for n in chunk[1:]
        ):
            raise StructureBlocked("Empty scientific section: " + label)
        chunks[label] = chunk
    return nodes[:start], chunks, nodes[tail_start:]


def plan_scientific_structure(source: Path) -> dict[str, Any]:
    _, _, body = read_document(source)
    _, chunks, _ = sections(body)
    return {
        "recipe": RECIPE,
        "source_sha256": file_hash(source),
        "recipe_kind": "author_selected_editorial_structure_not_journal_requirement",
        "target_top_level_order": ORDER,
        "sections": {label: [digest(n) for n in nodes] for label, nodes in chunks.items()},
        "moves": [
            {
                "section": "Related work",
                "into": "Introduction",
                "position": "end",
                "heading_level": 2,
            },
            {"section": "Conclusion", "into": "Discussion", "position": "end", "heading_level": 2},
            {"section": "Methods", "after": "Discussion"},
        ],
        "manual_editorial_review": [
            "Integrate related-work context into the introduction and relocate interpretive comparisons to discussion.",
            "Review conclusion transitions and overlap without inventing or deleting findings.",
            "Organize results around scientific findings; add brief method context only after author review.",
            "Check numbered section cross-references, citation/figure first-mention order, navigation and every rendered page.",
            "Complete factual declarations and run stage-specific full-format separately.",
        ],
        "submission_ready": False,
    }


def _heading(node: etree._Element, label: str, depth: int) -> None:
    props = node.find(W + "pPr")
    if props is None:
        props = etree.Element(W + "pPr")
        node.insert(0, props)
    for tag, value in (("pStyle", f"Heading{depth}"), ("outlineLvl", str(depth - 1))):
        item = props.find(W + tag)
        if item is None:
            item = etree.SubElement(props, W + tag)
        item.set(W + "val", value)
    # Remove automatic heading numbering only; retain all run content and manual prefixes.
    for item in list(props.findall(W + "numPr")):
        props.remove(item)


def _expected_body(body: etree._Element) -> etree._Element:
    result = copy.deepcopy(body)
    front, chunks, tail = sections(result)
    for label in ("Related work", "Conclusion"):
        for node in chunks[label]:
            old = level(node)
            if old is not None:
                if old >= 8:
                    raise StructureBlocked("Cannot demote heading below supported level 9")
                _heading(node, label, old + 2)
    result[:] = (
        front
        + chunks["Introduction"]
        + chunks["Related work"]
        + chunks["Results"]
        + chunks["Discussion"]
        + chunks["Conclusion"]
        + chunks["Methods"]
        + tail
    )
    return result


def verify_scientific_structure(
    source: Path, candidate: Path, plan: dict[str, Any]
) -> dict[str, Any]:
    if plan != plan_scientific_structure(source):
        raise StructureBlocked("Reviewed plan does not match current source and recipe")
    before_parts, before_root, before = read_document(source)
    after_parts, after_root, after = read_document(candidate)
    checks = {
        "package_members_preserved": set(before_parts) == set(after_parts),
        "other_parts_byte_identical": all(
            after_parts.get(k) == v for k, v in before_parts.items() if k != "word/document.xml"
        ),
        "all_text_preserved": Counter(text(n) for n in before) == Counter(text(n) for n in after),
        "exact_reviewed_structure": etree.tostring(
            _expected_body(before), method="c14n", exclusive=True
        )
        == etree.tostring(after, method="c14n", exclusive=True),
    }
    # Protect document-level namespaces/properties outside body as well.
    expected_root = copy.deepcopy(before_root)
    expected_body = expected_root.find(W + "body")
    assert expected_body is not None
    expected_root.replace(expected_body, _expected_body(before))
    checks["document_envelope_preserved"] = etree.tostring(
        expected_root, method="c14n"
    ) == etree.tostring(after_root, method="c14n")
    if not all(checks.values()):
        raise StructureBlocked("Scientific structure verification failed: " + str(checks))
    return {
        "status": "VERIFIED_STRUCTURE_CANDIDATE",
        "preservation_checks": checks,
        "source_sha256": file_hash(source),
        "candidate_sha256": file_hash(candidate),
        "submission_ready": False,
        "editorial_rewrite_completed": False,
        "manual_editorial_review": plan["manual_editorial_review"],
    }


def run_scientific_structure(
    source: Path, output: Path, *, plan_only: bool = False, reviewed_plan: Path | None = None
) -> dict[str, Any]:
    plan = plan_scientific_structure(source)
    if not plan_only and (reviewed_plan is None or json.loads(reviewed_plan.read_text()) != plan):
        raise StructureBlocked("Execution requires the unchanged reviewed plan for this manuscript")
    output.mkdir(parents=True, exist_ok=False)
    (output / "structure_plan.json").write_text(json.dumps(plan, indent=2) + "\n")
    if plan_only:
        return {"status": "PLAN_ONLY", "plan": str(output / "structure_plan.json")}
    parts, root, body = read_document(source)
    root.replace(body, _expected_body(body))
    parts["word/document.xml"] = serialize(root)
    candidate = output / "manuscript.docx"
    with zipfile.ZipFile(candidate, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, payload in parts.items():
            archive.writestr(name, payload)
    report = verify_scientific_structure(source, candidate, plan)
    (output / "structure_verification.json").write_text(json.dumps(report, indent=2) + "\n")
    (output / "EDITORIAL_REVIEW.md").write_text(
        "# Editorial review still required\n\n"
        + "\n".join("- " + s for s in plan["manual_editorial_review"])
        + "\n"
    )
    return {**report, "candidate": str(candidate)}
