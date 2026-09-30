"""Deterministic synthetic DOCX package builder used only by parser tests."""

from __future__ import annotations

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
M = "http://schemas.openxmlformats.org/officeDocument/2006/math"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


def _paragraph(
    text: str,
    style: str | None = None,
    *,
    bold: bool = False,
    centered: bool = False,
    spaced: bool = False,
    font_half_points: int | None = None,
) -> str:
    properties = ""
    if style:
        properties += f'<w:pStyle w:val="{style}"/>'
    if centered:
        properties += '<w:jc w:val="center"/>'
    if spaced:
        properties += '<w:spacing w:before="120" w:after="240"/>'
    style_xml = f"<w:pPr>{properties}</w:pPr>" if properties else ""
    run_properties = ("<w:b/>" if bold else "") + (
        f'<w:sz w:val="{font_half_points}"/>' if font_half_points is not None else ""
    )
    run_xml = f"<w:rPr>{run_properties}</w:rPr>" if run_properties else ""
    return f"<w:p>{style_xml}<w:r>{run_xml}<w:t>{text}</w:t></w:r></w:p>"


def _mixed_paragraph(runs: tuple[tuple[str, bool], ...], style: str | None = None) -> str:
    style_xml = f'<w:pPr><w:pStyle w:val="{style}"/></w:pPr>' if style else ""
    run_xml = "".join(
        f"<w:r>{'<w:rPr><w:b/></w:rPr>' if bold else ''}<w:t>{text}</w:t></w:r>"
        for text, bold in runs
    )
    return f"<w:p>{style_xml}{run_xml}</w:p>"


def build_docx(
    path: Path,
    *,
    hazards: bool = False,
    abstract_heading: str = "styled",
    front_matter: bool = False,
    numbered_introduction: bool = False,
    warning_field: bool = False,
    title_mode: str = "styled",
    core_title: bool = True,
    real_world_structure: bool = False,
    custom_numbered: tuple[tuple[str, bool], ...] = (),
    abstract_after_introduction: bool = False,
) -> Path:
    tracked = ""
    unsupported = ""
    unknown_field = ""
    if hazards:
        tracked = """
        <w:p><w:r><w:t>Baseline 10 and </w:t></w:r>
          <w:del w:id="1"><w:r><w:delText>citation [1]</w:delText></w:r></w:del>
          <w:ins w:id="2"><w:r><w:t>citation [2] with 11</w:t></w:r></w:ins>
          <w:ins w:id="3"><w:r><w:t> plus 12</w:t></w:r></w:ins></w:p>
        """
        unsupported = "<w:object><w:r><w:t>embedded result 99</w:t></w:r></w:object>"
        unknown_field = '<w:p><w:fldSimple w:instr="UNKNOWN"><w:r><w:instrText>UNKNOWN SCIENCE</w:instrText><w:t>7.3</w:t></w:r></w:fldSimple></w:p>'
    elif warning_field:
        unknown_field = "<w:p><w:r><w:instrText>REF bookmark</w:instrText><w:t>cross-reference</w:t></w:r></w:p>"
    abstract_paragraph = {
        "styled": _paragraph("Abstract", "Heading1"),
        "custom_styled": _paragraph("Abstract", "Abstract", spaced=True),
        "plain": _paragraph("Abstract"),
        "bold": _paragraph("Abstract", bold=True),
        "plain_colon": _paragraph("Abstract:", spaced=True),
        "inline": _mixed_paragraph(
            (("Abstract", True), ("The outlook includes 6 observations and citation [1].", False)),
            "BodyText",
        ),
        "inline_colon": _mixed_paragraph(
            (
                ("Abstract:", True),
                (" The outlook includes 6 observations and citation [1].", False),
            ),
            "BodyText",
        ),
        "body_sentence": _paragraph("Abstract models can support scientific discovery."),
        "flattened": _paragraph(
            "AbstractThe outlook of an AI-driven digital organism includes 6 observations and value 12.5%.",
            "BodyText",
        ),
        "flattened_space": _paragraph(
            "Abstract The outlook of an AI-driven digital organism includes 6 observations and value 12.5%.",
            "BodyText",
        ),
        "flattened_colon": _paragraph(
            "Abstract: The outlook of an AI-driven digital organism includes 6 observations and value 12.5%.",
            "BodyText",
        ),
        "abstractly": _paragraph(
            "Abstractly stated ideas in this paragraph include 6 observations and value 12.5%.",
            "BodyText",
        ),
        "abstract_concepts": _paragraph(
            "Abstract concepts in this paragraph include 6 observations and value 12.5% for comparison.",
            "BodyText",
        ),
        "ambiguous": _paragraph("This abstract describes prior work."),
    }[abstract_heading]
    title_paragraph = {
        "styled": _paragraph("Synthetic DOCX study", "Title"),
        "bold_centered": _paragraph("Synthetic DOCX study", bold=True, centered=True),
        "bold_bodytext": _paragraph(
            "A World Model of the Virtual Cell",
            "BodyText",
            bold=True,
            font_half_points=34,
        ),
        "plain": _paragraph("Synthetic DOCX study"),
        "ambiguous": _paragraph("This paragraph discusses preliminary observations."),
        "none": "",
    }[title_mode]
    front = (
        _paragraph("Ada Example and Charles Example")
        + _paragraph("Example Institute; contact@example.invalid")
        + _paragraph("30 September 2026")
        if front_matter
        else ""
    )
    introduction = _paragraph(
        "1 Introduction" if numbered_introduction else "Results",
        None if numbered_introduction else "Heading1",
    )
    if custom_numbered:
        introduction = "".join(
            _paragraph(value, "BodyText", bold=bold) + _paragraph("Section body text.")
            for value, bold in custom_numbered
        )
    if real_world_structure:
        title_paragraph = _paragraph(
            "A World Model of the Virtual Cell",
            "BodyText",
            bold=True,
            font_half_points=34,
        )
        front = (
            _paragraph("Ada Example and Charles Example", "BodyText", bold=True)
            + _paragraph("Example Institute", "BodyText", bold=True)
            + _paragraph("ada@example.invalid; charles@example.invalid", "BodyText")
            + _paragraph("30 September 2026", "BodyText")
        )
        if abstract_heading not in {
            "flattened",
            "flattened_space",
            "flattened_colon",
            "abstractly",
            "abstract_concepts",
        }:
            abstract_paragraph = _mixed_paragraph(
                (
                    ("Abstract", True),
                    ("The outlook includes 6 observations, citation [1], and value 12.5%.", False),
                ),
                "BodyText",
            )
        headings = (
            "1   Introduction",
            "2   Operational Definition",
            "3   What can a Virtual Cell be Used for Biomedicine?",
            "4   Architecture of a Virtual Cell World Model",
            "5   Key Differentiator",
            "6   Data Requirements",
            "7   Why a World Model?",
            "8   Computational and Technical Hurdles",
            "9   Evaluation",
            "10  From Integration to Holistic Modeling",
            "11  Toward Virtual Cell Banks and Digital Organisms",
            "12  Conclusion",
        )
        introduction = "".join(
            _paragraph(heading, "BodyText", bold=True)
            + _paragraph(f"Body text for section {position}.", "BodyText")
            for position, heading in enumerate(headings, start=1)
        )
    document = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
    <w:document xmlns:w="{W}" xmlns:m="{M}" xmlns:a="{A}" xmlns:r="{R}"><w:body>
      {title_paragraph}
      {front}
      {"" if abstract_after_introduction else abstract_paragraph}
      {"" if real_world_structure else _paragraph("We summarize 6 observations.")}
      {introduction}
      {abstract_paragraph if abstract_after_introduction else ""}
      {"" if real_world_structure else _paragraph("We measured 42 samples; response 12.5% and p &lt; 0.01.")}
      <w:p><w:r><w:instrText>CITATION doe2025</w:instrText><w:t>[1]</w:t></w:r></w:p>
      <w:p><m:oMath><m:r><m:t>y=2x+1</m:t></m:r></m:oMath></w:p>
      <w:p><w:r><w:drawing><a:blip r:embed="rIdImage1"/></w:drawing></w:r></w:p>
      {_paragraph("Figure 1 Synthetic signal.", "Caption")}
      <w:tbl><w:tr><w:tc>{_paragraph("A")}</w:tc><w:tc>{_paragraph("2")}</w:tc></w:tr></w:tbl>
      {_paragraph("Table 1 Synthetic values.", "Caption")}
      {_paragraph("References", "BodyText", bold=True) if real_world_structure else _paragraph("References", "Heading1")}
      {_paragraph("Doe J. Synthetic reference. 2025.")}
      {tracked}{unknown_field}{unsupported}
      <w:sectPr/>
    </w:body></w:document>"""
    relationships = """<?xml version="1.0" encoding="UTF-8"?>
    <Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
      <Relationship Id="rIdImage1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/image1.png"/>
    </Relationships>"""
    core_title_xml = "<dc:title>Synthetic DOCX study</dc:title>" if core_title else ""
    core = f"""<?xml version="1.0" encoding="UTF-8"?>
    <cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/">{core_title_xml}<dc:creator>Ada Example</dc:creator></cp:coreProperties>"""
    footnotes = f"""<?xml version="1.0" encoding="UTF-8"?>
    <w:footnotes xmlns:w="{W}"><w:footnote w:id="1">{_paragraph("Synthetic footnote 3.14")}</w:footnote></w:footnotes>"""
    endnotes = f"""<?xml version="1.0" encoding="UTF-8"?>
    <w:endnotes xmlns:w="{W}"><w:endnote w:id="1">{_paragraph("Synthetic endnote")}</w:endnote></w:endnotes>"""
    with ZipFile(path, "w", ZIP_DEFLATED) as archive:
        archive.writestr("word/document.xml", document)
        archive.writestr("word/_rels/document.xml.rels", relationships)
        archive.writestr("word/media/image1.png", b"synthetic-image-bytes")
        archive.writestr("word/footnotes.xml", footnotes)
        archive.writestr("word/endnotes.xml", endnotes)
        archive.writestr("docProps/core.xml", core)
    return path
