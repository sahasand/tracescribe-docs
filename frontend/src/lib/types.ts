export type TemplateType = "sop" | "deviation" | "capa" | "training" | "monitoring" | "general";

export interface TemplateInfo {
  type: TemplateType;
  display_name: string;
  description: string;
  placeholder_count: number;
}

export type AppStep = "select" | "upload" | "review" | "result";

// Extracted fields. Flat templates have string values; the General Document
// adds variable-length lists, so values may be strings or arrays.
export type Fields = Record<string, unknown>;

export interface Abbrev { term: string; definition: string }
export interface Reference { id: string; title: string }
export interface Revision { version: string; date: string; author: string; description: string }
export interface Subsubsection { title: string; content: string }
export interface Subsection { title: string; content: string; subsubsections: Subsubsection[] }
export interface Section { title: string; content: string; subsections: Subsection[] }

export interface FormatState {
  step: AppStep;
  selectedTemplate: TemplateType | null;
  file: File | null;
  fields: Fields | null;
  isLoading: boolean;
  error: string | null;
  downloadUrl: string | null;
  downloadFilename: string | null;
}
