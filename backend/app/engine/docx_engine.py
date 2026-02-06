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
    CONTENT_PARTS,
    B,
    COLOR,
    I,
    ICS,
    R,
    RPR,
    T,
    escape_xml,
)

PLACEHOLDER_RE = re.compile(r"\{\{([A-Z][A-Z0-9_]*)\}\}")


def fill_template(template_path: str, values: dict[str, str]) -> bytes:
    """
    Fill a .docx template with the given values.

    Args:
        template_path: Path to the .docx template file.
        values: Mapping of placeholder keys (without braces) to fill values.

    Returns:
        Bytes of the completed .docx file.
    """
    with open(template_path, "rb") as f:
        template_bytes = f.read()

    # Escape XML entities in all values
    safe_values = {k: escape_xml(v.replace("\n", " ")) for k, v in values.items()}

    parts = _unpack(template_bytes)
    modified_parts: dict[str, bytes] = {}

    for part_name in CONTENT_PARTS:
        if part_name not in parts:
            continue

        tree = etree.fromstring(parts[part_name])
        _merge_runs(tree)
        _fill_placeholders(tree, safe_values)
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
                # Append all text from next_run into run
                run_texts = run.findall(T)
                next_texts = next_run.findall(T)

                if run_texts and next_texts:
                    # Concatenate text of last <w:t> in run with first <w:t> in next_run
                    last_t = run_texts[-1]
                    first_next_t = next_texts[0]
                    last_t.text = (last_t.text or "") + (first_next_t.text or "")
                    last_t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")

                    # Move remaining <w:t> elements
                    for extra_t in next_texts[1:]:
                        run.append(extra_t)
                elif next_texts:
                    for nt in next_texts:
                        run.append(nt)

                # Remove the merged run
                parent.remove(next_run)
                children = list(parent)
                # Don't increment i — check if next sibling can also merge
            else:
                i += 1


def _runs_mergeable(run_a: etree._Element, run_b: etree._Element) -> bool:
    """Check if two runs have identical formatting properties."""
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
                        tree = etree.fromstring(xml_bytes)
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
