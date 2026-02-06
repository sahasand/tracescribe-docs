"""Tests for the core .docx template fill engine."""

import io
import re
import zipfile

import pytest
from lxml import etree

from app.engine.docx_engine import fill_template, _merge_runs, _fill_placeholders, PLACEHOLDER_RE
from app.engine.xml_utils import T, R, RPR, I, ICS, COLOR, NS, escape_xml
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
