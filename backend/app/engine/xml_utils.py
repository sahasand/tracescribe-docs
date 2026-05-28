"""XML namespace helpers and entity escaping for WordprocessingML."""

from lxml import etree

NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

# XML parts in a .docx that can contain placeholders
CONTENT_PARTS = [
    "word/document.xml",
    "word/header1.xml",
    "word/header2.xml",
    "word/header3.xml",
    "word/footer1.xml",
    "word/footer2.xml",
    "word/footer3.xml",
]


def tag(name: str) -> str:
    """Return a fully-qualified WordprocessingML tag name."""
    return f"{{{NS}}}{name}"


# Pre-computed tags used throughout the engine
T = tag("t")       # <w:t> — text element
R = tag("r")       # <w:r> — run element
RPR = tag("rPr")   # <w:rPr> — run properties
I = tag("i")       # <w:i> — italic
ICS = tag("iCs")   # <w:iCs> — complex-script italic
COLOR = tag("color")  # <w:color> — text color
B = tag("b")       # <w:b> — bold

# Structural tags for paragraph-splitting and empty-block pruning
P = tag("p")          # <w:p> — paragraph
TBL = tag("tbl")      # <w:tbl> — table
TR = tag("tr")        # <w:tr> — table row
BODY = tag("body")    # <w:body> — document body
PPR = tag("pPr")      # <w:pPr> — paragraph properties
PSTYLE = tag("pStyle")  # <w:pStyle> — paragraph style ref
NUMPR = tag("numPr")  # <w:numPr> — numbering properties (auto-numbered headings)
VAL = tag("val")      # the w:val attribute

# The xml:space attribute (not in the wordprocessingml namespace)
XML_SPACE = "{http://www.w3.org/XML/1998/namespace}space"


_XML_ESCAPE_MAP = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&apos;",
}


def escape_xml(text: str) -> str:
    """Escape XML special characters in fill values."""
    for char, entity in _XML_ESCAPE_MAP.items():
        text = text.replace(char, entity)
    return text


def secure_fromstring(data: bytes) -> etree._Element:
    """
    Parse XML from untrusted bytes with entity expansion disabled.

    Uploaded .docx files are user-controlled. A hardened parser blocks
    entity-expansion ("billion laughs") and external-entity (XXE) attacks:
    `resolve_entities=False` stops internal entity bombs, `no_network=True`
    and `load_dtd=False` block external/DTD fetches, `huge_tree=False`
    caps document size. A fresh parser is created per call because lxml
    parsers are not safe to share across threads.
    """
    parser = etree.XMLParser(
        resolve_entities=False,
        no_network=True,
        load_dtd=False,
        huge_tree=False,
    )
    return etree.fromstring(data, parser)
