"use client";

import { useState } from "react";
import { ArrowLeft, FileCheck, Plus, X } from "lucide-react";
import {
  Abbrev,
  Fields,
  Reference,
  Revision,
  Section,
  Subsection,
  Subsubsection,
} from "@/lib/types";

const SCALAR_GROUPS: { name: string; keys: string[] }[] = [
  {
    name: "Cover",
    keys: ["ORGANIZATION_NAME", "DOCUMENT_TITLE", "DOCUMENT_SUBTITLE", "DOCUMENT_ID", "VERSION", "EFFECTIVE_DATE", "AUTHOR", "DEPARTMENT", "STATUS"],
  },
  { name: "Signatures", keys: ["AUTHOR_DATE", "REVIEWER", "REVIEWER_DATE", "APPROVER", "APPROVER_DATE"] },
  { name: "Appendices", keys: ["APPENDICES"] },
];
const SCALAR_KEYS = SCALAR_GROUPS.flatMap((g) => g.keys);

const LABELS: Record<string, string> = {
  ORGANIZATION_NAME: "Organization", DOCUMENT_TITLE: "Title", DOCUMENT_SUBTITLE: "Subtitle",
  DOCUMENT_ID: "Document ID", VERSION: "Version", EFFECTIVE_DATE: "Effective date",
  AUTHOR: "Author", DEPARTMENT: "Department", STATUS: "Status", AUTHOR_DATE: "Author date",
  REVIEWER: "Reviewer", REVIEWER_DATE: "Reviewer date", APPROVER: "Approver",
  APPROVER_DATE: "Approver date", APPENDICES: "Appendices",
};

function replaceAt<T>(arr: T[], i: number, v: T): T[] {
  return arr.map((x, j) => (j === i ? v : x));
}
function removeAt<T>(arr: T[], i: number): T[] {
  return arr.filter((_, j) => j !== i);
}
function asList<T>(v: unknown): T[] {
  return Array.isArray(v) ? (v as T[]) : [];
}

interface Props {
  templateName: string;
  fields: Fields;
  onGenerate: (fields: Fields) => void;
  onBack: () => void;
}

// Small building blocks --------------------------------------------------------

function Field({ label, value, onChange, long }: { label: string; value: string; onChange: (v: string) => void; long?: boolean }) {
  return (
    <div className={long ? "sm:col-span-2" : ""}>
      <label className="block text-xs font-medium text-gray-500 mb-1">{label}</label>
      {long ? (
        <textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          rows={3}
          className="w-full rounded-md border border-gray-200 px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-teal-400 resize-y"
        />
      ) : (
        <input
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="w-full rounded-md border border-gray-200 px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-teal-400"
        />
      )}
    </div>
  );
}

function ListSection<T>({ title, items, blank, render, onChange, addLabel }: {
  title: string;
  items: T[];
  blank: T;
  render: (item: T, onItem: (patch: Partial<T>) => void) => React.ReactNode;
  onChange: (items: T[]) => void;
  addLabel: string;
}) {
  return (
    <section className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5 sm:p-6">
      <h3 className="text-sm font-semibold uppercase tracking-wide text-teal-700 mb-4">{title}</h3>
      <div className="space-y-3">
        {items.map((item, i) => (
          <div key={i} className="relative rounded-xl border border-gray-100 bg-gray-50/60 p-4">
            <button
              onClick={() => onChange(removeAt(items, i))}
              className="absolute top-2 right-2 text-gray-400 hover:text-red-500 transition-colors"
              aria-label="Remove"
            >
              <X className="w-4 h-4" />
            </button>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pr-6">
              {render(item, (patch) => onChange(replaceAt(items, i, { ...item, ...patch })))}
            </div>
          </div>
        ))}
      </div>
      <button
        onClick={() => onChange([...items, blank])}
        className="mt-3 inline-flex items-center gap-1.5 text-sm font-medium text-teal-600 hover:text-teal-700"
      >
        <Plus className="w-4 h-4" /> {addLabel}
      </button>
    </section>
  );
}

// Main component ---------------------------------------------------------------

export function StructuredReview({ templateName, fields, onGenerate, onBack }: Props) {
  const [scalars, setScalars] = useState<Record<string, string>>(() =>
    Object.fromEntries(SCALAR_KEYS.map((k) => [k, typeof fields[k] === "string" ? (fields[k] as string) : ""]))
  );
  const [revisions, setRevisions] = useState<Revision[]>(() => asList<Revision>(fields.revisions));
  const [abbreviations, setAbbrevs] = useState<Abbrev[]>(() => asList<Abbrev>(fields.abbreviations));
  const [references, setReferences] = useState<Reference[]>(() => asList<Reference>(fields.references));
  const [sections, setSections] = useState<Section[]>(() => asList<Section>(fields.sections));

  const setScalar = (k: string, v: string) => setScalars((s) => ({ ...s, [k]: v }));

  // Section helpers (nested immutable updates).
  const updateSection = (i: number, patch: Partial<Section>) =>
    setSections((s) => replaceAt(s, i, { ...s[i], ...patch }));
  const updateSub = (i: number, j: number, patch: Partial<Subsection>) =>
    updateSection(i, { subsections: replaceAt(sections[i].subsections, j, { ...sections[i].subsections[j], ...patch }) });
  const updateSubsub = (i: number, j: number, k: number, patch: Partial<Subsubsection>) => {
    const sub = sections[i].subsections[j];
    updateSub(i, j, { subsubsections: replaceAt(sub.subsubsections, k, { ...sub.subsubsections[k], ...patch }) });
  };

  const generate = () =>
    onGenerate({ ...scalars, revisions, abbreviations, references, sections });

  return (
    <div className="max-w-3xl mx-auto">
      <button onClick={onBack} className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-teal-600 mb-6 transition-colors">
        <ArrowLeft className="w-4 h-4" /> Back to upload
      </button>

      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold text-foreground mb-2">Review &amp; Edit</h2>
        <p className="text-gray-500">
          TraceScribe extracted these fields for your{" "}
          <span className="font-medium text-teal-600">{templateName}</span>. Add, remove, or edit
          anything before generating.
        </p>
      </div>

      <div className="space-y-5">
        {/* Scalar groups */}
        {SCALAR_GROUPS.map((group) => (
          <section key={group.name} className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5 sm:p-6">
            <h3 className="text-sm font-semibold uppercase tracking-wide text-teal-700 mb-4">{group.name}</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {group.keys.map((k) => (
                <Field
                  key={k}
                  label={LABELS[k] ?? k}
                  value={scalars[k]}
                  onChange={(v) => setScalar(k, v)}
                  long={k === "APPENDICES"}
                />
              ))}
            </div>
          </section>
        ))}

        {/* Revision history */}
        <ListSection<Revision>
          title="Revision history" items={revisions} onChange={setRevisions}
          blank={{ version: "", date: "", author: "", description: "" }} addLabel="Add revision"
          render={(it, on) => (
            <>
              <Field label="Version" value={it.version} onChange={(v) => on({ version: v })} />
              <Field label="Date" value={it.date} onChange={(v) => on({ date: v })} />
              <Field label="Author" value={it.author} onChange={(v) => on({ author: v })} />
              <Field label="Description" value={it.description} onChange={(v) => on({ description: v })} />
            </>
          )}
        />

        {/* Abbreviations */}
        <ListSection<Abbrev>
          title="Abbreviations" items={abbreviations} onChange={setAbbrevs}
          blank={{ term: "", definition: "" }} addLabel="Add abbreviation"
          render={(it, on) => (
            <>
              <Field label="Term" value={it.term} onChange={(v) => on({ term: v })} />
              <Field label="Definition" value={it.definition} onChange={(v) => on({ definition: v })} />
            </>
          )}
        />

        {/* References */}
        <ListSection<Reference>
          title="References" items={references} onChange={setReferences}
          blank={{ id: "", title: "" }} addLabel="Add reference"
          render={(it, on) => (
            <>
              <Field label="Document ID" value={it.id} onChange={(v) => on({ id: v })} />
              <Field label="Title" value={it.title} onChange={(v) => on({ title: v })} />
            </>
          )}
        />

        {/* Sections (nested) */}
        <section className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5 sm:p-6">
          <h3 className="text-sm font-semibold uppercase tracking-wide text-teal-700 mb-4">Sections</h3>
          <div className="space-y-4">
            {sections.map((sec, i) => (
              <div key={i} className="relative rounded-xl border border-teal-100 bg-teal-50/40 p-4">
                <button
                  onClick={() => setSections((s) => removeAt(s, i))}
                  className="absolute top-2 right-2 text-gray-400 hover:text-red-500"
                  aria-label="Remove section"
                >
                  <X className="w-4 h-4" />
                </button>
                <div className="grid grid-cols-1 gap-3 pr-6">
                  <Field label={`Section ${i + 1} title`} value={sec.title} onChange={(v) => updateSection(i, { title: v })} />
                  <Field label="Content" long value={sec.content} onChange={(v) => updateSection(i, { content: v })} />
                </div>

                {/* Subsections */}
                <div className="mt-3 ml-3 pl-3 border-l-2 border-teal-200 space-y-3">
                  {sec.subsections.map((sub, j) => (
                    <div key={j} className="relative rounded-lg border border-gray-100 bg-white p-3">
                      <button
                        onClick={() => updateSection(i, { subsections: removeAt(sec.subsections, j) })}
                        className="absolute top-2 right-2 text-gray-400 hover:text-red-500"
                        aria-label="Remove subsection"
                      >
                        <X className="w-3.5 h-3.5" />
                      </button>
                      <div className="grid grid-cols-1 gap-3 pr-6">
                        <Field label={`Subsection ${i + 1}.${j + 1} title`} value={sub.title} onChange={(v) => updateSub(i, j, { title: v })} />
                        <Field label="Content" long value={sub.content} onChange={(v) => updateSub(i, j, { content: v })} />
                      </div>

                      {/* Sub-subsections */}
                      <div className="mt-2 ml-3 pl-3 border-l-2 border-gray-200 space-y-2">
                        {sub.subsubsections.map((ss, k) => (
                          <div key={k} className="relative rounded-lg border border-gray-100 bg-gray-50 p-3">
                            <button
                              onClick={() => updateSub(i, j, { subsubsections: removeAt(sub.subsubsections, k) })}
                              className="absolute top-2 right-2 text-gray-400 hover:text-red-500"
                              aria-label="Remove sub-subsection"
                            >
                              <X className="w-3.5 h-3.5" />
                            </button>
                            <div className="grid grid-cols-1 gap-2 pr-6">
                              <Field label={`Sub-subsection ${i + 1}.${j + 1}.${k + 1} title`} value={ss.title} onChange={(v) => updateSubsub(i, j, k, { title: v })} />
                              <Field label="Content" long value={ss.content} onChange={(v) => updateSubsub(i, j, k, { content: v })} />
                            </div>
                          </div>
                        ))}
                        <button
                          onClick={() => updateSub(i, j, { subsubsections: [...sub.subsubsections, { title: "", content: "" }] })}
                          className="inline-flex items-center gap-1 text-xs font-medium text-teal-600 hover:text-teal-700"
                        >
                          <Plus className="w-3.5 h-3.5" /> Add sub-subsection
                        </button>
                      </div>
                    </div>
                  ))}
                  <button
                    onClick={() => updateSection(i, { subsections: [...sec.subsections, { title: "", content: "", subsubsections: [] }] })}
                    className="inline-flex items-center gap-1 text-sm font-medium text-teal-600 hover:text-teal-700"
                  >
                    <Plus className="w-4 h-4" /> Add subsection
                  </button>
                </div>
              </div>
            ))}
          </div>
          <button
            onClick={() => setSections((s) => [...s, { title: "", content: "", subsections: [] }])}
            className="mt-4 inline-flex items-center gap-1.5 text-sm font-medium text-teal-600 hover:text-teal-700"
          >
            <Plus className="w-4 h-4" /> Add section
          </button>
        </section>
      </div>

      <div className="mt-8 flex justify-end gap-3">
        <button onClick={onBack} className="px-4 py-2.5 rounded-md text-sm font-medium text-gray-600 hover:bg-gray-100 transition-colors">
          Back
        </button>
        <button
          onClick={generate}
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-md bg-teal-600 text-white text-sm font-semibold hover:bg-teal-700 transition-colors focus:outline-none focus:ring-2 focus:ring-teal-400 focus:ring-offset-2"
        >
          <FileCheck className="w-4 h-4" /> Generate document
        </button>
      </div>
    </div>
  );
}
