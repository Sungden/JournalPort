"""One-command conversion, bounded repair, rewriting, draft layout and rendering."""

from __future__ import annotations

import json
import shutil
import zipfile
from pathlib import Path
from typing import Any

from lxml import etree

from journalport.manuscript.rewrite_input import prepare_rewrite_input
from journalport.transform.full_docx import read_document, serialize
from journalport.transform.hashing import file_hash
from journalport.transform.layout import apply_alignment, apply_columns, apply_line_spacing
from journalport.transform.structure import W, text
from journalport.verify.render import LibreOfficeRenderBackend

from .nature_rewrite import SECTIONS, Model, _plain, run_nature_rewrite


def rewrite_manuscript(
    source: Path,
    output: Path,
    *,
    journal: str,
    writer: Model,
    reviewer: Model,
    privacy_mode: str,
    max_attempts: int = 3,
    render_executable: str | None = None,
) -> dict[str, Any]:
    """Produce a source-bound author-review draft; failed attempts remain inspectable."""
    if not 1 <= max_attempts <= 5:
        raise ValueError("max-attempts must be between 1 and 5")
    source_hash = file_hash(source)
    output.mkdir(parents=True, exist_ok=False)
    output.chmod(0o700)
    normalized, conversion = prepare_rewrite_input(source, output / "input")
    feedback: dict[str, Any] = {}
    result = None
    failures = []
    for attempt in range(1, max_attempts + 1):
        directory = output / f"attempt-{attempt}"

        def repair_writer(
            prompt: dict[str, Any], previous_feedback: dict[str, Any] = feedback
        ) -> dict[str, Any]:
            return writer(
                {
                    **prompt,
                    **(
                        {"previous_attempt_feedback": previous_feedback}
                        if previous_feedback
                        else {}
                    ),
                }
            )

        try:
            result = run_nature_rewrite(
                normalized,
                directory,
                journal=journal,
                writer=repair_writer,
                reviewer=reviewer,
                privacy_mode=privacy_mode,
            )
        except ValueError as exc:
            feedback = {"error": str(exc)}
            for name in ("rewrite_proposal.json", "semantic_review.json"):
                if (directory / name).exists():
                    feedback[name] = json.loads((directory / name).read_text())
            failures.append({"attempt": attempt, "reason": str(exc)})
            continue
        break
    if result is None:
        report = {"state": "BLOCKED", "failures": failures, "submission_ready": False}
    elif result["state"] != "DRAFT_REQUIRES_AUTHOR_REVIEW":
        report = result
    else:
        candidate = Path(result["candidate"])
        # Draft reading layout, not a VERIFIED publisher-profile transformation.
        parts, root, body = read_document(candidate)
        apply_columns(body, 1)
        apply_alignment(body, "LEFT")
        apply_line_spacing(body, 2)
        for run in body.iter(W + "r"):
            parent = run.getparent()
            if parent is None or not _plain(parent):
                continue
            properties = run.find(W + "rPr")
            if properties is None:
                properties = etree.Element(W + "rPr")
                run.insert(0, properties)
            fonts = properties.find(W + "rFonts")
            if fonts is None:
                fonts = etree.SubElement(properties, W + "rFonts")
            for key in ("asciiTheme", "hAnsiTheme", "eastAsiaTheme", "cstheme"):
                fonts.attrib.pop(W + key, None)
            for key in ("ascii", "hAnsi", "cs"):
                fonts.set(W + key, "Arial")
        parts["word/document.xml"] = serialize(root)
        final = output / "nature-draft.docx"
        with zipfile.ZipFile(final, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for name, value in parts.items():
                archive.writestr(name, value)
        final.chmod(0o600)
        original_parts, _, original_body = read_document(candidate)
        written_parts, _, written_body = read_document(final)
        if any(
            written_parts.get(k) != v for k, v in original_parts.items() if k != "word/document.xml"
        ):
            raise ValueError("Draft layout changed a protected package part")
        if [n.text for n in original_body.iter(W + "t")] != [
            n.text for n in written_body.iter(W + "t")
        ]:
            raise ValueError("Draft layout altered document text")
        rendering = LibreOfficeRenderBackend(render_executable).render(
            final, output / "render", SECTIONS, title_override=text(written_body[0])
        )
        (output / "render_report.json").write_text(json.dumps(rendering.to_dict(), indent=2) + "\n")
        markdown_parts = []
        for node in written_body:
            paragraph_text = text(node).strip()
            if not paragraph_text:
                continue
            heading = node.find(W + "pPr/" + W + "outlineLvl")
            style = node.find(W + "pPr/" + W + "pStyle")
            is_heading = heading is not None or (
                style is not None and style.get(W + "val") == "Heading1"
            )
            markdown_parts.append(("## " if is_heading else "") + paragraph_text)
        markdown = "\n\n".join(markdown_parts)
        (output / "nature-draft.md").write_text(markdown + "\n")
        shutil.copyfile(candidate.parent / "semantic_review.json", output / "semantic_review.json")
        report = {
            **result,
            "candidate": str(final),
            "candidate_sha256": file_hash(final),
            "original_source_sha256": source_hash,
            "conversion": conversion,
            "attempts": attempt,
            "render_status": rendering.status,
            "layout": "single_column_double_spaced_left_aligned_review_draft",
            "submission_ready": False,
        }
    if file_hash(source) != source_hash:
        raise ValueError("Original manuscript changed during workflow")
    (output / "rewrite_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    )
    return report
