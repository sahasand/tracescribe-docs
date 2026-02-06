"use client";

import { useCallback, useRef, useState } from "react";
import { Upload, ArrowLeft } from "lucide-react";
import { TEMPLATE_META } from "@/lib/templates";
import { TemplateType } from "@/lib/types";
import { FilePreview } from "./FilePreview";

interface UploadZoneProps {
  templateType: TemplateType;
  onUpload: (file: File) => void;
  onBack: () => void;
}

const ACCEPTED_TYPES = [
  ".docx",
  ".pdf",
  ".txt",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  "application/pdf",
  "text/plain",
];

export function UploadZone({ templateType, onUpload, onBack }: UploadZoneProps) {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const templateMeta = TEMPLATE_META.find((t) => t.type === templateType);

  const handleFile = useCallback((file: File) => {
    const ext = file.name.split(".").pop()?.toLowerCase();
    if (!ext || !["docx", "pdf", "txt"].includes(ext)) {
      alert("Please upload a .docx, .pdf, or .txt file");
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      alert("File too large. Maximum size is 10 MB.");
      return;
    }
    setSelectedFile(file);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragActive(false);
      if (e.dataTransfer.files[0]) {
        handleFile(e.dataTransfer.files[0]);
      }
    },
    [handleFile]
  );

  const handleSubmit = useCallback(() => {
    if (selectedFile) {
      onUpload(selectedFile);
    }
  }, [selectedFile, onUpload]);

  return (
    <div className="max-w-lg mx-auto">
      <button
        onClick={onBack}
        className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-teal-600 mb-6 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to templates
      </button>

      <div className="text-center mb-6">
        <h2 className="text-2xl font-bold text-foreground mb-2">Upload Your Document</h2>
        <p className="text-gray-500">
          Formatting as{" "}
          <span className="font-medium text-teal-600">{templateMeta?.displayName}</span>
        </p>
      </div>

      {/* Drop zone */}
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragActive(true);
        }}
        onDragLeave={() => setDragActive(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        className={`
          relative cursor-pointer rounded-2xl border-2 border-dashed p-10
          transition-all duration-200
          ${
            dragActive
              ? "border-teal-400 bg-teal-50"
              : "border-gray-300 bg-white hover:border-teal-300 hover:bg-gray-50"
          }
        `}
      >
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPTED_TYPES.join(",")}
          onChange={(e) => {
            if (e.target.files?.[0]) handleFile(e.target.files[0]);
          }}
          className="hidden"
        />
        <div className="flex flex-col items-center gap-3">
          <div
            className={`rounded-full p-3 transition-colors ${
              dragActive ? "bg-teal-100 text-teal-600" : "bg-gray-100 text-gray-400"
            }`}
          >
            <Upload className="w-6 h-6" />
          </div>
          <div>
            <p className="text-sm font-medium text-foreground">
              Drop your file here or click to browse
            </p>
            <p className="text-xs text-gray-400 mt-1">
              Supports .docx, .pdf, .txt (max 10 MB)
            </p>
          </div>
        </div>
      </div>

      {/* File preview */}
      {selectedFile && (
        <div className="mt-4 space-y-4">
          <FilePreview file={selectedFile} />
          <button
            onClick={handleSubmit}
            className="
              w-full py-3 px-4 rounded-md
              bg-teal-600 text-white font-medium
              hover:bg-teal-700 active:bg-teal-800
              transition-colors focus:outline-none focus:ring-2 focus:ring-teal-400 focus:ring-offset-2
            "
          >
            Format Document
          </button>
        </div>
      )}
    </div>
  );
}
