"""
AI content extractor using Claude API.

Sends document text to Claude with a template-specific prompt,
parses the JSON response, and returns a dict of placeholder values.
"""

import json

import anthropic

from app.config import settings
from app.models.template_registry import get_template
from .prompts import SYSTEM_PROMPT, build_extraction_prompt


async def extract_fields(template_type: str, document_text: str) -> dict[str, str]:
    """
    Use Claude to extract structured fields from document text.

    Args:
        template_type: One of the registered template types (sop, deviation, etc.)
        document_text: Plain text content of the uploaded document.

    Returns:
        Dict mapping placeholder keys to extracted values.
    """
    template_info = get_template(template_type)

    prompt = build_extraction_prompt(
        template_type=template_type,
        placeholders=template_info.placeholders,
        document_text=document_text,
    )

    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    message = await client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    # Extract text from response
    response_text = message.content[0].text.strip()

    # Strip markdown code fences if present
    if response_text.startswith("```"):
        lines = response_text.split("\n")
        # Remove first and last lines (```json and ```)
        lines = [l for l in lines if not l.strip().startswith("```")]
        response_text = "\n".join(lines)

    # Parse JSON
    try:
        extracted = json.loads(response_text)
    except json.JSONDecodeError as e:
        raise ValueError(f"AI returned invalid JSON: {e}\nResponse: {response_text[:500]}")

    # Ensure all expected keys exist, fill missing with ""
    result = {}
    for key in template_info.placeholders:
        val = extracted.get(key, "")
        result[key] = str(val) if val is not None else ""

    return result
