"use client";

import { TemplateType } from "@/lib/types";
import { type LucideIcon } from "lucide-react";

interface TemplateCardProps {
  type: TemplateType;
  displayName: string;
  description: string;
  icon: LucideIcon;
  color: string;
  onSelect: (type: TemplateType) => void;
}

export function TemplateCard({
  type,
  displayName,
  description,
  icon: Icon,
  color,
  onSelect,
}: TemplateCardProps) {
  return (
    <button
      onClick={() => onSelect(type)}
      className="
        group text-left bg-white rounded-2xl p-6
        shadow-sm hover:shadow-md
        border border-gray-100 hover:border-teal-200
        transition-all duration-200 hover:-translate-y-0.5
        focus:outline-none focus:ring-2 focus:ring-teal-400 focus:ring-offset-2
      "
    >
      <div className={`${color} mb-4`}>
        <Icon className="w-8 h-8" strokeWidth={1.5} />
      </div>
      <h3 className="font-semibold text-foreground mb-2 group-hover:text-teal-700 transition-colors">
        {displayName}
      </h3>
      <p className="text-sm text-gray-500 leading-relaxed">{description}</p>
      <div className="mt-4 flex items-center text-xs font-medium text-teal-600 opacity-0 group-hover:opacity-100 transition-opacity">
        Select template
        <svg className="w-3.5 h-3.5 ml-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
      </div>
    </button>
  );
}
