"""Deterministic synthetic DOCX package builder used only by parser tests."""

from __future__ import annotations

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
M = "http://schemas.openxmlformats.org/officeDocument/2006/math"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


def _paragraph(text: str, style: str | None = None) -> str:
    style_xml = f'<w:pPr><w:pStyle w:val="{style}"/></w:pPr>' if style else ""
    return f"<w:p>{style_xml}<w:r><w:t>{text}</w:t></w:r></w:p>"


def build_docx(path: Path, *, hazards: bool = False) -> Path:
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
    document = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
    <w:document xmlns:w="{W}" xmlns:m="{M}" xmlns:a="{A}" xmlns:r="{R}"><w:body>
      {_paragraph("Synthetic DOCX study", "Title")}
      {_paragraph("Abstract", "Heading1")}
      {_paragraph("We summarize 6 observations.")}
      {_paragraph("Results", "Heading1")}
      {_paragraph("We measured 42 samples; response 12.5% and p &lt; 0.01.")}
      <w:p><w:r><w:instrText>CITATION doe2025</w:instrText><w:t>[1]</w:t></w:r></w:p>
      <w:p><m:oMath><m:r><m:t>y=2x+1</m:t></m:r></m:oMath></w:p>
      <w:p><w:r><w:drawing><a:blip r:embed="rIdImage1"/></w:drawing></w:r></w:p>
      {_paragraph("Figure 1 Synthetic signal.", "Caption")}
      <w:tbl><w:tr><w:tc>{_paragraph("A")}</w:tc><w:tc>{_paragraph("2")}</w:tc></w:tr></w:tbl>
      {_paragraph("Table 1 Synthetic values.", "Caption")}
      {_paragraph("References", "Heading1")}
      {_paragraph("Doe J. Synthetic reference. 2025.")}
      {tracked}{unknown_field}{unsupported}
      <w:sectPr/>
    </w:body></w:document>"""
    relationships = """<?xml version="1.0" encoding="UTF-8"?>
    <Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
      <Relationship Id="rIdImage1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/image1.png"/>
    </Relationships>"""
    core = """<?xml version="1.0" encoding="UTF-8"?>
    <cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:title>Synthetic DOCX study</dc:title><dc:creator>Ada Example</dc:creator></cp:coreProperties>"""
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
