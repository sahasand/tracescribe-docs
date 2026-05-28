"""API routes for the document formatter."""

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import Response

from app.engine.docx_engine import fill_template
from app.extraction.text_extractor import extract_text
from app.extraction.ai_extractor import extract_fields
from app.models.template_registry import TEMPLATES, TemplateInfo, get_template
from app.models.schemas import ExtractResponse, FillRequest, TemplateInfoResponse

router = APIRouter()

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_EXTENSIONS = {"docx", "pdf", "txt"}

DOCX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def _require_template(template_type: str) -> TemplateInfo:
    try:
        return get_template(template_type)
    except KeyError as e:
        raise HTTPException(status_code=400, detail=str(e))


async def _read_upload(file: UploadFile) -> bytes:
    """Validate extension + size and return the uploaded bytes (capped)."""
    filename = file.filename or "upload"
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: .{ext}. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )
    # Read at most one byte past the limit so an oversized upload is rejected
    # without buffering the entire (potentially huge) file into memory.
    file_bytes = await file.read(MAX_FILE_SIZE + 1)
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Maximum size: 10 MB.")
    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    return file_bytes


async def _extract(template_type: str, file: UploadFile) -> dict[str, str]:
    """Shared upload → text → AI-extraction step."""
    _require_template(template_type)
    file_bytes = await _read_upload(file)
    filename = file.filename or "upload"

    try:
        document_text = await run_in_threadpool(extract_text, file_bytes, filename)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to extract text: {e}")
    if not document_text.strip():
        raise HTTPException(status_code=400, detail="No text content found in uploaded file.")

    try:
        return await extract_fields(template_type, document_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI extraction failed: {e}")


async def _fill(template_info: TemplateInfo, fields: dict[str, str]) -> bytes:
    """Shared fill step. Every placeholder is filled (missing → '')."""
    values = {k: "" for k in template_info.placeholders}
    for key, value in fields.items():
        if key in values:  # whitelist to the template's own placeholders
            values[key] = str(value) if value is not None else ""
    try:
        return await run_in_threadpool(fill_template, str(template_info.path), values)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Template fill failed: {e}")


def _docx_response(template_type: str, output_bytes: bytes) -> Response:
    return Response(
        content=output_bytes,
        media_type=DOCX_MEDIA_TYPE,
        headers={"Content-Disposition": f'attachment; filename="{template_type}_formatted.docx"'},
    )


@router.get("/templates", response_model=list[TemplateInfoResponse])
async def list_templates():
    """Return available template types."""
    return [
        TemplateInfoResponse(
            type=key,
            display_name=info.display_name,
            description=info.description,
            placeholder_count=len(info.placeholders),
        )
        for key, info in TEMPLATES.items()
    ]


@router.post("/extract", response_model=ExtractResponse)
async def extract_document(
    file: UploadFile = File(...),
    template_type: str = Form(...),
):
    """Extract structured fields from an upload for the user to review/edit."""
    fields = await _extract(template_type, file)
    return ExtractResponse(template_type=template_type, fields=fields)


@router.post("/fill")
async def fill_document(req: FillRequest):
    """Fill a template from reviewed fields and return the completed .docx."""
    template_info = _require_template(req.template_type)
    output_bytes = await _fill(template_info, req.fields)
    return _docx_response(req.template_type, output_bytes)


@router.post("/format")
async def format_document(
    file: UploadFile = File(...),
    template_type: str = Form(...),
):
    """One-shot: upload → extract → fill → .docx (kept for backward compatibility)."""
    template_info = _require_template(template_type)
    fields = await _extract(template_type, file)
    output_bytes = await _fill(template_info, fields)
    return _docx_response(template_type, output_bytes)
