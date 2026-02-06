"""
Extract plain text from uploaded documents (.docx, .pdf, .txt).
"""

import io
import zipfile

from lxml import etree

from app.engine.xml_utils import T


def extract_text(file_bytes: bytes, filename: str) -> str:
    """
    Extract plain text from a document based on its file extension.

    Args:
        file_bytes: Raw bytes of the uploaded file.
        filename: Original filename (used to determine type).

    Returns:
        Extracted plain text content.
    """
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext == "txt":
        return _extract_txt(file_bytes)
    elif ext == "docx":
        return _extract_docx(file_bytes)
    elif ext == "pdf":
        return _extract_pdf(file_bytes)
    else:
        raise ValueError(f"Unsupported file type: .{ext}. Supported: .docx, .pdf, .txt")


def _extract_txt(file_bytes: bytes) -> str:
    """Decode and return text content."""
    for encoding in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            return file_bytes.decode(encoding)
        except UnicodeDecodeError:
            continue
    return file_bytes.decode("utf-8", errors="replace")


def _extract_docx(file_bytes: bytes) -> str:
    """Extract text from .docx by reading <w:t> elements from document.xml."""
    texts = []
    with zipfile.ZipFile(io.BytesIO(file_bytes), "r") as zf:
        if "word/document.xml" not in zf.namelist():
            raise ValueError("Invalid .docx: missing word/document.xml")
        tree = etree.fromstring(zf.read("word/document.xml"))
        for t_elem in tree.iter(T):
            if t_elem.text:
                texts.append(t_elem.text)
    return "\n".join(texts)


def _extract_pdf(file_bytes: bytes) -> str:
    """Extract text from .pdf using PyMuPDF."""
    import fitz  # PyMuPDF

    doc = fitz.open(stream=file_bytes, filetype="pdf")
    texts = []
    for page in doc:
        texts.append(page.get_text())
    doc.close()
    return "\n".join(texts)
