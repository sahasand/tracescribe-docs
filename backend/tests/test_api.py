"""Tests for FastAPI endpoints (mocking the AI layer)."""

import io
import json
import zipfile
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.models.template_registry import get_template


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


def _mock_extract_fields(template_type: str):
    """Create a mock that returns placeholder values for the given template."""
    info = get_template(template_type)
    values = {key: f"Test {key.lower()}" for key in info.placeholders}

    async def mock_fn(t_type, doc_text):
        return values
    return mock_fn


@pytest.mark.anyio
async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


@pytest.mark.anyio
async def test_list_templates(client):
    resp = await client.get("/api/templates")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 6
    types = {t["type"] for t in data}
    assert types == {"sop", "deviation", "capa", "training", "monitoring", "general"}


@pytest.mark.anyio
@patch("app.api.routes.extract_fields")
async def test_format_sop(mock_extract, client):
    mock_extract.side_effect = _mock_extract_fields("sop")

    content = b"This is a test SOP document about lab procedures."
    files = {"file": ("test.txt", io.BytesIO(content), "text/plain")}
    data = {"template_type": "sop"}

    resp = await client.post("/api/format", files=files, data=data)
    assert resp.status_code == 200
    assert "application/vnd.openxmlformats" in resp.headers["content-type"]
    assert 'filename="sop_formatted.docx"' in resp.headers["content-disposition"]

    # Verify output is valid ZIP
    with zipfile.ZipFile(io.BytesIO(resp.content), "r") as zf:
        assert zf.testzip() is None


@pytest.mark.anyio
async def test_invalid_template_type(client):
    content = b"Some text"
    files = {"file": ("test.txt", io.BytesIO(content), "text/plain")}
    data = {"template_type": "invalid"}

    resp = await client.post("/api/format", files=files, data=data)
    assert resp.status_code == 400
    assert "Unknown template type" in resp.json()["detail"]


@pytest.mark.anyio
async def test_unsupported_file_type(client):
    content = b"Some data"
    files = {"file": ("test.xlsx", io.BytesIO(content), "application/octet-stream")}
    data = {"template_type": "sop"}

    resp = await client.post("/api/format", files=files, data=data)
    assert resp.status_code == 400
    assert "Unsupported file type" in resp.json()["detail"]


@pytest.mark.anyio
async def test_empty_file(client):
    files = {"file": ("test.txt", io.BytesIO(b""), "text/plain")}
    data = {"template_type": "sop"}

    resp = await client.post("/api/format", files=files, data=data)
    assert resp.status_code == 400


@pytest.mark.anyio
@patch("app.api.routes.extract_fields")
async def test_format_all_template_types(mock_extract, client):
    """Smoke test: format endpoint works for every template type."""
    for template_type in ["sop", "deviation", "capa", "training", "monitoring", "general"]:
        mock_extract.side_effect = _mock_extract_fields(template_type)

        content = f"Test document for {template_type}".encode()
        files = {"file": (f"test_{template_type}.txt", io.BytesIO(content), "text/plain")}
        data = {"template_type": template_type}

        resp = await client.post("/api/format", files=files, data=data)
        assert resp.status_code == 200, f"Failed for {template_type}: {resp.text}"
