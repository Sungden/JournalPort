"""Safe, non-executing LaTeX subset parser with provenance-preserving fallbacks."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

from .ids import StableIdFactory
from .model import (
    Asset,
    CanonicalManuscript,
    Citation,
    Equation,
    Reference,
    Section,
    SourceLocator,
    TextBlock,
)
from .unsupported import register_unsupported


class LatexParseError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class _Source:
    path: Path
    text: str


INCLUDE_RE = re.compile(r"\\(?:input|include)\s*\{([^}]+)\}")
SECTION_RE = re.compile(r"^\s*\\(section|subsection)\*?\s*\{([^}]*)\}", re.MULTILINE)
ENV_RE = re.compile(r"\\begin\{([^}]+)\}(.*?)\\end\{\1\}", re.DOTALL)
CITE_RE = re.compile(r"\\(cite|citep|citet)\s*(?:\[[^]]*\]\s*)*\{([^}]+)\}")
REF_RE = re.compile(r"\\(?:eqref|ref)\s*\{([^}]+)\}")
LABEL_RE = re.compile(r"\\label\s*\{([^}]+)\}")
CAPTION_RE = re.compile(r"\\caption\s*\{([^}]*)\}", re.DOTALL)
BIBITEM_RE = re.compile(
    r"\\bibitem(?:\[[^]]*\])?\{([^}]+)\}\s*(.*?)(?=\\bibitem|\\end\{thebibliography\})", re.DOTALL
)
COMMAND_RE = re.compile(r"\\([A-Za-z@]+)")
UNSAFE_RE = re.compile(
    r"\\(?:write18|immediate\s*\\write18|openout|write|read|input\s*\|)", re.IGNORECASE
)

KNOWN_COMMANDS = {
    "documentclass",
    "usepackage",
    "title",
    "author",
    "date",
    "maketitle",
    "begin",
    "end",
    "section",
    "subsection",
    "label",
    "ref",
    "eqref",
    "cite",
    "citep",
    "citet",
    "caption",
    "includegraphics",
    "bibliography",
    "bibliographystyle",
    "input",
    "include",
    "item",
    "bibitem",
    "textbf",
    "textit",
    "emph",
    "url",
    "href",
    "footnote",
    "thanks",
    "newcommand",
    "renewcommand",
    "frac",
    "sqrt",
    "sum",
    "prod",
    "int",
    "mathrm",
    "mathbf",
    "mathit",
    "left",
    "right",
    "alpha",
    "beta",
    "gamma",
    "delta",
    "theta",
    "lambda",
    "mu",
    "sigma",
    "pm",
    "times",
    "and",
}
KNOWN_ENVIRONMENTS = {
    "document",
    "abstract",
    "figure",
    "figure*",
    "table",
    "table*",
    "tabular",
    "thebibliography",
    "equation",
    "equation*",
    "align",
    "align*",
    "displaymath",
    "itemize",
    "enumerate",
}
EQUATION_ENVIRONMENTS = {"equation", "equation*", "align", "align*", "displaymath"}


def _sha256(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _line(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _locator(
    source: _Source,
    start: int,
    end: int,
    *,
    environment: str | None = None,
    command: str | None = None,
    status: str = "EXACT",
) -> SourceLocator:
    return SourceLocator(
        format="LATEX",
        status=status,
        source_file=str(source.path),
        line_start=_line(source.text, start),
        line_end=_line(source.text, end),
        environment=environment,
        command=command,
    )


def _strip_comments(text: str) -> str:
    return re.sub(r"(?<!\\)%.*", "", text)


def _collect_sources(
    main: Path, root: Path, ids: StableIdFactory, manuscript: CanonicalManuscript
) -> list[_Source]:
    sources: list[_Source] = []
    active: list[Path] = []
    seen: set[Path] = set()

    def visit(path: Path, origin: SourceLocator | None = None) -> None:
        resolved = path.resolve()
        if not resolved.is_relative_to(root):
            loc = origin or SourceLocator("LATEX", "UNKNOWN", str(path))
            manuscript.unsupported_content.append(
                register_unsupported(
                    ids,
                    object_type="LATEX_PATH_TRAVERSAL",
                    locator=loc,
                    reason="include escapes the permitted project root",
                    severity="BLOCKING",
                    raw_fragment=str(path),
                    preservation_possible=False,
                )
            )
            return
        if resolved in active:
            loc = origin or SourceLocator("LATEX", "PARTIAL", str(path))
            manuscript.unsupported_content.append(
                register_unsupported(
                    ids,
                    object_type="LATEX_INCLUDE_CYCLE",
                    locator=loc,
                    reason="include cycle detected",
                    severity="BLOCKING",
                    raw_fragment=" -> ".join(map(str, active + [resolved])),
                )
            )
            return
        if resolved in seen:
            return
        if not resolved.is_file():
            loc = origin or SourceLocator("LATEX", "UNKNOWN", str(path))
            manuscript.unsupported_content.append(
                register_unsupported(
                    ids,
                    object_type="LATEX_MISSING_INCLUDE",
                    locator=loc,
                    reason="included source file does not exist",
                    severity="BLOCKING",
                    raw_fragment=str(path),
                    preservation_possible=False,
                )
            )
            return
        text = resolved.read_text(encoding="utf-8")
        source = _Source(resolved, text)
        sources.append(source)
        seen.add(resolved)
        active.append(resolved)
        for match in INCLUDE_RE.finditer(_strip_comments(text)):
            relative = Path(match.group(1))
            if not relative.suffix:
                relative = relative.with_suffix(".tex")
            visit(
                resolved.parent / relative,
                _locator(source, match.start(), match.end(), command=match.group(0)),
            )
        active.pop()

    visit(main)
    return sources


def parse_latex(
    path: str | Path, *, root_directory: str | Path | None = None
) -> CanonicalManuscript:
    source_path = Path(path).resolve()
    root = Path(root_directory).resolve() if root_directory else source_path.parent.resolve()
    if not source_path.is_relative_to(root):
        raise LatexParseError("main file must be within root_directory")
    payload = source_path.read_bytes()
    ids = StableIdFactory()
    manuscript = CanonicalManuscript(
        manuscript_id=ids.make("document", _sha256(payload), source_path.name),
        source={"format": "LATEX", "filename": source_path.name, "sha256": _sha256(payload)},
        metadata={
            "title": "",
            "short_title": None,
            "article_type": "UNKNOWN",
            "authors": [],
            "author_order": [],
            "affiliations": [],
            "keywords": [],
        },
    )
    sources = _collect_sources(source_path, root, ids, manuscript)
    current_section: Section | None = None

    for source in sources:
        clean = _strip_comments(source.text)
        if UNSAFE_RE.search(clean):
            match = UNSAFE_RE.search(clean)
            assert match is not None
            manuscript.unsupported_content.append(
                register_unsupported(
                    ids,
                    object_type="UNSAFE_LATEX_COMMAND",
                    locator=_locator(source, match.start(), match.end(), command=match.group(0)),
                    reason="command can read, write, or execute external content; parsing never executes it",
                    severity="BLOCKING",
                    raw_fragment=match.group(0),
                    preservation_possible=False,
                )
            )

        title = re.search(r"\\title\s*\{([^}]*)\}", clean, re.DOTALL)
        if title and not manuscript.metadata["title"]:
            manuscript.metadata["title"] = title.group(1).strip()
        author = re.search(r"\\author\s*\{([^}]*)\}", clean, re.DOTALL)
        if author:
            for name in re.split(r"\\and|,", author.group(1)):
                name = name.strip()
                if name:
                    author_id = ids.make("author", f"{source.path}:{author.start()}:{name}", name)
                    manuscript.metadata["authors"].append(
                        {
                            "object_id": author_id,
                            "name": name,
                            "orcid": None,
                            "affiliation_ids": [],
                            "corresponding": False,
                            "email": None,
                        }
                    )
                    manuscript.metadata["author_order"].append(author_id)

        positions: list[tuple[int, int, str, str]] = []
        for match in SECTION_RE.finditer(clean):
            positions.append((match.start(), match.end(), match.group(1), match.group(2).strip()))
        for position_index, (start, end, kind, title_text) in enumerate(positions):
            level = 1 if kind == "section" else 2
            section = Section(
                ids.make(
                    "section" if level == 1 else "subsection", f"{source.path}:{start}", title_text
                ),
                title_text,
                level,
                _locator(source, start, end, command=kind),
            )
            if level == 2 and current_section is not None:
                current_section.subsections.append(section)
            else:
                manuscript.main_body.append(section)
            current_section = section
            content_start = end
            content_end = (
                positions[position_index + 1][0]
                if position_index + 1 < len(positions)
                else len(clean)
            )
            body = clean[content_start:content_end]
            for paragraph_match in re.finditer(
                r"(?:^|\n\s*\n)(.*?)(?=\n\s*\n|\Z)", body, re.DOTALL
            ):
                paragraph = paragraph_match.group(1).strip()
                if paragraph and not paragraph.startswith("\\begin{"):
                    absolute_start = content_start + paragraph_match.start(1)
                    current_section.paragraphs.append(
                        TextBlock(
                            ids.make("paragraph", f"{source.path}:{absolute_start}", paragraph),
                            paragraph,
                            _locator(source, absolute_start, absolute_start + len(paragraph)),
                        )
                    )

        environment_matches: list[tuple[str, re.Match[str]]] = []
        environment_names = set(re.findall(r"\\begin\{([^}]+)\}", clean))
        for environment in environment_names:
            pattern = re.compile(
                rf"\\begin\{{{re.escape(environment)}\}}(.*?)\\end\{{{re.escape(environment)}\}}",
                re.DOTALL,
            )
            environment_matches.extend((environment, match) for match in pattern.finditer(clean))
        environment_matches.sort(key=lambda item: item[1].start())
        for environment, match in environment_matches:
            body = match.group(1)
            loc = _locator(source, match.start(), match.end(), environment=environment)
            caption_match = CAPTION_RE.search(body)
            label_match = LABEL_RE.search(body)
            caption = caption_match.group(1).strip() if caption_match else ""
            label = label_match.group(1).strip() if label_match else ""
            if environment == "abstract":
                text_value = re.sub(r"\\[A-Za-z@]+(?:\[[^]]*\])?\{([^}]*)\}", r"\1", body).strip()
                section = Section(
                    ids.make("section", f"{source.path}:abstract:{match.start()}", "Abstract"),
                    "Abstract",
                    1,
                    loc,
                )
                if text_value:
                    section.paragraphs.append(
                        TextBlock(
                            ids.make(
                                "paragraph", f"{source.path}:abstract:{match.start()}", text_value
                            ),
                            text_value,
                            loc,
                        )
                    )
                manuscript.abstract.append(section)
            elif environment in {"figure", "figure*"}:
                files = re.findall(r"\\includegraphics(?:\[[^]]*\])?\{([^}]+)\}", body)
                manuscript.figures.append(
                    Asset(
                        ids.make("figure", f"{source.path}:figure:{match.start()}", body),
                        label or f"Figure {len(manuscript.figures) + 1}",
                        caption,
                        files,
                        loc,
                        None,
                        None,
                    )
                )
            elif environment in {"table", "table*"}:
                manuscript.tables.append(
                    Asset(
                        ids.make("table", f"{source.path}:table:{match.start()}", body),
                        label or f"Table {len(manuscript.tables) + 1}",
                        caption,
                        [],
                        loc,
                        _sha256(body.encode()),
                        body.strip(),
                    )
                )
            elif environment in EQUATION_ENVIRONMENTS:
                manuscript.equations.append(
                    Equation(
                        ids.make("equation", f"{source.path}:{environment}:{match.start()}", body),
                        "LATEX",
                        body.strip(),
                        loc,
                        label or None,
                    )
                )
            elif environment not in KNOWN_ENVIRONMENTS:
                manuscript.unsupported_content.append(
                    register_unsupported(
                        ids,
                        object_type="UNKNOWN_LATEX_ENVIRONMENT",
                        locator=loc,
                        reason=f"environment {environment!r} is not interpreted",
                        severity="BLOCKING",
                        raw_fragment=match.group(0),
                    )
                )

        covered_equations = [
            (match.start(), match.end())
            for environment, match in environment_matches
            if environment in EQUATION_ENVIRONMENTS
        ]
        inline_patterns = [
            re.compile(r"(?<!\$)\$(?!\$)(.+?)(?<!\$)\$(?!\$)", re.DOTALL),
            re.compile(r"\\\((.+?)\\\)", re.DOTALL),
            re.compile(r"\$\$(.+?)\$\$", re.DOTALL),
            re.compile(r"\\\[(.+?)\\\]", re.DOTALL),
        ]
        for pattern in inline_patterns:
            for math_index, match in enumerate(pattern.finditer(clean)):
                if any(start <= match.start() < end for start, end in covered_equations):
                    continue
                value = match.group(1).strip()
                if value:
                    manuscript.equations.append(
                        Equation(
                            ids.make(
                                "equation",
                                f"{source.path}:math:{match.start()}:{math_index}",
                                value,
                            ),
                            "LATEX",
                            value,
                            _locator(
                                source,
                                match.start(),
                                match.end(),
                                environment="inline-math"
                                if not match.group(0).startswith(("$$", "\\["))
                                else "display-math",
                            ),
                        )
                    )

        for cite_index, match in enumerate(CITE_RE.finditer(clean)):
            keys = [key.strip() for key in match.group(2).split(",") if key.strip()]
            manuscript.citations.append(
                Citation(
                    ids.make(
                        "citation",
                        f"{source.path}:cite:{match.start()}:{cite_index}",
                        match.group(0),
                    ),
                    [],
                    match.group(0),
                    _locator(source, match.start(), match.end(), command=match.group(1)),
                    keys,
                )
            )

        for bib_index, match in enumerate(BIBITEM_RE.finditer(clean)):
            key, raw = match.group(1), match.group(2).strip()
            manuscript.references.append(
                Reference(
                    ids.make("reference", f"{source.path}:bibitem:{key}:{bib_index}", raw),
                    raw,
                    _locator(source, match.start(), match.end(), command="bibitem"),
                    {"citation-key": key},
                )
            )

        for macro in COMMAND_RE.finditer(clean):
            command = macro.group(1)
            if command not in KNOWN_COMMANDS and not command.startswith(("if", "fi")):
                manuscript.unsupported_content.append(
                    register_unsupported(
                        ids,
                        object_type="UNKNOWN_LATEX_MACRO",
                        locator=_locator(source, macro.start(), macro.end(), command=command),
                        reason=f"macro \\{command} is preserved but its content effect is unknown",
                        severity="BLOCKING",
                        raw_fragment=macro.group(0),
                    )
                )

        bibliography = re.finditer(r"\\bibliography\s*\{([^}]+)\}", clean)
        for match in bibliography:
            manuscript.unsupported_content.append(
                register_unsupported(
                    ids,
                    object_type="EXTERNAL_BIBLIOGRAPHY",
                    locator=_locator(source, match.start(), match.end(), command="bibliography"),
                    reason="bibliography declaration preserved; external database parsing is deferred",
                    severity="WARNING",
                    raw_fragment=match.group(0),
                )
            )

    if not manuscript.metadata["title"]:
        manuscript.metadata["title"] = ""
    return manuscript
