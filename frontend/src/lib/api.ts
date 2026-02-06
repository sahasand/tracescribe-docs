import { TemplateType } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function formatDocument(
  file: File,
  templateType: TemplateType
): Promise<Blob> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("template_type", templateType);

  const response = await fetch(`${API_URL}/api/format`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(error.detail || `Server error: ${response.status}`);
  }

  return response.blob();
}
