import { Fields, TemplateType } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function errorMessage(response: Response): Promise<string> {
  const error = await response.json().catch(() => ({ detail: "Unknown error" }));
  return error.detail || `Server error: ${response.status}`;
}

/** Upload a document and get back the extracted fields for review. */
export async function extractFields(
  file: File,
  templateType: TemplateType
): Promise<Fields> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("template_type", templateType);

  const response = await fetch(`${API_URL}/api/extract`, {
    method: "POST",
    body: formData,
  });
  if (!response.ok) throw new Error(await errorMessage(response));

  const data = await response.json();
  return data.fields as Fields;
}

/** Fill the template from reviewed fields and get the .docx back. */
export async function fillDocument(
  templateType: TemplateType,
  fields: Fields
): Promise<Blob> {
  const response = await fetch(`${API_URL}/api/fill`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ template_type: templateType, fields }),
  });
  if (!response.ok) throw new Error(await errorMessage(response));

  return response.blob();
}
