"""
Template-specific prompts for AI content extraction.

Each prompt instructs Claude to extract structured data from a messy document
and return JSON mapping placeholder keys to extracted values.
"""

SYSTEM_PROMPT = """You are a document formatting assistant for clinical research organizations.
You extract structured content from messy, unformatted documents and return clean JSON
that maps to specific template placeholder fields.

Rules:
- Extract only what is present or clearly implied in the source document.
- For fields with no matching content, return an empty string "".
- Summarize or infer where the source document is incomplete but context exists.
- Never fabricate data — especially dates, names, or IDs.
- Keep values concise and professional.
- Return ONLY valid JSON. No markdown, no explanation, no code fences."""


def build_extraction_prompt(template_type: str, placeholders: list[str], document_text: str) -> str:
    """Build the user prompt for a given template type."""
    prompt_fn = _TEMPLATE_PROMPTS.get(template_type)
    if prompt_fn is None:
        return _generic_prompt(placeholders, document_text)
    return prompt_fn(placeholders, document_text)


def _sop_prompt(placeholders: list[str], text: str) -> str:
    return f"""Extract content from this document to fill a Standard Operating Procedure (SOP) template.

The SOP template has these sections:
- Title block: organization name, SOP title, document ID, revision, effective date, department
- Document approval: author, reviewer, approver names and dates
- Revision history: up to 2 revision entries (number, date, author, description)
- Purpose: why the SOP exists
- Scope: what the SOP covers
- References: up to 3 referenced documents (ID and title)
- Definitions: up to 3 terms with definitions
- Roles and responsibilities: up to 3 roles with their responsibilities
- Procedure: 5 procedure steps (each with a title and detailed description)
- Documentation requirements, training requirements, attachments

Return a JSON object with these exact keys (use "" for fields with no matching content):
{_format_keys(placeholders)}

SOURCE DOCUMENT:
{text}"""


def _deviation_prompt(placeholders: list[str], text: str) -> str:
    return f"""Extract content from this document to fill a Clinical Trial Deviation Report template.

The template has these sections:
- Identification: deviation ID, date identified, identified by, study/protocol, site, category, severity
- Description: detailed deviation description and requirement violated
- Root cause analysis
- Impact assessment: impact on subject safety and data integrity
- Corrective and preventive actions with due date and responsible person
- Resolution/closure: summary, date resolved, closed by
- Notifications: IRB and sponsor notification status
- Approval: PI and QA manager names and dates

Return a JSON object with these exact keys (use "" for fields with no matching content):
{_format_keys(placeholders)}

SOURCE DOCUMENT:
{text}"""


def _capa_prompt(placeholders: list[str], text: str) -> str:
    return f"""Extract content from this document to fill a CAPA (Corrective and Preventive Action) Report template.

The template has these sections:
- Identification: CAPA ID, date, initiator, type, priority, related deviations, study/system
- Problem statement: detailed description of the problem
- Root cause investigation: method, lead, findings, contributing factors
- Corrective actions: up to 3 actions with responsible person and due date
- Preventive actions: up to 2 actions with responsible person and due date
- Effectiveness verification: method, date, verified by, assessment
- Closure: CAPA status, date closed, closed by
- Approval: QA manager and department head names and dates

Return a JSON object with these exact keys (use "" for fields with no matching content):
{_format_keys(placeholders)}

SOURCE DOCUMENT:
{text}"""


def _training_prompt(placeholders: list[str], text: str) -> str:
    return f"""Extract content from this document to fill a Training Record template.

The template has these sections:
- Training details: record ID, title, type, related SOP, date, method, duration, trainer
- Content: topics covered, learning objectives
- Trainee attendance: up to 5 trainees (name, title, department, date for each)
- Assessment: method, passing criteria, notes
- Trainer sign-off: trainer name and date

Return a JSON object with these exact keys (use "" for fields with no matching content):
{_format_keys(placeholders)}

SOURCE DOCUMENT:
{text}"""


def _monitoring_prompt(placeholders: list[str], text: str) -> str:
    return f"""Extract content from this document to fill a Clinical Trial Monitoring Visit Report template.

The template has these sections:
- Visit information: sponsor, report ID, study/protocol, site details, PI, visit type/dates, monitors, site personnel
- Study status: subjects screened/enrolled/active/completed/withdrawn, screen failures, SAEs, protocol deviations
- Monitoring activities: ICF review, source document verification (CRFs, queries, SDV), IP accountability, safety, regulatory/essential docs, lab findings
- Findings by severity: critical, major, minor
- Action items: up to 5 items with owner, due date, status
- Previous action items status
- Overall site assessment
- Next visit: date, type, focus areas
- Sign-off: monitor and lead CRA names and dates

Return a JSON object with these exact keys (use "" for fields with no matching content):
{_format_keys(placeholders)}

SOURCE DOCUMENT:
{text}"""


def _general_prompt(placeholders: list[str], text: str) -> str:
    return f"""Extract content from this document to fill a General Document template.

This is a flexible, multi-section document template with:
- Cover page: organization name, document title, subtitle, document ID, version, effective date, author, department, status
- Signature page: author/reviewer/approver with dates
- Revision history: up to 3 revision entries (version, date, author, description)
- Abbreviations table: up to 5 abbreviations with definitions
- 5 numbered sections, each with:
  - A section title and content
  - Two sub-sections (e.g., 1.1, 1.2) each with title and content
  - Section 1 also has a third-level sub-section (1.1.1)
- References: up to 3 referenced documents (ID and title)
- Appendices

Map the source document's content to the numbered sections logically. If the source has fewer than 5 major sections, leave extra sections empty.

Return a JSON object with these exact keys (use "" for fields with no matching content):
{_format_keys(placeholders)}

SOURCE DOCUMENT:
{text}"""


def _generic_prompt(placeholders: list[str], text: str) -> str:
    return f"""Extract content from this document to fill a template with specific placeholder fields.

Return a JSON object with these exact keys (use "" for fields with no matching content):
{_format_keys(placeholders)}

SOURCE DOCUMENT:
{text}"""


def _format_keys(keys: list[str]) -> str:
    return "\n".join(f'  "{k}": ""' for k in keys)


_TEMPLATE_PROMPTS = {
    "sop": _sop_prompt,
    "deviation": _deviation_prompt,
    "capa": _capa_prompt,
    "training": _training_prompt,
    "monitoring": _monitoring_prompt,
    "general": _general_prompt,
}
