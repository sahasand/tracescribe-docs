"use client";

import { useCallback, useState } from "react";
import { AppStep, FormatState, TemplateType } from "@/lib/types";
import { formatDocument } from "@/lib/api";

const INITIAL_STATE: FormatState = {
  step: "select",
  selectedTemplate: null,
  file: null,
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

  // Drop a file → TraceScribe processes it → download. One step, no review.
  const uploadFile = useCallback(
    async (file: File) => {
      if (!state.selectedTemplate) return;
      const template = state.selectedTemplate;

      setState((s) => ({
        ...s,
        step: "result" as AppStep,
        file,
        isLoading: true,
        error: null,
        downloadUrl: null,
      }));

      try {
        const blob = await formatDocument(file, template);
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
    [state.selectedTemplate]
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
      if (s.step === "result" && !s.isLoading) {
        if (s.downloadUrl) URL.revokeObjectURL(s.downloadUrl);
        return { ...s, step: "upload", error: null, downloadUrl: null, downloadFilename: null };
      }
      return s;
    });
  }, []);

  return {
    ...state,
    selectTemplate,
    uploadFile,
    reset,
    goBack,
  };
}
