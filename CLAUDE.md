# CLAUDE.md — TraceScribe Document Formatter

## What
Web app. User uploads a messy document (.docx, .pdf, .txt), picks a template type, AI extracts the content into structured fields, engine fills a clean formatted .docx template. Stateless — nothing stored, nothing persists.

## Current State
**Deployed and live.**

- Backend: 46 tests passing (engine, extraction, API)
- Frontend: Next.js builds clean, all components working
- 6 templates with 288 total placeholders
- **Live:** https://docs.tracescribe.com
- **Backend:** https://tracescribe-docs-production.up.railway.app
- **GitHub:** https://github.com/sahasand/tracescribe-docs

## Stack
- **Backend:** Python 3.13, FastAPI, lxml, uvicorn — deploy on **Railway**
- **Frontend:** Next.js 14 App Router, TypeScript, Tailwind, Lucide — deploy on **Vercel**
- **AI:** Claude API (claude-sonnet-4-20250514) for content extraction
- **No database. No file storage. No auth.** Process in memory, return result, discard.

## Project Structure
```
backend/
  templates/           # 6 .docx template files
  app/
    main.py            # FastAPI app, CORS, health check
    config.py          # pydantic-settings (env vars from .env)
    api/
      routes.py        # POST /api/format, GET /api/templates
    engine/
      xml_utils.py     # Namespace helpers, XML entity escaping
      docx_engine.py   # Core: unpack, merge runs, fill, repack, validate
    extraction/
      text_extractor.py   # .docx/.pdf/.txt → plain text
      ai_extractor.py     # Claude API call → JSON
      prompts.py          # Template-specific prompt definitions
    models/
      schemas.py          # Pydantic response models
      template_registry.py  # Template type → file path + placeholder keys
  tests/                # 46 tests (engine, extraction, API)
  requirements.txt
  Dockerfile
  .env                  # Local only, gitignored

frontend/
  src/
    app/
      layout.tsx        # Root layout, Plus Jakarta Sans + JetBrains Mono
      page.tsx          # Single page: Select → Upload → Result
    components/
      TemplateGrid.tsx, TemplateCard.tsx, UploadZone.tsx,
      ResultPanel.tsx, StepIndicator.tsx, FilePreview.tsx
    hooks/
      useFormatDocument.ts  # State machine hook
    lib/
      api.ts, templates.ts, types.ts
  .env.local.example
```

## The Engine
A .docx is a ZIP of XML files. The core engine unpacks the ZIP, finds `{{PLACEHOLDER}}` markers in `<w:t>` XML elements, replaces text, repacks. All original formatting (styles, images, headers, footers, tables, fonts) is preserved perfectly. Output is byte-identical to template except filled placeholders.

### Critical Rules
1. Never recreate a .docx from scratch. Always unpack → edit XML → repack.
2. Only modify `<w:t>` text elements. Never touch formatting XML.
3. Word splits placeholders across multiple `<w:r>` runs — merge adjacent runs with identical `<w:rPr>` before scanning.
4. Remove italic/gray (#808080) formatting from filled runs. Preserve bold.
5. Escape XML entities in fill values: `& < > " '`
6. Replace newlines in values with spaces (v1 decision).
7. Process both `document.xml` AND `header1.xml` for placeholders.
8. Use `re.sub` for replacement — headers have multiple placeholders per `<w:t>`.
9. Validate output: ZIP valid, XML well-formed, no unfilled `{{}}` remaining.

### XML Namespace
```python
NS = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
def tag(name): return f'{{{NS}}}{name}'
```

## API
```
GET  /api/templates    → list of template types with metadata
POST /api/format       → multipart form (file + template_type) → .docx binary
GET  /health           → {"status": "ok"}
```

The format endpoint:
1. Validates template_type and file extension (.docx, .pdf, .txt)
2. Enforces 10 MB file size limit
3. Extracts text from uploaded file
4. Sends text to Claude with template-specific prompt → gets JSON
5. Fills the template .docx with returned JSON
6. Returns the completed .docx with Content-Disposition header
7. Discards everything

## Templates
Ship as .docx files bundled with the backend. Each has `{{PLACEHOLDER}}` markers in italic gray text. 6 templates:

| Template | Placeholders | Key Sections |
|----------|-------------|--------------|
| **SOP** | 54 | Title block, approval, revision history, purpose, scope, references, definitions, roles, 5 procedure steps, documentation, training |
| **Deviation Report** | 26 | Identification, description, root cause, impact (safety + data), CAPA, resolution/closure, approval |
| **CAPA Report** | 39 | Identification, problem statement, root cause investigation, corrective/preventive actions tables, effectiveness verification, closure |
| **Training Record** | 35 | Training details, content/objectives, 5-row attendance log, assessment, trainer sign-off |
| **Monitoring Visit** | 59 | Visit info, study status metrics, 6 monitoring activity subsections, findings by severity, action items, assessment, next visit |
| **General Document** | 75 | Cover page, signature/approval page, revision history (3 rows), TOC, abbreviations (5 rows), 5 numbered sections with sub-sections (1.1, 1.1.1), references, appendices |

## AI Extraction
For each template type, send the uploaded document text to Claude with a prompt that:
- Lists all placeholder keys for that template
- Describes the template structure so Claude maps content logically
- Asks Claude to return JSON mapping keys to extracted values
- Instructs Claude to infer/summarize where the source doc is incomplete
- Returns empty string for fields with no matching content

One API call per document. Model: claude-sonnet-4-20250514.

## Frontend
Single page app. Three states:

1. **Select** — Grid of 6 template cards with icons. User picks one.
2. **Upload** — Drag-and-drop zone. User drops their messy doc. File preview shown.
3. **Result** — Loading spinner while AI processes (~15-30s), then download button. Error state with retry.

No navigation, no sidebar, no login. One page, one flow.

## Design System
- **Font:** Plus Jakarta Sans (body + headings), JetBrains Mono (code/technical)
- **Colors:** Teal `#0D9488` primary, Coral `#F97316` accent, warm off-white `hsl(30, 20%, 98%)`
- **Radius:** 10px base, `rounded-2xl` cards
- **Icons:** Lucide React
- **Cards:** soft shadow, hover lift, hover border-teal
- **Buttons:** `rounded-md`, teal primary

## Deployment

### Backend → Railway
- **URL:** https://tracescribe-docs-production.up.railway.app
- **Repo:** `sahasand/tracescribe-docs` (root directory: `backend`)
- **Builder:** Dockerfile (auto-detected)
- **Port:** 8000
- Auto-deploys on push to `main`

### Frontend → Vercel
- **URL:** https://docs.tracescribe.com (custom domain on tracescribe.com)
- **Repo:** `sahasand/tracescribe-docs` (root directory: `frontend`)
- **Framework:** Next.js (auto-detected)
- Connected to GitHub — auto-deploys on push to `main`

### Env Vars
```
# Railway (backend)
ANTHROPIC_API_KEY=sk-ant-...
FRONTEND_URL=https://docs.tracescribe.com

# Vercel (frontend)
NEXT_PUBLIC_API_URL=https://tracescribe-docs-production.up.railway.app
```

### Custom Domain
- Optional: add via Vercel project settings → Domains

## Running Locally
```bash
# Backend
cd backend
pip install -r requirements.txt
cp .env.example .env  # add your ANTHROPIC_API_KEY
uvicorn app.main:app --port 8000

# Frontend
cd frontend
npm install
cp .env.local.example .env.local
npm run dev -- --port 3001
```

## Testing
```bash
cd backend
pytest tests/ -v   # 46 tests, ~1s
```
