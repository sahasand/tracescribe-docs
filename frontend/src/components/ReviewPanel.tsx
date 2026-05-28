"use client";

import { ArrowLeft, FileCheck } from "lucide-react";
import { Fields } from "@/lib/types";

interface ReviewPanelProps {
  templateName: string;
  fields: Fields;
  onChange: (key: string, value: string) => void;
  onGenerate: () => void;
  onBack: () => void;
}

// Acronyms to keep uppercased when humanizing key names.
const ACRONYMS = new Set([
  "ID", "SOP", "CAPA", "IRB", "QA", "PI", "CRA", "SAE", "SAES", "ICF", "CRF",
  "CRFS", "SDV", "IP", "REV", "REF", "TOC", "DEPT", "NUM",
]);

function humanize(key: string): string {
  return key
    .toLowerCase()
    .split("_")
    .map((w) => (ACRONYMS.has(w.toUpperCase()) ? w.toUpperCase() : w.charAt(0).toUpperCase() + w.slice(1)))
    .join(" ");
}

// Long-form fields render as textareas (and support \n → paragraphs).
const LONG_SUFFIXES = [
  "CONTENT", "DESCRIPTION", "DETAIL", "PURPOSE", "SCOPE", "RESPONSIBILITIES",
  "FINDINGS", "NOTES", "ASSESSMENT", "SUMMARY", "OBJECTIVES", "REQUIREMENTS",
  "STATEMENT", "FACTORS", "TOPICS", "ATTACHMENTS", "APPENDICES", "DEFINITION",
];
function isLong(key: string): boolean {
  return LONG_SUFFIXES.some((s) => key.endsWith(s) || key.includes(s));
}

// Bucket each key into a display group (works across all 6 templates).
const GROUP_ORDER = [
  "Details", "Approvals & signatures", "Revision history", "Definitions",
  "Abbreviations", "Roles", "Procedure", "Attendance", "Monitoring",
  "Findings", "Action items", "Sections", "References", "Appendices",
];
function groupOf(key: string): string {
  if (key.startsWith("REV_")) return "Revision history";
  if (key.startsWith("ABBREV_")) return "Abbreviations";
  if (key.startsWith("SECTION_")) return "Sections";
  if (key.startsWith("REF_")) return "References";
  if (key.startsWith("TERM_") || key.startsWith("DEFINITION_")) return "Definitions";
  if (key.startsWith("ROLE_")) return "Roles";
  if (key.startsWith("PROCEDURE_STEP_")) return "Procedure";
  if (key.startsWith("TRAINEE_")) return "Attendance";
  if (key.startsWith("ACTION_")) return "Action items";
  if (key.endsWith("_FINDINGS") || key.endsWith("FINDINGS")) return "Findings";
  if (
    key.includes("APPROV") || key.includes("REVIEW") || key.endsWith("_DATE") ||
    ["PI_NAME", "QA_NAME", "DEPT_HEAD_NAME", "MONITOR_NAME", "LEAD_CRA_NAME", "CLOSED_BY", "VERIFIED_BY", "TRAINER_NAME"].includes(key)
  ) return "Approvals & signatures";
  if (key === "APPENDICES") return "Appendices";
  if (
    key.startsWith("SUBJECTS_") || key.startsWith("QUERIES_") || key.includes("ICF_") ||
    key.startsWith("CRFS_") || key.includes("IP_ACCOUNT") || key.includes("REGULATORY")
  ) return "Monitoring";
  return "Details";
}

export function ReviewPanel({ templateName, fields, onChange, onGenerate, onBack }: ReviewPanelProps) {
  const keys = Object.keys(fields);
  const groups = GROUP_ORDER
    .map((g) => ({ name: g, keys: keys.filter((k) => groupOf(k) === g) }))
    .filter((g) => g.keys.length > 0);

  return (
    <div className="max-w-3xl mx-auto">
      <button
        onClick={onBack}
        className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-teal-600 mb-6 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to upload
      </button>

      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold text-foreground mb-2">Review &amp; Edit</h2>
        <p className="text-gray-500">
          TraceScribe extracted these fields for your{" "}
          <span className="font-medium text-teal-600">{templateName}</span>. Edit anything before
          generating the document.
        </p>
      </div>

      <div className="space-y-5">
        {groups.map((group) => (
          <section
            key={group.name}
            className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5 sm:p-6"
          >
            <h3 className="text-sm font-semibold uppercase tracking-wide text-teal-700 mb-4">
              {group.name}
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {group.keys.map((key) => {
                const long = isLong(key);
                return (
                  <div key={key} className={long ? "sm:col-span-2" : ""}>
                    <label
                      htmlFor={key}
                      className="block text-xs font-medium text-gray-500 mb-1"
                    >
                      {humanize(key)}
                    </label>
                    {long ? (
                      <textarea
                        id={key}
                        value={fields[key]}
                        onChange={(e) => onChange(key, e.target.value)}
                        rows={3}
                        className="w-full rounded-md border border-gray-200 px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-teal-400 focus:border-transparent resize-y"
                      />
                    ) : (
                      <input
                        id={key}
                        type="text"
                        value={fields[key]}
                        onChange={(e) => onChange(key, e.target.value)}
                        className="w-full rounded-md border border-gray-200 px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-teal-400 focus:border-transparent"
                      />
                    )}
                  </div>
                );
              })}
            </div>
          </section>
        ))}
      </div>

      <div className="mt-8 flex justify-end gap-3">
        <button
          onClick={onBack}
          className="px-4 py-2.5 rounded-md text-sm font-medium text-gray-600 hover:bg-gray-100 transition-colors"
        >
          Back
        </button>
        <button
          onClick={() => onGenerate()}
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-md bg-teal-600 text-white text-sm font-semibold hover:bg-teal-700 transition-colors focus:outline-none focus:ring-2 focus:ring-teal-400 focus:ring-offset-2"
        >
          <FileCheck className="w-4 h-4" />
          Generate document
        </button>
      </div>
    </div>
  );
}
