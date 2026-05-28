export type TemplateType = "sop" | "deviation" | "capa" | "training" | "monitoring" | "general";

export interface TemplateInfo {
  type: TemplateType;
  display_name: string;
  description: string;
  placeholder_count: number;
}

export type AppStep = "select" | "upload" | "review" | "result";

export type Fields = Record<string, string>;

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
