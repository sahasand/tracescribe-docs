"""Pydantic models for API request/response validation."""

from typing import Any

from pydantic import BaseModel


class TemplateInfoResponse(BaseModel):
    type: str
    display_name: str
    description: str
    placeholder_count: int


class ErrorResponse(BaseModel):
    detail: str


class ExtractResponse(BaseModel):
    """Extracted fields for review. Flat dict[str,str] for most templates;
    the General Document includes variable-length lists (so values are Any)."""
    template_type: str
    fields: dict[str, Any]


class FillRequest(BaseModel):
    """Reviewed/edited fields to fill into a template."""
    template_type: str
    fields: dict[str, Any]
