"use client";

import { FileText } from "lucide-react";
import { useFormatDocument } from "@/hooks/useFormatDocument";
import { StepIndicator } from "@/components/StepIndicator";
import { TemplateGrid } from "@/components/TemplateGrid";
import { UploadZone } from "@/components/UploadZone";
import { ResultPanel } from "@/components/ResultPanel";

export default function Home() {
  const {
    step,
    selectedTemplate,
    isLoading,
    error,
    downloadUrl,
    downloadFilename,
    selectTemplate,
    uploadFile,
    reset,
    goBack,
  } = useFormatDocument();

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="border-b border-gray-200 bg-white/70 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-4 py-4 flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-teal-600 flex items-center justify-center">
            <FileText className="w-5 h-5 text-white" strokeWidth={1.5} />
          </div>
          <div>
            <h1 className="text-lg font-bold text-foreground tracking-tight">
              TraceScribe
            </h1>
            <p className="text-xs text-gray-400 -mt-0.5">Document Formatter</p>
          </div>
        </div>
      </header>

      {/* Main */}
      <main className="flex-1 max-w-5xl mx-auto w-full px-4 py-10">
        <StepIndicator currentStep={step} />

        {step === "select" && <TemplateGrid onSelect={selectTemplate} />}

        {step === "upload" && selectedTemplate && (
          <UploadZone
            templateType={selectedTemplate}
            onUpload={uploadFile}
            onBack={goBack}
          />
        )}

        {step === "result" && (
          <ResultPanel
            isLoading={isLoading}
            error={error}
            downloadUrl={downloadUrl}
            downloadFilename={downloadFilename}
            onReset={reset}
            onRetry={goBack}
          />
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-100 py-4">
        <p className="text-center text-xs text-gray-400">
          TraceScribe Document Formatter — Process in memory, nothing stored
        </p>
      </footer>
    </div>
  );
}
