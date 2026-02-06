"""
Template registry: maps template types to file paths and placeholder keys.
"""

from pathlib import Path
from dataclasses import dataclass

TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent / "templates"


@dataclass(frozen=True)
class TemplateInfo:
    file_name: str
    display_name: str
    description: str
    placeholders: list[str]

    @property
    def path(self) -> Path:
        return TEMPLATES_DIR / self.file_name


TEMPLATES: dict[str, TemplateInfo] = {
    "sop": TemplateInfo(
        file_name="SOP_Template.docx",
        display_name="Standard Operating Procedure",
        description="Purpose, Scope, References, Definitions, Roles, Procedure steps, Documentation, Training, Attachments",
        placeholders=[
            "ORGANIZATION_NAME", "SOP_TITLE", "DOCUMENT_ID", "REVISION",
            "EFFECTIVE_DATE", "SUPERSEDES", "DEPARTMENT",
            "AUTHOR_NAME", "AUTHOR_DATE", "REVIEWER_NAME", "REVIEWER_DATE",
            "APPROVER_NAME", "APPROVER_DATE",
            "REV_1_NUM", "REV_1_DATE", "REV_1_AUTHOR", "REV_1_DESCRIPTION",
            "REV_2_NUM", "REV_2_DATE", "REV_2_AUTHOR", "REV_2_DESCRIPTION",
            "PURPOSE", "SCOPE",
            "REF_1_ID", "REF_1_TITLE", "REF_2_ID", "REF_2_TITLE",
            "REF_3_ID", "REF_3_TITLE",
            "TERM_1", "DEFINITION_1", "TERM_2", "DEFINITION_2",
            "TERM_3", "DEFINITION_3",
            "ROLE_1_TITLE", "ROLE_1_RESPONSIBILITIES",
            "ROLE_2_TITLE", "ROLE_2_RESPONSIBILITIES",
            "ROLE_3_TITLE", "ROLE_3_RESPONSIBILITIES",
            "PROCEDURE_STEP_1_TITLE", "PROCEDURE_STEP_1_DETAIL",
            "PROCEDURE_STEP_2_TITLE", "PROCEDURE_STEP_2_DETAIL",
            "PROCEDURE_STEP_3_TITLE", "PROCEDURE_STEP_3_DETAIL",
            "PROCEDURE_STEP_4_TITLE", "PROCEDURE_STEP_4_DETAIL",
            "PROCEDURE_STEP_5_TITLE", "PROCEDURE_STEP_5_DETAIL",
            "DOCUMENTATION_REQUIREMENTS", "TRAINING_REQUIREMENTS",
            "ATTACHMENTS",
        ],
    ),
    "deviation": TemplateInfo(
        file_name="Deviation_Report_Template.docx",
        display_name="Deviation Report",
        description="Identification, Description, Root Cause, Impact Assessment, CAPA, Resolution/Closure, Approval",
        placeholders=[
            "ORGANIZATION_NAME", "DEVIATION_ID", "DATE_IDENTIFIED",
            "IDENTIFIED_BY", "STUDY_PROTOCOL", "SITE_NAME",
            "DEVIATION_CATEGORY", "SEVERITY",
            "DEVIATION_DESCRIPTION", "REQUIREMENT_VIOLATED",
            "ROOT_CAUSE",
            "IMPACT_SAFETY", "IMPACT_DATA",
            "CORRECTIVE_ACTION", "PREVENTIVE_ACTION",
            "CAPA_DUE_DATE", "CAPA_RESPONSIBLE",
            "RESOLUTION_SUMMARY", "DATE_RESOLVED", "CLOSED_BY",
            "IRB_NOTIFICATION", "SPONSOR_NOTIFICATION",
            "PI_NAME", "PI_DATE", "QA_NAME", "QA_DATE",
        ],
    ),
    "capa": TemplateInfo(
        file_name="CAPA_Report_Template.docx",
        display_name="CAPA Report",
        description="Identification, Problem Statement, Root Cause Investigation, Corrective/Preventive Actions, Effectiveness Verification, Closure",
        placeholders=[
            "ORGANIZATION_NAME", "CAPA_ID", "DATE_INITIATED",
            "INITIATED_BY", "CAPA_TYPE", "PRIORITY",
            "RELATED_DEVIATIONS", "STUDY_SYSTEM",
            "PROBLEM_DESCRIPTION",
            "INVESTIGATION_METHOD", "INVESTIGATION_LEAD",
            "ROOT_CAUSE_FINDINGS", "CONTRIBUTING_FACTORS",
            "CORRECTIVE_ACTION_1", "CA1_RESPONSIBLE", "CA1_DUE",
            "CORRECTIVE_ACTION_2", "CA2_RESPONSIBLE", "CA2_DUE",
            "CORRECTIVE_ACTION_3", "CA3_RESPONSIBLE", "CA3_DUE",
            "PREVENTIVE_ACTION_1", "PA1_RESPONSIBLE", "PA1_DUE",
            "PREVENTIVE_ACTION_2", "PA2_RESPONSIBLE", "PA2_DUE",
            "VERIFICATION_METHOD", "VERIFICATION_DATE", "VERIFIED_BY",
            "EFFECTIVENESS_ASSESSMENT",
            "CAPA_STATUS", "DATE_CLOSED", "CLOSED_BY",
            "QA_NAME", "QA_DATE", "DEPT_HEAD_NAME", "DEPT_HEAD_DATE",
        ],
    ),
    "training": TemplateInfo(
        file_name="Training_Record_Template.docx",
        display_name="Training Record",
        description="Training Details, Content/Objectives, Attendance Log, Assessment, Trainer Sign-off",
        placeholders=[
            "ORGANIZATION_NAME", "RECORD_ID", "TRAINING_TITLE",
            "TRAINING_TYPE", "RELATED_SOP", "TRAINING_DATE",
            "TRAINING_METHOD", "DURATION", "TRAINER_NAME",
            "TOPICS_COVERED", "LEARNING_OBJECTIVES",
            "TRAINEE_1_NAME", "TRAINEE_1_TITLE", "TRAINEE_1_DEPT", "TRAINEE_1_DATE",
            "TRAINEE_2_NAME", "TRAINEE_2_TITLE", "TRAINEE_2_DEPT", "TRAINEE_2_DATE",
            "TRAINEE_3_NAME", "TRAINEE_3_TITLE", "TRAINEE_3_DEPT", "TRAINEE_3_DATE",
            "TRAINEE_4_NAME", "TRAINEE_4_TITLE", "TRAINEE_4_DEPT", "TRAINEE_4_DATE",
            "TRAINEE_5_NAME", "TRAINEE_5_TITLE", "TRAINEE_5_DEPT", "TRAINEE_5_DATE",
            "ASSESSMENT_METHOD", "PASSING_CRITERIA", "ASSESSMENT_NOTES",
            "SIGNOFF_DATE",
        ],
    ),
    "monitoring": TemplateInfo(
        file_name="Monitoring_Visit_Report_Template.docx",
        display_name="Monitoring Visit Report",
        description="Visit Info, Study Status, Monitoring Activities, Findings, Action Items, Assessment, Next Visit",
        placeholders=[
            "SPONSOR_NAME", "REPORT_ID", "STUDY_PROTOCOL",
            "SITE_NUMBER", "SITE_NAME", "PI_NAME",
            "VISIT_TYPE", "VISIT_DATES", "MONITOR_NAMES", "SITE_PERSONNEL",
            "SUBJECTS_SCREENED", "SUBJECTS_ENROLLED", "SUBJECTS_ACTIVE",
            "SUBJECTS_COMPLETED", "SUBJECTS_WITHDRAWN",
            "SCREEN_FAILURES", "SAES_REPORTED", "PROTOCOL_DEVIATIONS",
            "ICF_REVIEW_FINDINGS",
            "CRFS_REVIEWED", "QUERIES_GENERATED", "QUERIES_RESOLVED",
            "SDV_FINDINGS",
            "IP_ACCOUNTABILITY", "SAFETY_FINDINGS",
            "REGULATORY_FINDINGS", "LAB_FINDINGS",
            "CRITICAL_FINDINGS", "MAJOR_FINDINGS", "MINOR_FINDINGS",
            "ACTION_1", "ACTION_1_OWNER", "ACTION_1_DUE", "ACTION_1_STATUS",
            "ACTION_2", "ACTION_2_OWNER", "ACTION_2_DUE", "ACTION_2_STATUS",
            "ACTION_3", "ACTION_3_OWNER", "ACTION_3_DUE", "ACTION_3_STATUS",
            "ACTION_4", "ACTION_4_OWNER", "ACTION_4_DUE", "ACTION_4_STATUS",
            "ACTION_5", "ACTION_5_OWNER", "ACTION_5_DUE", "ACTION_5_STATUS",
            "PREVIOUS_ACTION_ITEMS_STATUS",
            "OVERALL_ASSESSMENT",
            "NEXT_VISIT_DATE", "NEXT_VISIT_TYPE", "NEXT_VISIT_FOCUS",
            "MONITOR_NAME", "MONITOR_DATE",
            "LEAD_CRA_NAME", "LEAD_CRA_DATE",
        ],
    ),
    "general": TemplateInfo(
        file_name="General_Document_Template.docx",
        display_name="General Document",
        description="Cover page, signature/revision history, TOC, abbreviations, 5 numbered sections with sub-sections, references, appendices",
        placeholders=[
            "ORGANIZATION_NAME", "DOCUMENT_TITLE", "DOCUMENT_SUBTITLE",
            "DOCUMENT_ID", "VERSION", "EFFECTIVE_DATE",
            "AUTHOR", "DEPARTMENT", "STATUS",
            "AUTHOR_DATE", "REVIEWER", "REVIEWER_DATE",
            "APPROVER", "APPROVER_DATE",
            "REV_1_VERSION", "REV_1_DATE", "REV_1_AUTHOR", "REV_1_DESCRIPTION",
            "REV_2_VERSION", "REV_2_DATE", "REV_2_AUTHOR", "REV_2_DESCRIPTION",
            "REV_3_VERSION", "REV_3_DATE", "REV_3_AUTHOR", "REV_3_DESCRIPTION",
            "ABBREV_1", "ABBREV_1_DEF", "ABBREV_2", "ABBREV_2_DEF",
            "ABBREV_3", "ABBREV_3_DEF", "ABBREV_4", "ABBREV_4_DEF",
            "ABBREV_5", "ABBREV_5_DEF",
            "SECTION_1_TITLE", "SECTION_1_CONTENT",
            "SECTION_1_1_TITLE", "SECTION_1_1_CONTENT",
            "SECTION_1_1_1_TITLE", "SECTION_1_1_1_CONTENT",
            "SECTION_1_2_TITLE", "SECTION_1_2_CONTENT",
            "SECTION_2_TITLE", "SECTION_2_CONTENT",
            "SECTION_2_1_TITLE", "SECTION_2_1_CONTENT",
            "SECTION_2_2_TITLE", "SECTION_2_2_CONTENT",
            "SECTION_3_TITLE", "SECTION_3_CONTENT",
            "SECTION_3_1_TITLE", "SECTION_3_1_CONTENT",
            "SECTION_3_2_TITLE", "SECTION_3_2_CONTENT",
            "SECTION_4_TITLE", "SECTION_4_CONTENT",
            "SECTION_4_1_TITLE", "SECTION_4_1_CONTENT",
            "SECTION_4_2_TITLE", "SECTION_4_2_CONTENT",
            "SECTION_5_TITLE", "SECTION_5_CONTENT",
            "SECTION_5_1_TITLE", "SECTION_5_1_CONTENT",
            "SECTION_5_2_TITLE", "SECTION_5_2_CONTENT",
            "REF_1_ID", "REF_1_TITLE", "REF_2_ID", "REF_2_TITLE",
            "REF_3_ID", "REF_3_TITLE",
            "APPENDICES",
        ],
    ),
}


def get_template(template_type: str) -> TemplateInfo:
    """Get template info by type. Raises KeyError if not found."""
    if template_type not in TEMPLATES:
        valid = ", ".join(sorted(TEMPLATES.keys()))
        raise KeyError(f"Unknown template type '{template_type}'. Valid types: {valid}")
    return TEMPLATES[template_type]
