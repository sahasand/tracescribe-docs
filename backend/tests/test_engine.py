"""Tests for the core .docx template fill engine."""

import io
import re
import zipfile

import pytest
from lxml import etree

from app.engine.docx_engine import (
    fill_template,
    _merge_runs,
    _fill_placeholders,
    _split_paragraphs,
    _prune_empty_blocks,
    PLACEHOLDER_RE,
)
from app.engine.xml_utils import T, R, RPR, I, ICS, COLOR, NS, P, TBL, TR, escape_xml
from app.models.template_registry import TEMPLATES, get_template


TEMPLATES_DIR = get_template("sop").path.parent


# ---- Helper to extract all text from a .docx ----

def extract_text(docx_bytes: bytes) -> str:
    """Extract all <w:t> text from a .docx byte stream."""
    texts = []
    with zipfile.ZipFile(io.BytesIO(docx_bytes), "r") as zf:
        for name in zf.namelist():
            if name.startswith("word/") and name.endswith(".xml"):
                tree = etree.fromstring(zf.read(name))
                for t_elem in tree.iter(T):
                    if t_elem.text:
                        texts.append(t_elem.text)
    return "\n".join(texts)


def has_unfilled_placeholders(docx_bytes: bytes, keys: set[str]) -> list[str]:
    """Return any {{KEY}} placeholders still present for given keys."""
    text = extract_text(docx_bytes)
    found = []
    for m in PLACEHOLDER_RE.finditer(text):
        if m.group(1) in keys:
            found.append(m.group(1))
    return found


# ---- Tests ----


class TestEscapeXml:
    def test_ampersand(self):
        assert escape_xml("R&D") == "R&amp;D"

    def test_angle_brackets(self):
        assert escape_xml("<tag>") == "&lt;tag&gt;"

    def test_quotes(self):
        assert escape_xml('He said "hello"') == "He said &quot;hello&quot;"

    def test_no_escaping_needed(self):
        assert escape_xml("plain text") == "plain text"

    def test_all_entities(self):
        assert escape_xml("&<>\"'") == "&amp;&lt;&gt;&quot;&apos;"


class TestTemplateRegistry:
    def test_all_templates_exist(self):
        for key, info in TEMPLATES.items():
            assert info.path.exists(), f"Template file missing: {info.path}"

    def test_get_template_valid(self):
        info = get_template("sop")
        assert info.display_name == "Standard Operating Procedure"

    def test_get_template_invalid(self):
        with pytest.raises(KeyError, match="Unknown template type"):
            get_template("nonexistent")

    def test_placeholder_counts(self):
        expected = {"sop": 54, "deviation": 26, "capa": 39, "training": 35, "monitoring": 59, "general": 75}
        for key, count in expected.items():
            info = get_template(key)
            assert len(info.placeholders) == count, (
                f"{key}: expected {count} placeholders, got {len(info.placeholders)}"
            )


class TestFillTemplateSOP:
    """Test filling the SOP template — the most complex one."""

    def _make_values(self) -> dict[str, str]:
        info = get_template("sop")
        return {key: f"Test {key.lower().replace('_', ' ')}" for key in info.placeholders}

    def test_fill_returns_bytes(self):
        values = self._make_values()
        result = fill_template(str(get_template("sop").path), values)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_output_is_valid_zip(self):
        values = self._make_values()
        result = fill_template(str(get_template("sop").path), values)
        with zipfile.ZipFile(io.BytesIO(result), "r") as zf:
            assert zf.testzip() is None

    def test_no_unfilled_placeholders(self):
        values = self._make_values()
        result = fill_template(str(get_template("sop").path), values)
        unfilled = has_unfilled_placeholders(result, set(values.keys()))
        assert unfilled == [], f"Unfilled placeholders: {unfilled}"

    def test_values_present_in_output(self):
        values = self._make_values()
        result = fill_template(str(get_template("sop").path), values)
        text = extract_text(result)
        # Spot-check some values
        assert "Test purpose" in text
        assert "Test scope" in text
        assert "Test sop title" in text

    def test_xml_well_formed(self):
        values = self._make_values()
        result = fill_template(str(get_template("sop").path), values)
        with zipfile.ZipFile(io.BytesIO(result), "r") as zf:
            for name in zf.namelist():
                if name.endswith(".xml"):
                    xml_bytes = zf.read(name)
                    # Should parse without error
                    etree.fromstring(xml_bytes)

    def test_header_has_filled_values(self):
        """SOP header has {{DOCUMENT_ID}}  Rev {{REVISION}} in one <w:t>."""
        values = self._make_values()
        result = fill_template(str(get_template("sop").path), values)
        with zipfile.ZipFile(io.BytesIO(result), "r") as zf:
            header = etree.fromstring(zf.read("word/header1.xml"))
            header_text = " ".join(t.text for t in header.iter(T) if t.text)
            assert "Test document id" in header_text
            assert "Test revision" in header_text


class TestFillAllTemplates:
    """Smoke-test fill for every registered template."""

    @pytest.mark.parametrize("template_type", list(TEMPLATES.keys()))
    def test_fill_template(self, template_type):
        info = get_template(template_type)
        values = {key: f"Filled {key}" for key in info.placeholders}
        result = fill_template(str(info.path), values)

        # Valid ZIP
        with zipfile.ZipFile(io.BytesIO(result), "r") as zf:
            assert zf.testzip() is None

        # No unfilled placeholders
        unfilled = has_unfilled_placeholders(result, set(values.keys()))
        assert unfilled == [], f"[{template_type}] Unfilled: {unfilled}"


class TestStylingStrip:
    """Verify that italic and gray color are removed after filling."""

    def test_italic_removed(self):
        info = get_template("deviation")
        values = {key: f"Val {key}" for key in info.placeholders}
        result = fill_template(str(info.path), values)

        with zipfile.ZipFile(io.BytesIO(result), "r") as zf:
            tree = etree.fromstring(zf.read("word/document.xml"))

            for run in tree.iter(R):
                for t_elem in run.findall(T):
                    text = t_elem.text or ""
                    if text.startswith("Val "):
                        rpr = run.find(RPR)
                        if rpr is not None:
                            # Should not have italic
                            assert rpr.find(I) is None, f"Italic still present on: {text}"
                            assert rpr.find(ICS) is None, f"iCs still present on: {text}"
                            # Should not have gray color
                            for color in rpr.findall(COLOR):
                                val = color.get(f"{{{NS}}}val", "")
                                assert val.upper() != "808080", f"Gray color on: {text}"


class TestSpecialCharacters:
    """Test that XML-unsafe characters in values are handled."""

    def test_ampersand_in_value(self):
        info = get_template("deviation")
        values = {key: "" for key in info.placeholders}
        values["DEVIATION_DESCRIPTION"] = "R&D Department < Building > 5"
        result = fill_template(str(info.path), values)
        text = extract_text(result)
        assert "R&amp;D Department &lt; Building &gt; 5" in text or "R&D Department" in text

    def test_quotes_in_value(self):
        info = get_template("deviation")
        values = {key: "" for key in info.placeholders}
        values["ROOT_CAUSE"] = 'Said "hello" to O\'Brien'
        result = fill_template(str(info.path), values)
        # Just verify it produces valid XML output
        with zipfile.ZipFile(io.BytesIO(result), "r") as zf:
            tree = etree.fromstring(zf.read("word/document.xml"))
            assert tree is not None


class TestMergeRuns:
    """Test run merging logic with synthetic XML."""

    def test_merge_split_placeholder(self):
        """Simulate Word splitting {{PLACEHOLDER}} across two runs."""
        xml = f"""
        <w:body xmlns:w="{NS}">
            <w:p>
                <w:r>
                    <w:rPr><w:i/></w:rPr>
                    <w:t>{{{{PLACE</w:t>
                </w:r>
                <w:r>
                    <w:rPr><w:i/></w:rPr>
                    <w:t>HOLDER}}}}</w:t>
                </w:r>
            </w:p>
        </w:body>
        """
        tree = etree.fromstring(xml.encode())
        _merge_runs(tree)

        texts = [t.text for t in tree.iter(T) if t.text]
        merged = "".join(texts)
        assert "{{PLACEHOLDER}}" in merged

    def test_no_merge_different_formatting(self):
        """Runs with different formatting should NOT be merged."""
        xml = f"""
        <w:body xmlns:w="{NS}">
            <w:p>
                <w:r>
                    <w:rPr><w:b/></w:rPr>
                    <w:t>Bold</w:t>
                </w:r>
                <w:r>
                    <w:rPr><w:i/></w:rPr>
                    <w:t>Italic</w:t>
                </w:r>
            </w:p>
        </w:body>
        """
        tree = etree.fromstring(xml.encode())
        _merge_runs(tree)

        texts = [t.text for t in tree.iter(T) if t.text]
        assert "Bold" in texts
        assert "Italic" in texts
        assert len(texts) == 2

    def test_merge_preserves_non_text_children(self):
        """Merging mergeable runs must not drop <w:br/>, tabs, etc."""
        xml = f"""
        <w:body xmlns:w="{NS}">
            <w:p>
                <w:r>
                    <w:rPr><w:i/></w:rPr>
                    <w:t>line one</w:t>
                </w:r>
                <w:r>
                    <w:rPr><w:i/></w:rPr>
                    <w:br/>
                    <w:t>line two</w:t>
                </w:r>
            </w:p>
        </w:body>
        """
        tree = etree.fromstring(xml.encode())
        _merge_runs(tree)

        # The <w:br/> must survive the merge.
        assert tree.find(f".//{{{NS}}}br") is not None
        texts = [t.text for t in tree.iter(T) if t.text]
        assert "line one" in texts and "line two" in texts


class TestSecureParsing:
    """The hardened parser must neutralize untrusted-XML attacks."""

    def test_entity_bomb_not_expanded(self):
        """A 'billion laughs' entity bomb must not be expanded."""
        from app.engine.xml_utils import secure_fromstring

        bomb = b"""<?xml version="1.0"?>
        <!DOCTYPE lolz [
          <!ENTITY lol "lol">
          <!ENTITY lol1 "&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;">
          <!ENTITY lol2 "&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;">
        ]>
        <root>&lol2;</root>"""
        try:
            el = secure_fromstring(bomb)
            # If it parsed, entities must be unexpanded (no blow-up).
            assert "lol" not in (el.text or "")
        except etree.XMLSyntaxError:
            pass  # rejected outright is also acceptable

    def test_legit_xml_still_parses(self):
        """Normal WordprocessingML, including &amp;, parses fine."""
        from app.engine.xml_utils import secure_fromstring

        legit = (
            f'<w:document xmlns:w="{NS}"><w:body><w:p><w:r>'
            f"<w:t>A &amp; B {{{{NAME}}}}</w:t></w:r></w:p></w:body></w:document>"
        ).encode()
        tree = secure_fromstring(legit)
        txt = "".join(t.text for t in tree.iter(T) if t.text)
        assert "A & B" in txt and "{{NAME}}" in txt


class TestSplitParagraphs:
    """A filled value containing \\n becomes real paragraph breaks."""

    def _body(self, inner: str):
        return etree.fromstring(f'<w:body xmlns:w="{NS}">{inner}</w:body>'.encode())

    def test_multi_paragraph_clones_with_pPr_preserved(self):
        inner = (
            '<w:p><w:pPr><w:spacing w:after="120"/></w:pPr>'
            '<w:r><w:t>para1\npara2\npara3</w:t></w:r></w:p>'
        )
        tree = self._body(inner)
        _split_paragraphs(tree)
        paras = tree.findall(P)
        assert len(paras) == 3
        texts = ["".join(t.text or "" for t in p.iter(T)) for p in paras]
        assert texts == ["para1", "para2", "para3"]
        for p in paras:  # spacing pPr survives on every clone
            assert p.find(f"{{{NS}}}pPr") is not None

    def test_single_line_unchanged(self):
        tree = self._body('<w:p><w:r><w:t>just one line</w:t></w:r></w:p>')
        _split_paragraphs(tree)
        assert len(tree.findall(P)) == 1

    def test_trailing_and_double_newlines_no_blank_paras(self):
        tree = self._body('<w:p><w:r><w:t>a\n\nb\n</w:t></w:r></w:p>')
        _split_paragraphs(tree)
        texts = ["".join(t.text or "" for t in p.iter(T)) for p in tree.findall(P)]
        assert texts == ["a", "b"]

    def test_mixed_content_paragraph_not_cloned(self):
        inner = (
            '<w:p>'
            '<w:r><w:t xml:space="preserve">Doc </w:t></w:r>'
            '<w:r><w:t>X\nY</w:t></w:r>'
            '</w:p>'
        )
        tree = self._body(inner)
        _split_paragraphs(tree)
        assert len(tree.findall(P)) == 1  # not duplicated
        full = "".join(t.text or "" for t in tree.iter(T))
        assert "X Y" in full  # newline collapsed to space as fallback


class TestPruneEmptyRows:
    """Fully-blank table data rows are removed; header is kept."""

    def test_blank_data_row_removed_header_kept(self):
        xml = (
            f'<w:body xmlns:w="{NS}"><w:tbl>'
            '<w:tr><w:tc><w:p><w:r><w:t>Abbreviation</w:t></w:r></w:p></w:tc>'
            '<w:tc><w:p><w:r><w:t>Definition</w:t></w:r></w:p></w:tc></w:tr>'
            '<w:tr><w:tc><w:p><w:r><w:t>EDC</w:t></w:r></w:p></w:tc>'
            '<w:tc><w:p><w:r><w:t>Electronic Data Capture</w:t></w:r></w:p></w:tc></w:tr>'
            '<w:tr><w:tc><w:p><w:r><w:t></w:t></w:r></w:p></w:tc>'
            '<w:tc><w:p><w:r><w:t>   </w:t></w:r></w:p></w:tc></w:tr>'
            '</w:tbl></w:body>'
        )
        tree = etree.fromstring(xml.encode())
        _prune_empty_blocks(tree)
        rows = tree.find(TBL).findall(TR)
        assert len(rows) == 2
        assert "Abbreviation" in "".join(t.text or "" for t in rows[0].iter(T))
        assert "EDC" in "".join(t.text or "" for t in rows[1].iter(T))


class TestPruneEmptySections:
    """Blank numbered section blocks are removed; titled ones are kept."""

    def _heading(self, level: int, text: str) -> str:
        return (
            f'<w:p><w:pPr><w:pStyle w:val="Heading{level}"/>'
            f'<w:numPr><w:ilvl w:val="{level - 1}"/><w:numId w:val="2"/></w:numPr></w:pPr>'
            f'<w:r><w:t>{text}</w:t></w:r></w:p>'
        )

    def _content(self, text: str) -> str:
        return f'<w:p><w:r><w:t>{text}</w:t></w:r></w:p>'

    def _numbered_headings(self, tree):
        out = []
        for p in tree.iter(P):
            ppr = p.find(f"{{{NS}}}pPr")
            if ppr is not None and ppr.find(f"{{{NS}}}numPr") is not None:
                out.append(p)
        return out

    def test_empty_section_removed_filled_kept(self):
        xml = (
            f'<w:body xmlns:w="{NS}">'
            + self._heading(1, "Purpose") + self._content("Why we exist.")
            + self._heading(1, "") + self._content("")
            + '</w:body>'
        )
        tree = etree.fromstring(xml.encode())
        _prune_empty_blocks(tree)
        assert len(self._numbered_headings(tree)) == 1
        full = "".join(t.text or "" for t in tree.iter(T))
        assert "Purpose" in full and "Why we exist." in full

    def test_titled_section_without_content_kept(self):
        xml = (
            f'<w:body xmlns:w="{NS}">'
            + self._heading(1, "Scope") + self._content("")
            + '</w:body>'
        )
        tree = etree.fromstring(xml.encode())
        _prune_empty_blocks(tree)
        assert "Scope" in "".join(t.text or "" for t in tree.iter(T))


class TestFillTemplateGeneral:
    """End-to-end fill of the real General Document template (Phase 1)."""

    def test_partial_general_splits_and_prunes(self):
        from app.engine.docx_engine import _is_numbered_heading, _para_text
        from app.engine.xml_utils import secure_fromstring

        info = get_template("general")
        values = {k: "" for k in info.placeholders}
        values.update({
            "ORGANIZATION_NAME": "Acme",
            "DOCUMENT_TITLE": "Data Plan",
            "SECTION_1_TITLE": "Purpose",
            "SECTION_1_CONTENT": "First paragraph.\nSecond paragraph.",
            "ABBREV_1": "EDC", "ABBREV_1_DEF": "Electronic Data Capture",
            "REF_1_ID": "SOP-1", "REF_1_TITLE": "Master SOP",
            "REV_1_VERSION": "1.0", "REV_1_DATE": "2026",
            "REV_1_AUTHOR": "A", "REV_1_DESCRIPTION": "Initial",
        })
        out = fill_template(str(info.path), values)

        zf = zipfile.ZipFile(io.BytesIO(out))
        assert zf.testzip() is None
        doc = secure_fromstring(zf.read("word/document.xml"))
        full = "".join(t.text or "" for t in doc.iter(T))

        # multi-paragraph content rendered as separate paragraphs
        assert "First paragraph." in full and "Second paragraph." in full
        # nothing left unfilled
        assert "{{" not in full
        # no blank numbered section heading survived
        assert [p for p in doc.iter(P)
                if _is_numbered_heading(p) and not _para_text(p).strip()] == []
        # no fully-blank data row survived in any table
        for tbl in doc.iter(TBL):
            for row in tbl.findall(TR)[1:]:
                assert any((t.text or "").strip() for t in row.iter(T))
