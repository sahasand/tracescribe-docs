"use client";

import { FileText, FileType, File as FileIcon } from "lucide-react";

interface FilePreviewProps {
  file: File;
}

function getFileIcon(filename: string) {
  const ext = filename.split(".").pop()?.toLowerCase();
  switch (ext) {
    case "pdf":
      return <FileType className="w-5 h-5" />;
    case "docx":
      return <FileText className="w-5 h-5" />;
    default:
      return <FileIcon className="w-5 h-5" />;
  }
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function FilePreview({ file }: FilePreviewProps) {
  return (
    <div className="flex items-center gap-3 bg-teal-50 rounded-xl p-3 border border-teal-100">
      <div className="text-teal-600">{getFileIcon(file.name)}</div>
      <div className="min-w-0 flex-1">
        <p className="text-sm font-medium text-foreground truncate">{file.name}</p>
        <p className="text-xs text-gray-500">{formatFileSize(file.size)}</p>
      </div>
    </div>
  );
}
