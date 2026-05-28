# CLAUDE.md — TraceScribe Document Formatter

## What
Web app. User uploads a messy document (.docx, .pdf, .txt), picks a template type, AI extracts the content into structured fields, engine fills a clean formatted .docx template. Stateless — nothing stored, nothing persists.

## Current State
**Deployed and live.**

- Backend: 62 tests passing (engine, extraction, API)
- Frontend: Next.js builds clean, all components working
- 6 templates with 288 total placeholders
- **Live frontend:** https://docs.tracescribe.com (custom domain on tracescribe.com)
- **Live backend:** https://tracescribe-docs-production.up.railway.app
- **GitHub:** https://github.com/sahasand/tracescribe-docs

## Stack
- **Backend:** Python 3.13, FastAPI, lxml, uvicorn — deploy on **Railway**
- **Frontend:** Next.js 16 App Router, React 19, TypeScript, Tailwind 3.4.x, Lucide — deploy on **Vercel**
- **AI:** Claude API (default `claude-opus-4-8`, override via `ANTHROPIC_MODEL` env var) for content extraction
- **No database. No file storage. No auth.** Process in memory, return result, discard.

### Stack gotchas
- **CORS:** `FRONTEND_URL` is a **comma-separated** allowlist of frontend origins (prod: both `https://docs.tracescribe.com` and `https://tracescribe-docs.vercel.app`). Each must match exactly (incl. port). Locally the frontend runs on **3001**, so set `FRONTEND_URL=http://localhost:3001` in `backend/.env`.
- **Lint:** ESLint uses flat config (`frontend/eslint.config.mjs`); `next lint` was removed in Next 16 — run `npx eslint .`.
- **Tailwind is intentionally pinned to 3.4.x.** v4 is deferred — it silently renames utilities the app uses (`shadow-sm`, `outline-none`) and needs visual QA before adopting.

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
  tests/                # 62 tests (engine, extraction, API)
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
A .docx is a ZIP of XML files. The core engine unpacks the ZIP, finds `{{PLACEHOLDER}}` markers in `<w:t>` XML elements, replaces text, repacks. All original formatting (styles, images, headers, footers, tables, fonts) is preserved.

Per content part, the pipeline order is: `_expand_general` (general only — clone repeatable blocks) → `_merge_runs` → `_fill_placeholders` → `_split_paragraphs` (newlines → paragraphs) → `_prune_empty_blocks` (drop empty rows/sections) → serialize → `_repack` → `_validate`.

### Critical Rules
1. Never recreate a .docx from scratch. Always unpack → edit XML → repack.
2. Only modify `<w:t>` text elements. Never touch formatting XML.
3. Word splits placeholders across multiple `<w:r>` runs — merge adjacent runs with identical `<w:rPr>` before scanning. **Never merge runs containing a Word field (`<w:fldChar>`/`<w:instrText>`)** — doing so scrambles PAGE/NUMPAGES and breaks header/footer page numbers (`_run_has_field` guards this).
4. Remove italic/gray (#808080) formatting from filled runs. Preserve bold.
5. Escape XML entities in fill values: `& < > " '`
6. Preserve newlines: a `\n` in a value becomes a real paragraph break — `_split_paragraphs` clones the enclosing `<w:p>` (keeps style/numbering). Mixed-content paragraphs fall back to spaces.
7. Process both `document.xml` AND `header1.xml`/`footer1.xml` for placeholders and fields.
8. Use `re.sub` for replacement — headers have multiple placeholders per `<w:t>`.
9. After filling, `_prune_empty_blocks` removes blank table data rows (header kept) and blank numbered section/subsection blocks. Word auto-numbers (`<w:numPr>`) the survivors on open.
10. Validate output: ZIP valid, XML well-formed, no unfilled `{{}}` remaining.
11. Parse all XML (esp. uploaded `.docx`) via `xml_utils.secure_fromstring` — entity expansion off (blocks billion-laughs/XXE). Never call `etree.fromstring` directly on untrusted bytes.
12. **General Document is variable-length** (`TemplateInfo.structured=True`): extraction returns lists, and `_expand_general` clones the template's prototype table rows (abbrev/ref/revision) and section/subsection/sub-subsection blocks per item. Other 5 templates use the flat placeholder path.

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
| **General Document** | structured | Cover page, signatures, **variable-length** revision history, abbreviations, references, and numbered sections (with subsections 1.1 / sub-subsections 1.1.1) — any count, via block cloning. References, appendices |

## AI Extraction
For each template type, send the uploaded document text to Claude with a prompt that:
- Describes the template structure so Claude maps content logically
- Asks Claude to return JSON, inferring/summarizing where the source is incomplete and using `""` for fields with no matching content
- Flat templates: a JSON object of placeholder keys → values.
- General Document: a **structured** JSON object — 15 scalar keys plus `revisions`/`abbreviations`/`references`/`sections` lists ("as many as the source has"), sections nested 3 levels. `ai_extractor._normalize_general` defensively coerces the shape.

One API call per document. Model: default `claude-opus-4-8`, configurable via `ANTHROPIC_MODEL`. `max_tokens` is per-template (`TemplateInfo.max_tokens`; general = 16384, others 8192); a truncation guard raises a clear error when `stop_reason == "max_tokens"`. The route offloads `extract_text`/`fill_template` to a threadpool (`run_in_threadpool`) so blocking work doesn't stall the event loop. There is no review/edit step — one shot: upload → process → download (the intelligence is in the processing).

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
- **Railway project:** `tracescribe-docs` → service `tracescribe-docs` (production env). ⚠️ A *separate, unrelated* Railway project `tracescribe-backend` (a Clerk/OpenAI/Postgres app) also exists in this account — **don't confuse them**; this app's backend is the `tracescribe-docs` project only.
- **Repo:** `sahasand/tracescribe-docs` (root directory: `backend`)
- **Builder:** Dockerfile (auto-detected)
- **Port:** 8000
- Auto-deploys on push to `main`. `FRONTEND_URL` is set to both prod origins (comma-separated).

### Frontend → Vercel
- **URL:** https://docs.tracescribe.com (custom domain on tracescribe.com)
- **Repo:** `sahasand/tracescribe-docs` (root directory: `frontend`)
- **Framework:** Next.js (auto-detected)
- Connected to GitHub — auto-deploys on push to `main`

### Env Vars
```
# Railway (backend)
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-opus-4-8   # optional; defaults to claude-opus-4-8
FRONTEND_URL=https://docs.tracescribe.com,https://tracescribe-docs.vercel.app   # comma-separated CORS allowlist

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
pytest tests/ -v   # 62 tests, ~1s
```
