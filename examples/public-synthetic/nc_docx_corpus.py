"""Public synthetic NC stress corpus generator. Contains no real manuscript data."""

from __future__ import annotations

import argparse
import struct
import zlib
from pathlib import Path
from xml.sax.saxutils import escape
from zipfile import ZIP_DEFLATED, ZipFile

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
WP = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
PIC = "http://schemas.openxmlformats.org/drawingml/2006/picture"
M = "http://schemas.openxmlformats.org/officeDocument/2006/math"


def png_chunk(kind: bytes, value: bytes) -> bytes:
    return (
        struct.pack(">I", len(value)) + kind + value + struct.pack(">I", zlib.crc32(kind + value))
    )


# Visible synthetic diagram, not an invisible one-pixel placeholder.
PNG = (
    b"\x89PNG\r\n\x1a\n"
    + png_chunk(b"IHDR", struct.pack(">IIBBBBB", 100, 60, 8, 2, 0, 0, 0))
    + png_chunk(
        b"IDAT",
        zlib.compress(
            b"".join(
                b"\x00" + bytes((35, 85, 145) if row < 30 else (180, 205, 230)) * 100
                for row in range(60)
            )
        ),
    )
    + png_chunk(b"IEND", b"")
)


def paragraph(value: str, style: str | None = None, bold: bool = False) -> str:
    properties = f'<w:pPr><w:pStyle w:val="{style}"/></w:pPr>' if style else ""
    run_properties = "<w:rPr><w:b/></w:rPr>" if bold else ""
    return f"<w:p>{properties}<w:r>{run_properties}<w:t>{escape(value)}</w:t></w:r></w:p>"


def drawing(number: int) -> str:
    return f'''<w:p><w:r><w:drawing><wp:inline>
    <wp:extent cx="914400" cy="914400"/><wp:docPr id="{number}" name="Figure {number}"/>
    <a:graphic><a:graphicData uri="{PIC}"><pic:pic>
    <pic:nvPicPr><pic:cNvPr id="{number}" name="Figure {number}"/><pic:cNvPicPr/></pic:nvPicPr>
    <pic:blipFill><a:blip r:embed="rIdImage{number}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>
    <pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="914400" cy="914400"/></a:xfrm>
    <a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr>
    </pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>'''


def build_case(destination: Path, case: int) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    messy = case == 2

    def heading(value: str) -> str:
        return paragraph(value, None if messy else "Heading1", bold=messy)

    count = 6 if case == 4 else 2
    ref_count = 30 if case == 3 else 5
    content = paragraph("Title: Synthetic cell measurement study", "BodyText" if messy else "Title")
    content += paragraph("Authors: Ada Example*; Charles Example")
    if messy:
        content += paragraph("Correspondence: ada@example.invalid")
    content += paragraph("Affiliations: Synthetic Institute of Measurement")
    if not messy:
        content += paragraph("Correspondence: ada@example.invalid")
    content += heading("Abstract") + paragraph(
        "We describe a synthetic study of a measurable signal."
    )
    for section in ("Introduction", "Methods", "Results", "Discussion"):
        content += heading(section)
        marker = "[1, 3–5]" if case == 3 else "[1–3]"
        content += paragraph(
            f"Synthetic {section.lower()} reports 42 samples, 12.5% response and p < 0.01 {marker}."
        )
        if section == "Results":
            for number in range(1, count + 1):
                content += drawing(number) + paragraph(
                    f"Fig. {number}. Synthetic signal panel {number}.", "Caption"
                )
            content += paragraph("Table 1. Synthetic measured values.", "Caption")
            content += "<w:tbl><w:tblPr/><w:tblGrid><w:gridCol w:w='2000'/><w:gridCol w:w='2000'/></w:tblGrid><w:tr>"
            content += (
                "<w:tc>"
                + paragraph("Signal")
                + "</w:tc><w:tc>"
                + paragraph("12.5")
                + "</w:tc></w:tr></w:tbl>"
            )
            if case == 4:
                content += paragraph("") + paragraph("Table 2. Synthetic merged cells.", "Caption")
                content += (
                    "<w:tbl><w:tblPr/><w:tblGrid><w:gridCol w:w='2000'/><w:gridCol w:w='2000'/></w:tblGrid><w:tr><w:tc><w:tcPr><w:gridSpan w:val='2'/></w:tcPr>"
                    + paragraph("Merged synthetic value 24")
                    + "</w:tc></w:tr></w:tbl>"
                )
                content += "<w:p><m:oMath><m:r><m:t>y=2x+1</m:t></m:r></m:oMath></w:p>"
    content += heading("Competing Interests") + paragraph(
        "Synthetic authors report a synthetic declaration."
    )
    content += heading("Author Contributions") + paragraph(
        "A.E. designed this synthetic fixture; C.E. checked it."
    )
    content += heading("Acknowledgements") + paragraph(
        "We acknowledge synthetic fixture contributors."
    )
    content += heading("References")
    for number in range(1, ref_count + 1):
        content += paragraph(
            f"{number}. Example, A.; Example, B. Synthetic reference {number}. Example J. 12, {number}–{number + 2} (2026). https://doi.org/10.0000/synthetic{number}"
        )
    if case == 5:
        content += "<w:p><m:oMath><m:r><m:t>y=2x+1</m:t></m:r></m:oMath></w:p>"
        content += '<w:p><w:r><w:fldChar w:fldCharType="begin"/></w:r><w:r><w:instrText> ADDIN ZOTERO_ITEM CSL_CITATION </w:instrText></w:r><w:r><w:fldChar w:fldCharType="end"/></w:r></w:p>'
        content += '<w:p><w:ins w:id="1" w:author="Synthetic"><w:r><w:t>Tracked synthetic text.</w:t></w:r></w:ins></w:p>'
    content += '<w:sectPr><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440"/><w:cols w:num="2"/></w:sectPr>'
    document = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
    <w:document xmlns:w="{W}" xmlns:r="{R}" xmlns:a="{A}" xmlns:wp="{WP}"
    xmlns:pic="{PIC}" xmlns:m="{M}" xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006"
    xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml" mc:Ignorable="w14"><w:body>{content}</w:body></w:document>'''
    relationships = f'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rIdStyles" Type="{R}/styles" Target="styles.xml"/>'
    relationships += (
        "".join(
            f'<Relationship Id="rIdImage{n}" Type="{R}/image" Target="media/image{n}.png"/>'
            for n in range(1, count + 1)
        )
        + "</Relationships>"
    )
    styles = f'<w:styles xmlns:w="{W}">'
    for name in ("Normal", "BodyText", "Title", "Heading1", "Caption"):
        styles += f'<w:style w:type="paragraph" w:styleId="{name}"><w:name w:val="{name}"/>'
        if name == "Heading1":
            styles += '<w:pPr><w:outlineLvl w:val="0"/></w:pPr>'
        styles += "</w:style>"
    styles += "</w:styles>"
    types = '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Default Extension="png" ContentType="image/png"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/><Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/></Types>'
    with ZipFile(destination, "w", ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", types)
        archive.writestr(
            "_rels/.rels",
            f'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="{R}/officeDocument" Target="word/document.xml"/></Relationships>',
        )
        archive.writestr("word/document.xml", document)
        archive.writestr("word/_rels/document.xml.rels", relationships)
        archive.writestr("word/styles.xml", styles)
        for number in range(1, count + 1):
            archive.writestr(f"word/media/image{number}.png", PNG)
    return destination


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    for case in range(1, 6):
        build_case(args.output / f"SYN-NC-{case:03}.docx", case)
