"use client";

import { AppStep } from "@/lib/types";
import { Check } from "lucide-react";

interface StepIndicatorProps {
  currentStep: AppStep;
}

const STEPS: { key: AppStep; label: string }[] = [
  { key: "select", label: "Choose Template" },
  { key: "upload", label: "Upload Document" },
  { key: "result", label: "Download Result" },
];

export function StepIndicator({ currentStep }: StepIndicatorProps) {
  const currentIndex = STEPS.findIndex((s) => s.key === currentStep);

  return (
    <div className="flex items-center justify-center gap-2 mb-10">
      {STEPS.map((step, i) => {
        const isCompleted = i < currentIndex;
        const isCurrent = i === currentIndex;

        return (
          <div key={step.key} className="flex items-center gap-2">
            {i > 0 && (
              <div
                className={`h-px w-8 sm:w-12 transition-colors duration-300 ${
                  isCompleted ? "bg-teal-600" : "bg-gray-300"
                }`}
              />
            )}
            <div className="flex items-center gap-2">
              <div
                className={`
                  w-7 h-7 rounded-full flex items-center justify-center text-xs font-semibold
                  transition-all duration-300
                  ${
                    isCompleted
                      ? "bg-teal-600 text-white"
                      : isCurrent
                      ? "bg-teal-600 text-white ring-2 ring-teal-200"
                      : "bg-gray-200 text-gray-500"
                  }
                `}
              >
                {isCompleted ? <Check className="w-3.5 h-3.5" /> : i + 1}
              </div>
              <span
                className={`text-sm font-medium hidden sm:inline ${
                  isCurrent ? "text-teal-700" : isCompleted ? "text-gray-600" : "text-gray-400"
                }`}
              >
                {step.label}
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
