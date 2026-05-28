"""
Core .docx template fill engine.

Unpacks a .docx ZIP, scans XML for {{PLACEHOLDER}} markers,
replaces them with provided values, strips template styling,
repacks, and validates.
"""

import io
import re
import zipfile
from copy import deepcopy

from lxml import etree

from .xml_utils import (
    BODY,
    CONTENT_PARTS,
    B,
    COLOR,
    I,
    FLDCHAR,
    ICS,
    INSTRTEXT,
    NUMPR,
    P,
    PPR,
    PSTYLE,
    R,
    RPR,
    T,
    TBL,
    TR,
    VAL,
    XML_SPACE,
    escape_xml,
    secure_fromstring,
)

PLACEHOLDER_RE = re.compile(r"\{\{([A-Z][A-Z0-9_]*)\}\}")


def fill_template(
    template_path: str,
    values: dict[str, str],
    structured: dict | None = None,
) -> bytes:
    """
    Fill a .docx template with the given values.

    Args:
        template_path: Path to the .docx template file.
        values: Mapping of scalar placeholder keys (without braces) to values.
        structured: Optional variable-length data for the General Document —
            lists of abbreviations/references/revisions/sections. When given,
            repeatable template rows/section-blocks are cloned to match.

    Returns:
        Bytes of the completed .docx file.
    """
    with open(template_path, "rb") as f:
        template_bytes = f.read()

    # Escape XML entities in all values. Newlines are preserved here (no longer
    # collapsed to spaces) so _split_paragraphs can render them as real
    # paragraph breaks after substitution.
    safe_values = {k: escape_xml(v) for k, v in values.items()}

    parts = _unpack(template_bytes)
    modified_parts: dict[str, bytes] = {}

    for part_name in CONTENT_PARTS:
        if part_name not in parts:
            continue

        tree = secure_fromstring(parts[part_name])
        # Clone repeatable blocks before anything else so the rest of the
        # pipeline (merge/fill/split/prune) treats them like normal content.
        if structured is not None and part_name == "word/document.xml":
            _expand_general(tree, structured)
        _merge_runs(tree)
        _fill_placeholders(tree, safe_values)
        _split_paragraphs(tree)
        _prune_empty_blocks(tree)
        modified_parts[part_name] = etree.tostring(tree, xml_declaration=True, encoding="UTF-8", standalone=True)

    output = _repack(template_bytes, modified_parts)
    _validate(output, safe_values)
    return output


def _unpack(docx_bytes: bytes) -> dict[str, bytes]:
    """Extract all files from a .docx ZIP archive."""
    parts = {}
    with zipfile.ZipFile(io.BytesIO(docx_bytes), "r") as zf:
        for name in zf.namelist():
            parts[name] = zf.read(name)
    return parts


def _merge_runs(tree: etree._Element) -> None:
    """
    Merge adjacent <w:r> runs that have identical <w:rPr> formatting.

    Word sometimes splits a single text span like {{PLACEHOLDER}} across
    multiple runs. This merges them back together so regex replacement works.
    """
    for parent in tree.iter():
        children = list(parent)
        i = 0
        while i < len(children) - 1:
            run = children[i]
            next_run = children[i + 1]

            if run.tag != R or next_run.tag != R:
                i += 1
                continue

            if _runs_mergeable(run, next_run):
                # Move every child of next_run except its <w:rPr> (formatting,
                # identical to run's) into run, preserving order. This keeps
                # breaks, tabs, drawings, etc. that an earlier <w:t>-only merge
                # would have silently dropped.
                movable = [c for c in next_run if c.tag != RPR]
                run_texts = run.findall(T)

                # If both sides have text at the boundary, concatenate it into a
                # single <w:t> so a placeholder split across runs (e.g. "{{",
                # "KEY", "}}") reassembles for the regex pass.
                if run_texts and movable and movable[0].tag == T:
                    last_t = run_texts[-1]
                    first_next_t = movable.pop(0)
                    last_t.text = (last_t.text or "") + (first_next_t.text or "")
                    last_t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")

                for child in movable:
                    run.append(child)

                # Remove the merged run
                parent.remove(next_run)
                children = list(parent)
                # Don't increment i — check if next sibling can also merge
            else:
                i += 1


def _run_has_field(run: etree._Element) -> bool:
    """True if a run participates in a Word field (PAGE, NUMPAGES, TOC, ...)."""
    return run.find(FLDCHAR) is not None or run.find(INSTRTEXT) is not None


def _runs_mergeable(run_a: etree._Element, run_b: etree._Element) -> bool:
    """Check if two runs have identical formatting properties."""
    # Never merge field runs: merging the runs around a PAGE/NUMPAGES field
    # concatenates the surrounding literals and scrambles the field, breaking
    # page numbers in headers/footers.
    if _run_has_field(run_a) or _run_has_field(run_b):
        return False

    rpr_a = run_a.find(RPR)
    rpr_b = run_b.find(RPR)

    if rpr_a is None and rpr_b is None:
        return True
    if rpr_a is None or rpr_b is None:
        return False

    # Compare by serializing to canonical XML (strips namespace declarations)
    return _canonical_rpr(rpr_a) == _canonical_rpr(rpr_b)


def _canonical_rpr(rpr: etree._Element) -> bytes:
    """Serialize run properties to a canonical form for comparison."""
    clone = deepcopy(rpr)
    return etree.tostring(clone, method="c14n2")


def _fill_placeholders(tree: etree._Element, values: dict[str, str]) -> None:
    """
    Replace {{KEY}} placeholders in all <w:t> elements.

    Handles multiple placeholders in a single <w:t> element
    (e.g., "{{DOCUMENT_ID}}  Rev {{REVISION}}").
    """
    for t_elem in tree.iter(T):
        text = t_elem.text
        if not text or "{{" not in text:
            continue

        had_placeholder = False

        def replace_match(m: re.Match) -> str:
            nonlocal had_placeholder
            key = m.group(1)
            if key in values:
                had_placeholder = True
                return values[key]
            return m.group(0)  # Leave unfound placeholders as-is

        new_text = PLACEHOLDER_RE.sub(replace_match, text)
        t_elem.text = new_text

        if had_placeholder:
            # Preserve spaces
            t_elem.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
            # Strip template styling from the parent run
            run = t_elem.getparent()
            if run is not None and run.tag == R:
                _strip_template_styling(run)


def _strip_template_styling(run: etree._Element) -> None:
    """
    Remove italic and gray color from a filled run.

    Template placeholders are styled italic + gray (#808080) as visual
    instructions. After filling, we strip these but preserve bold.
    """
    rpr = run.find(RPR)
    if rpr is None:
        return

    # Remove italic
    for elem in rpr.findall(I):
        rpr.remove(elem)
    for elem in rpr.findall(ICS):
        rpr.remove(elem)

    # Remove gray color (808080)
    for elem in rpr.findall(COLOR):
        val = elem.get("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val", "")
        if val.upper() == "808080":
            rpr.remove(elem)


def _enclosing_paragraph(elem: etree._Element) -> etree._Element | None:
    """Walk up from an element to its nearest <w:p> ancestor."""
    node = elem.getparent()
    while node is not None and node.tag != P:
        node = node.getparent()
    return node


def _split_paragraphs(tree: etree._Element) -> None:
    """
    Render newlines inside a filled value as real paragraph breaks.

    A filled value may contain '\\n' (e.g. multi-paragraph section content).
    A literal newline inside a <w:t> is treated as whitespace by Word, not a
    break, so for each extra paragraph we clone the enclosing <w:p> — preserving
    its paragraph properties (style, numbering, spacing) — and place it after.

    Only applies when the paragraph's sole non-empty text run is this element;
    paragraphs that mix multiple placeholders/runs fall back to space-joining so
    we never duplicate unrelated content.
    """
    for t_elem in list(tree.iter(T)):
        text = t_elem.text
        if not text or "\n" not in text:
            continue

        para = _enclosing_paragraph(t_elem)
        if para is None:
            t_elem.text = text.replace("\n", " ")
            continue

        content_ts = [t for t in para.iter(T) if (t.text or "").strip()]
        if len(content_ts) != 1 or content_ts[0] is not t_elem:
            # Mixed-content paragraph — don't clone it; keep on one line.
            t_elem.text = text.replace("\n", " ")
            t_elem.set(XML_SPACE, "preserve")
            continue

        # Drop empty segments so "\n\n" / trailing "\n" don't add blank paragraphs.
        segments = [s for s in text.split("\n") if s != ""]
        if not segments:
            t_elem.text = ""
            continue

        t_idx = list(para.iter(T)).index(t_elem)
        t_elem.text = segments[0]
        t_elem.set(XML_SPACE, "preserve")

        anchor = para
        for seg in segments[1:]:
            clone = deepcopy(para)
            clone_t = list(clone.iter(T))[t_idx]
            clone_t.text = seg
            clone_t.set(XML_SPACE, "preserve")
            anchor.addnext(clone)
            anchor = clone


def _para_text(para: etree._Element) -> str:
    """Concatenated text of all <w:t> in a paragraph."""
    return "".join(t.text or "" for t in para.iter(T))


def _is_numbered_heading(para: etree._Element) -> bool:
    """True for an auto-numbered section heading (Heading1/2/3 with <w:numPr>)."""
    ppr = para.find(PPR)
    if ppr is None:
        return False
    pstyle = ppr.find(PSTYLE)
    if pstyle is None or pstyle.get(VAL) not in ("Heading1", "Heading2", "Heading3"):
        return False
    return ppr.find(NUMPR) is not None


def _prune_empty_blocks(tree: etree._Element) -> None:
    """Remove leftover empty structure so partial documents look finished."""
    _prune_empty_rows(tree)
    _prune_empty_sections(tree)


def _prune_empty_rows(tree: etree._Element) -> None:
    """
    Drop fully-blank data rows from tables (abbreviations, references, revision
    history). The first <w:tr> (header) is always kept.
    """
    for tbl in list(tree.iter(TBL)):
        rows = tbl.findall(TR)  # direct child rows only
        for row in rows[1:]:
            if all(not (t.text or "").strip() for t in row.iter(T)):
                parent = row.getparent()
                if parent is not None:
                    parent.remove(row)


def _prune_empty_sections(tree: etree._Element) -> None:
    """
    Remove a numbered section/subsection (its heading paragraph plus the content
    paragraphs up to the next numbered heading) when the whole block is blank.
    Word recomputes the "1." / "1.1" labels via auto-numbering, so no renumber.
    """
    for body in tree.iter(BODY):
        children = list(body)
        n = len(children)
        to_remove: list[etree._Element] = []
        idx = 0
        while idx < n:
            el = children[idx]
            if el.tag == P and _is_numbered_heading(el):
                block = [el]
                j = idx + 1
                while j < n:
                    nxt = children[j]
                    if nxt.tag != P or _is_numbered_heading(nxt):
                        break
                    block.append(nxt)
                    j += 1
                if all(not _para_text(p).strip() for p in block):
                    to_remove.extend(block)
                idx = j
            else:
                idx += 1
        for el in to_remove:
            parent = el.getparent()
            if parent is not None:
                parent.remove(el)


# --- Variable-length expansion (General Document only) ------------------------


def _fill_marker(t_elem: etree._Element, value: str) -> None:
    """Set a placeholder <w:t> to a value and strip its template styling."""
    t_elem.text = value or ""  # lxml escapes on serialize — pass raw text
    t_elem.set(XML_SPACE, "preserve")
    run = t_elem.getparent()
    if run is not None and run.tag == R:
        _strip_template_styling(run)


def _fill_row_markers(row: etree._Element, marker_values: dict[str, str]) -> None:
    """Within a cloned row, replace each {{MARKER}} cell with its value."""
    for t in row.iter(T):
        txt = t.text or ""
        if "{{" not in txt:
            continue
        for marker, value in marker_values.items():
            if marker in txt:
                _fill_marker(t, value)
                break


def _row_text(tr: etree._Element) -> str:
    return "".join(t.text or "" for t in tr.iter(T))


def _expand_table(tree: etree._Element, base: str, items: list, markers) -> None:
    """
    Clone the template's '_1' data row once per item, fill it, then drop the
    original template rows. `markers(item)` -> {"{{KEY}}": value, ...}.
    """
    proto = None
    parent = None
    for tbl in tree.iter(TBL):
        for tr in tbl.findall(TR):
            if "{{" + base + "_1" in _row_text(tr):
                proto, parent = tr, tbl
                break
        if proto is not None:
            break
    if proto is None:
        return

    region = [tr for tr in parent.findall(TR) if re.search(r"\{\{" + base + r"_\d", _row_text(tr))]

    anchor = proto
    for item in items:
        clone = deepcopy(proto)
        _fill_row_markers(clone, markers(item))
        anchor.addnext(clone)
        anchor = clone

    for tr in region:  # remove the original template rows
        parent.remove(tr)


def _set_para_marker(para: etree._Element, value: str) -> None:
    """Set the single placeholder <w:t> inside a cloned heading/content para."""
    for t in para.iter(T):
        if "{{" in (t.text or ""):
            _fill_marker(t, value)
            return


def _expand_sections(tree: etree._Element, sections: list) -> None:
    """
    Rebuild the numbered sections from a variable-length list. Clones the
    template's heading/content paragraphs (keeping their <w:numPr>, so Word
    auto-renumbers) for each section, subsection, and sub-subsection.
    """
    def find_para(marker: str):
        for p in tree.iter(P):
            if marker in "".join(t.text or "" for t in p.iter(T)):
                return p
        return None

    h1 = find_para("{{SECTION_1_TITLE}}")
    content = find_para("{{SECTION_1_CONTENT}}")
    if h1 is None or content is None:
        return
    h2 = find_para("{{SECTION_1_1_TITLE}}")
    if h2 is None:
        h2 = h1
    h3 = find_para("{{SECTION_1_1_1_TITLE}}")

    body = h1.getparent()
    h1p, cp, h2p = deepcopy(h1), deepcopy(content), deepcopy(h2)
    h3p = deepcopy(h3) if h3 is not None else None

    # Every paragraph that holds a SECTION_* placeholder is part of the region.
    sec_paras = [
        p for p in list(body)
        if p.tag == P and "{{SECTION_" in "".join(t.text or "" for t in p.iter(T))
    ]
    if not sec_paras:
        return
    anchor = sec_paras[0]

    def block(proto, value):
        node = deepcopy(proto)
        _set_para_marker(node, value)
        return node

    new_nodes: list[etree._Element] = []
    for sec in sections:
        new_nodes.append(block(h1p, sec.get("title", "")))
        new_nodes.append(block(cp, sec.get("content", "")))
        for sub in sec.get("subsections", []) or []:
            new_nodes.append(block(h2p, sub.get("title", "")))
            new_nodes.append(block(cp, sub.get("content", "")))
            for ss in (sub.get("subsubsections", []) or []):
                if h3p is None:
                    break
                new_nodes.append(block(h3p, ss.get("title", "")))
                new_nodes.append(block(cp, ss.get("content", "")))

    for node in new_nodes:
        anchor.addprevious(node)
    for p in sec_paras:
        body.remove(p)


def _expand_general(tree: etree._Element, data: dict) -> None:
    """Expand all variable-length regions of the General Document."""
    _expand_table(
        tree, "ABBREV", data.get("abbreviations", []) or [],
        lambda i: {"{{ABBREV_1}}": i.get("term", ""), "{{ABBREV_1_DEF}}": i.get("definition", "")},
    )
    _expand_table(
        tree, "REF", data.get("references", []) or [],
        lambda i: {"{{REF_1_ID}}": i.get("id", ""), "{{REF_1_TITLE}}": i.get("title", "")},
    )
    _expand_table(
        tree, "REV", data.get("revisions", []) or [],
        lambda i: {
            "{{REV_1_VERSION}}": i.get("version", ""), "{{REV_1_DATE}}": i.get("date", ""),
            "{{REV_1_AUTHOR}}": i.get("author", ""), "{{REV_1_DESCRIPTION}}": i.get("description", ""),
        },
    )
    _expand_sections(tree, data.get("sections", []) or [])


def _repack(original_bytes: bytes, modified_parts: dict[str, bytes]) -> bytes:
    """
    Repack a .docx ZIP, replacing only the modified XML parts.

    Preserves all non-modified content (images, relationships, styles, etc.)
    exactly as-is from the original.
    """
    output = io.BytesIO()

    with zipfile.ZipFile(io.BytesIO(original_bytes), "r") as original_zip:
        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as new_zip:
            for item in original_zip.infolist():
                if item.filename in modified_parts:
                    new_zip.writestr(item, modified_parts[item.filename])
                else:
                    new_zip.writestr(item, original_zip.read(item.filename))

    return output.getvalue()


def _validate(output_bytes: bytes, values: dict[str, str]) -> None:
    """
    Validate the output .docx:
    1. ZIP is valid
    2. XML is well-formed
    3. No unfilled {{}} placeholders remain (for keys that were provided)
    """
    # 1. ZIP validity
    try:
        with zipfile.ZipFile(io.BytesIO(output_bytes), "r") as zf:
            bad = zf.testzip()
            if bad is not None:
                raise ValueError(f"Corrupt ZIP entry: {bad}")

            # 2. XML well-formedness for content parts
            for part_name in CONTENT_PARTS:
                if part_name in [info.filename for info in zf.infolist()]:
                    xml_bytes = zf.read(part_name)
                    try:
                        tree = secure_fromstring(xml_bytes)
                    except etree.XMLSyntaxError as e:
                        raise ValueError(f"Malformed XML in {part_name}: {e}")

                    # 3. Check for unfilled placeholders that should have been filled
                    for t_elem in tree.iter(T):
                        text = t_elem.text or ""
                        for m in PLACEHOLDER_RE.finditer(text):
                            key = m.group(1)
                            if key in values:
                                raise ValueError(
                                    f"Unfilled placeholder {{{{{key}}}}} "
                                    f"remains in {part_name}"
                                )

    except zipfile.BadZipFile as e:
        raise ValueError(f"Output is not a valid ZIP: {e}")
