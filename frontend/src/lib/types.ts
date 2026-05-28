export type TemplateType = "sop" | "deviation" | "capa" | "training" | "monitoring" | "general";

export interface TemplateInfo {
  type: TemplateType;
  display_name: string;
  description: string;
  placeholder_count: number;
}

export type AppStep = "select" | "upload" | "result";

export interface FormatState {
  step: AppStep;
  selectedTemplate: TemplateType | null;
  file: File | null;
  isLoading: boolean;
  error: string | null;
  downloadUrl: string | null;
  downloadFilename: string | null;
}
