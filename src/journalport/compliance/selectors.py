"""Deterministic selectors over CanonicalManuscript."""

from __future__ import annotations

from journalport.manuscript.model import CanonicalManuscript, Section
from journalport.profiles.models import ProfileRule

from .counting import word_count
from .models import Selection
from .sections import canonical_section


def _section_text(sections: list[Section]) -> tuple[str, tuple[str, ...]]:
    text: list[str] = []
    ids: list[str] = []

    def visit(section: Section) -> None:
        ids.append(section.object_id)
        text.extend(block.text for block in section.paragraphs)
        for child in section.subsections:
            visit(child)

    for item in sections:
        visit(item)
    return "\n".join(text), tuple(ids)


def _measure(text: str, rule: ProfileRule) -> int | str:
    if rule.unit == "words":
        return word_count(text)
    if rule.unit == "characters":
        return len(text)
    return text


def select_target(manuscript: CanonicalManuscript, rule: ProfileRule) -> Selection:
    target = rule.target
    if target == "title":
        value = manuscript.metadata.get("title")
        if not isinstance(value, str) or not value.strip():
            return Selection(target, (), None, "metadata.title", "missing canonical title")
        return Selection(
            target, (manuscript.manuscript_id,), _measure(value, rule), "metadata.title"
        )
    if target == "article_type":
        return Selection(
            target,
            (manuscript.manuscript_id,),
            manuscript.metadata.get("article_type"),
            "metadata.article_type",
        )
    if target in {"abstract", "main_text"}:
        sections = manuscript.abstract if target == "abstract" else manuscript.main_body
        value, section_ids = _section_text(sections)
        if not sections:
            return Selection(target, (), None, f"canonical.{target}", f"missing {target}")
        return Selection(target, section_ids, _measure(value, rule), f"canonical.{target}")
    if target == "references":
        return Selection(
            target,
            tuple(x.object_id for x in manuscript.references),
            len(manuscript.references),
            "reference_count",
        )
    if target == "figures_and_tables":
        objects = manuscript.figures + manuscript.tables
        return Selection(
            target, tuple(x.object_id for x in objects), len(objects), "figure_plus_table_count"
        )
    if target == "figure_files":
        return Selection(
            target,
            tuple(x.object_id for x in manuscript.figures),
            all(x.file_refs for x in manuscript.figures),
            "figure_file_refs",
        )
    if target == "supplementary_information":
        return Selection(
            target,
            tuple(x.object_id for x in manuscript.supplementary_materials),
            bool(manuscript.supplementary_materials),
            "supplementary_count",
        )
    if target == "section_order":
        names: list[str] = []
        section_ids_list: list[str] = []
        for section in manuscript.main_body + (manuscript.methods or []):
            name = canonical_section(section.title)
            if name is not None:
                names.append(name.replace("_", " ").title())
                section_ids_list.append(section.object_id)
        return Selection(
            target, tuple(section_ids_list), list(names), "section_alias_registry@1.0.0"
        )
    if target in manuscript.statements:
        return Selection(
            target,
            (manuscript.manuscript_id,),
            manuscript.statements[target],
            f"statements.{target}",
        )
    metadata_targets = {"cover_letter", "title_page", "extended_data"}
    if target in metadata_targets:
        if target not in manuscript.metadata:
            return Selection(target, (), None, f"metadata.{target}", "missing canonical field")
        return Selection(
            target, (manuscript.manuscript_id,), manuscript.metadata[target], f"metadata.{target}"
        )
    return Selection(target, (), None, "unsupported-selector", f"unsupported target: {target}")
