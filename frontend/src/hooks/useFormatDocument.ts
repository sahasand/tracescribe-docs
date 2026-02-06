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

  const uploadFile = useCallback(
    async (file: File) => {
      if (!state.selectedTemplate) return;

      setState((s) => ({
        ...s,
        step: "result" as AppStep,
        file,
        isLoading: true,
        error: null,
        downloadUrl: null,
      }));

      try {
        const blob = await formatDocument(file, state.selectedTemplate);
        const url = URL.createObjectURL(blob);
        setState((s) => ({
          ...s,
          isLoading: false,
          downloadUrl: url,
          downloadFilename: `${state.selectedTemplate}_formatted.docx`,
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
    // Revoke any existing blob URL
    if (state.downloadUrl) {
      URL.revokeObjectURL(state.downloadUrl);
    }
    setState(INITIAL_STATE);
  }, [state.downloadUrl]);

  const goBack = useCallback(() => {
    if (state.step === "upload") {
      setState((s) => ({
        ...s,
        step: "select" as AppStep,
        selectedTemplate: null,
      }));
    } else if (state.step === "result" && !state.isLoading) {
      if (state.downloadUrl) {
        URL.revokeObjectURL(state.downloadUrl);
      }
      setState((s) => ({
        ...s,
        step: "upload" as AppStep,
        file: null,
        error: null,
        downloadUrl: null,
        downloadFilename: null,
      }));
    }
  }, [state.step, state.isLoading, state.downloadUrl]);

  return {
    ...state,
    selectTemplate,
    uploadFile,
    reset,
    goBack,
  };
}
