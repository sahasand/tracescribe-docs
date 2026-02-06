"""XML namespace helpers and entity escaping for WordprocessingML."""

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
