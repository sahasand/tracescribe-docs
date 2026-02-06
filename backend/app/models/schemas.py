"""Pydantic models for API request/response validation."""

from pydantic import BaseModel


class TemplateInfoResponse(BaseModel):
    type: str
    display_name: str
    description: str
    placeholder_count: int


class ErrorResponse(BaseModel):
    detail: str
