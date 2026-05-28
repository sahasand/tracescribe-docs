"use client";

import { useCallback, useState } from "react";
import { AppStep, Fields, FormatState, TemplateType } from "@/lib/types";
import { extractFields, fillDocument } from "@/lib/api";

const INITIAL_STATE: FormatState = {
  step: "select",
  selectedTemplate: null,
  file: null,
  fields: null,
  isLoading: false,
  error: null,
  downloadUrl: null,
  downloadFilename: null,
};

export function useFormatDocument() {
  const [state, setState] = useState<FormatState>(INITIAL_STATE);

  const selectTemplate = useCallback((type: TemplateType) => {
    setState((s) => ({
      ...s,
      step: "upload" as AppStep,
      selectedTemplate: type,
      error: null,
    }));
  }, []);

  // Upload → extract fields → move to the review step.
  const uploadFile = useCallback(
    async (file: File) => {
      if (!state.selectedTemplate) return;
      const template = state.selectedTemplate;

      setState((s) => ({ ...s, file, isLoading: true, error: null }));

      try {
        const fields = await extractFields(file, template);
        setState((s) => ({
          ...s,
          step: "review" as AppStep,
          isLoading: false,
          fields,
        }));
      } catch (err) {
        setState((s) => ({
          ...s,
          isLoading: false,
          error: err instanceof Error ? err.message : "An error occurred",
        }));
      }
    },
    [state.selectedTemplate]
  );

  const updateField = useCallback((key: string, value: string) => {
    setState((s) => (s.fields ? { ...s, fields: { ...s.fields, [key]: value } } : s));
  }, []);

  // Review confirmed → fill the template → download result.
  const confirmAndFill = useCallback(
    async (fields?: Fields) => {
      const template = state.selectedTemplate;
      const finalFields = fields ?? state.fields;
      if (!template || !finalFields) return;

      setState((s) => ({
        ...s,
        step: "result" as AppStep,
        isLoading: true,
        error: null,
        downloadUrl: null,
      }));

      try {
        const blob = await fillDocument(template, finalFields);
        const url = URL.createObjectURL(blob);
        setState((s) => ({
          ...s,
          isLoading: false,
          downloadUrl: url,
          downloadFilename: `${template}_formatted.docx`,
        }));
      } catch (err) {
        setState((s) => ({
          ...s,
          isLoading: false,
          error: err instanceof Error ? err.message : "An error occurred",
        }));
      }
    },
    [state.selectedTemplate, state.fields]
  );

  const reset = useCallback(() => {
    if (state.downloadUrl) URL.revokeObjectURL(state.downloadUrl);
    setState(INITIAL_STATE);
  }, [state.downloadUrl]);

  const goBack = useCallback(() => {
    setState((s) => {
      if (s.step === "upload") {
        return { ...s, step: "select", selectedTemplate: null };
      }
      if (s.step === "review") {
        return { ...s, step: "upload", fields: null, error: null };
      }
      if (s.step === "result" && !s.isLoading) {
        if (s.downloadUrl) URL.revokeObjectURL(s.downloadUrl);
        // Return to review so edits aren't lost.
        return { ...s, step: "review", error: null, downloadUrl: null, downloadFilename: null };
      }
      return s;
    });
  }, []);

  return {
    ...state,
    selectTemplate,
    uploadFile,
    updateField,
    confirmAndFill,
    reset,
    goBack,
  };
}
