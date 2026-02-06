"""Tests for text extraction (non-AI components)."""

import pytest

from app.extraction.text_extractor import extract_text
from app.extraction.prompts import build_extraction_prompt, SYSTEM_PROMPT
from app.models.template_registry import TEMPLATES, get_template


class TestTextExtractorTxt:
    def test_utf8(self):
        text = "Hello, world!".encode("utf-8")
        assert extract_text(text, "test.txt") == "Hello, world!"

    def test_latin1(self):
        text = "Résumé café".encode("latin-1")
        result = extract_text(text, "doc.txt")
        assert "caf" in result

    def test_empty(self):
        assert extract_text(b"", "empty.txt") == ""


class TestTextExtractorDocx:
    def test_extract_from_template(self):
        """Extract text from actual SOP template .docx."""
        info = get_template("sop")
        with open(info.path, "rb") as f:
            text = extract_text(f.read(), "SOP_Template.docx")
        assert "Standard Operating Procedure" in text
        assert "{{PURPOSE}}" in text

    def test_invalid_docx(self):
        with pytest.raises(Exception):
            extract_text(b"not a zip", "bad.docx")


class TestTextExtractorUnsupported:
    def test_unsupported_extension(self):
        with pytest.raises(ValueError, match="Unsupported file type"):
            extract_text(b"data", "file.xyz")


class TestPrompts:
    @pytest.mark.parametrize("template_type", list(TEMPLATES.keys()))
    def test_prompt_contains_all_keys(self, template_type):
        info = get_template(template_type)
        prompt = build_extraction_prompt(template_type, info.placeholders, "Sample text")
        for key in info.placeholders:
            assert key in prompt, f"Key {key} missing from {template_type} prompt"

    def test_system_prompt_exists(self):
        assert len(SYSTEM_PROMPT) > 50
        assert "JSON" in SYSTEM_PROMPT
