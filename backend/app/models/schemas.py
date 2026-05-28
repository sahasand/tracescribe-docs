"""Pydantic models for API request/response validation."""

from pydantic import BaseModel


class TemplateInfoResponse(BaseModel):
    type: str
    display_name: str
    description: str
    placeholder_count: int


class ErrorResponse(BaseModel):
    detail: str


class ExtractResponse(BaseModel):
    """Structured fields extracted from an uploaded document, for review."""
    template_type: str
    fields: dict[str, str]


class FillRequest(BaseModel):
    """Reviewed/edited fields to fill into a template."""
    template_type: str
    fields: dict[str, str]
