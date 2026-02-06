"use client";

import { Download, RotateCcw, AlertCircle, Loader2 } from "lucide-react";

interface ResultPanelProps {
  isLoading: boolean;
  error: string | null;
  downloadUrl: string | null;
  downloadFilename: string | null;
  onReset: () => void;
  onRetry: () => void;
}

export function ResultPanel({
  isLoading,
  error,
  downloadUrl,
  downloadFilename,
  onReset,
  onRetry,
}: ResultPanelProps) {
  return (
    <div className="max-w-lg mx-auto text-center">
      {/* Loading */}
      {isLoading && (
        <div className="bg-white rounded-2xl p-10 shadow-sm border border-gray-100">
          <Loader2 className="w-12 h-12 text-teal-600 animate-spin mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-foreground mb-2">
            Formatting Your Document
          </h3>
          <p className="text-sm text-gray-500">
            AI is extracting and structuring the content. This may take 15-30 seconds.
          </p>
          <div className="mt-6 flex justify-center">
            <div className="flex gap-1">
              {[0, 1, 2].map((i) => (
                <div
                  key={i}
                  className="w-2 h-2 rounded-full bg-teal-400 animate-bounce"
                  style={{ animationDelay: `${i * 0.15}s` }}
                />
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="bg-white rounded-2xl p-10 shadow-sm border border-red-100">
          <div className="w-12 h-12 rounded-full bg-red-50 flex items-center justify-center mx-auto mb-4">
            <AlertCircle className="w-6 h-6 text-red-500" />
          </div>
          <h3 className="text-lg font-semibold text-foreground mb-2">
            Something Went Wrong
          </h3>
          <p className="text-sm text-gray-500 mb-6">{error}</p>
          <div className="flex gap-3 justify-center">
            <button
              onClick={onRetry}
              className="
                py-2.5 px-5 rounded-md text-sm font-medium
                bg-teal-600 text-white hover:bg-teal-700
                transition-colors focus:outline-none focus:ring-2 focus:ring-teal-400
              "
            >
              Try Again
            </button>
            <button
              onClick={onReset}
              className="
                py-2.5 px-5 rounded-md text-sm font-medium
                bg-gray-100 text-gray-600 hover:bg-gray-200
                transition-colors focus:outline-none focus:ring-2 focus:ring-gray-300
              "
            >
              Start Over
            </button>
          </div>
        </div>
      )}

      {/* Success */}
      {downloadUrl && (
        <div className="bg-white rounded-2xl p-10 shadow-sm border border-teal-100">
          <div className="w-16 h-16 rounded-full bg-teal-50 flex items-center justify-center mx-auto mb-4">
            <Download className="w-8 h-8 text-teal-600" />
          </div>
          <h3 className="text-lg font-semibold text-foreground mb-2">
            Document Ready
          </h3>
          <p className="text-sm text-gray-500 mb-6">
            Your formatted document has been created successfully.
          </p>
          <div className="flex flex-col gap-3">
            <a
              href={downloadUrl}
              download={downloadFilename || "formatted.docx"}
              className="
                inline-flex items-center justify-center gap-2
                py-3 px-5 rounded-md text-sm font-medium
                bg-teal-600 text-white hover:bg-teal-700
                transition-colors focus:outline-none focus:ring-2 focus:ring-teal-400
              "
            >
              <Download className="w-4 h-4" />
              Download {downloadFilename}
            </a>
            <button
              onClick={onReset}
              className="
                inline-flex items-center justify-center gap-2
                py-2.5 px-5 rounded-md text-sm font-medium
                text-gray-600 hover:bg-gray-100
                transition-colors focus:outline-none focus:ring-2 focus:ring-gray-300
              "
            >
              <RotateCcw className="w-4 h-4" />
              Format Another Document
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
