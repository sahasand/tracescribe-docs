"""API routes for the document formatter."""

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import Response

from app.engine.docx_engine import fill_template
from app.extraction.text_extractor import extract_text
from app.extraction.ai_extractor import extract_fields
from app.models.template_registry import TEMPLATES, get_template
from app.models.schemas import TemplateInfoResponse

router = APIRouter()

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_EXTENSIONS = {"docx", "pdf", "txt"}


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


@router.post("/format")
async def format_document(
    file: UploadFile = File(...),
    template_type: str = Form(...),
):
    """
    Upload a document and get back a formatted .docx.

    1. Validates template_type and file extension
    2. Extracts text from uploaded file
    3. Sends to Claude for structured extraction
    4. Fills template and returns completed .docx
    """
    # Validate template type
    try:
        template_info = get_template(template_type)
    except KeyError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Validate file extension
    filename = file.filename or "upload"
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: .{ext}. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    # Read file with size limit
    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Maximum size: 10 MB.")

    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # Extract text
    try:
        document_text = extract_text(file_bytes, filename)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to extract text: {e}")

    if not document_text.strip():
        raise HTTPException(status_code=400, detail="No text content found in uploaded file.")

    # AI extraction
    try:
        values = await extract_fields(template_type, document_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI extraction failed: {e}")

    # Fill template
    try:
        output_bytes = fill_template(str(template_info.path), values)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Template fill failed: {e}")

    # Return .docx
    output_filename = f"{template_type}_formatted.docx"
    return Response(
        content=output_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{output_filename}"'},
    )
