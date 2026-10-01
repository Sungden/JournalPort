"""Profile-driven Word properties; unspecified typography and page dimensions are untouched."""

from __future__ import annotations

from lxml import etree

from .structure import W

ROLES = (
    "JP_TITLE",
    "JP_AUTHOR",
    "JP_AFFILIATION",
    "JP_ABSTRACT",
    "JP_BODY",
    "JP_HEADING_1",
    "JP_HEADING_2",
    "JP_FIGURE_LEGEND",
    "JP_TABLE_TITLE",
    "JP_REFERENCES",
    "JP_ADMIN_HEADING",
    "JP_ADMIN_BODY",
)

PROPERTY_ORDER = {
    "sectPr": (
        "headerReference",
        "footerReference",
        "footnotePr",
        "endnotePr",
        "type",
        "pgSz",
        "pgMar",
        "paperSrc",
        "pgBorders",
        "lnNumType",
        "pgNumType",
        "cols",
        "formProt",
        "vAlign",
        "noEndnote",
        "titlePg",
        "textDirection",
        "bidi",
        "rtlGutter",
        "docGrid",
        "printerSettings",
        "sectPrChange",
    ),
    "pPr": (
        "pStyle",
        "keepNext",
        "keepLines",
        "pageBreakBefore",
        "framePr",
        "widowControl",
        "numPr",
        "suppressLineNumbers",
        "pBdr",
        "shd",
        "tabs",
        "suppressAutoHyphens",
        "kinsoku",
        "wordWrap",
        "overflowPunct",
        "topLinePunct",
        "autoSpaceDE",
        "autoSpaceDN",
        "bidi",
        "adjustRightInd",
        "snapToGrid",
        "spacing",
        "ind",
        "contextualSpacing",
        "mirrorIndents",
        "suppressOverlap",
        "jc",
        "textDirection",
        "textAlignment",
        "textboxTightWrap",
        "outlineLvl",
        "divId",
        "cnfStyle",
        "rPr",
        "sectPr",
        "pPrChange",
    ),
}


def property_node(parent: etree._Element, tag: str) -> etree._Element:
    found = parent.find(W + tag)
    if found is None:
        found = etree.Element(W + tag)
        order = PROPERTY_ORDER.get(etree.QName(parent).localname, ())
        rank = order.index(tag) if tag in order else len(order)
        insertion = next(
            (
                index
                for index, child in enumerate(parent)
                if etree.QName(child).localname in order
                and order.index(etree.QName(child).localname) > rank
            ),
            len(parent),
        )
        parent.insert(insertion, found)
    return found


def paragraph_property(paragraph: etree._Element, tag: str) -> etree._Element:
    props = paragraph.find(W + "pPr")
    if props is None:
        props = etree.Element(W + "pPr")
        paragraph.insert(0, props)
    return property_node(props, tag)


def apply_line_spacing(body: etree._Element, multiple: float) -> None:
    if multiple != 2:
        raise ValueError("unsupported verified line spacing")
    for paragraph in body.iter(W + "p"):
        spacing = paragraph_property(paragraph, "spacing")
        spacing.set(W + "line", "480")
        spacing.set(W + "lineRule", "auto")


def apply_alignment(body: etree._Element, alignment: str) -> None:
    if alignment != "LEFT":
        raise ValueError("unsupported verified alignment")
    for paragraph in body.iter(W + "p"):
        paragraph_property(paragraph, "jc").set(W + "val", "left")


def apply_columns(body: etree._Element, count: int) -> None:
    if count != 1:
        raise ValueError("unsupported verified column target")
    sections = list(body.iter(W + "sectPr"))
    if not sections:
        sections = [etree.SubElement(body, W + "sectPr")]
    for section in sections:
        columns = property_node(section, "cols")
        for column in list(columns):
            columns.remove(column)
        columns.set(W + "num", "1")
        columns.set(W + "equalWidth", "1")


def page_footer() -> bytes:
    root = etree.Element(W + "ftr", nsmap={"w": W[1:-1]})
    paragraph = etree.SubElement(root, W + "p")
    field = etree.SubElement(paragraph, W + "fldSimple")
    field.set(W + "instr", "PAGE \\* Arabic")
    etree.SubElement(etree.SubElement(field, W + "r"), W + "t").text = "1"
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
