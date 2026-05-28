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

    client = anthropic.AsyncAnthropic(
        api_key=settings.anthropic_api_key,
        timeout=120.0,
    )

    message = await client.messages.create(
        model=settings.anthropic_model,
        max_tokens=template_info.max_tokens,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    # If the model ran out of output budget the JSON is truncated; fail with a
    # clear message instead of a confusing JSONDecodeError downstream.
    if message.stop_reason == "max_tokens":
        raise ValueError(
            "AI response was truncated (hit the output token limit). "
            "The source document may be too long for this template."
        )

    # Extract text from response (guard against non-text leading blocks)
    response_text = next(
        (block.text for block in message.content if block.type == "text"), ""
    ).strip()
    if not response_text:
        raise ValueError("AI returned no text content")

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
