"use client";

import { TemplateType } from "@/lib/types";
import { Sparkles, type LucideIcon } from "lucide-react";

interface TemplateCardProps {
  type: TemplateType;
  displayName: string;
  description: string;
  icon: LucideIcon;
  color: string;
  featured?: boolean;
  onSelect: (type: TemplateType) => void;
}

export function TemplateCard({
  type,
  displayName,
  description,
  icon: Icon,
  color,
  featured = false,
  onSelect,
}: TemplateCardProps) {
  return (
    <button
      onClick={() => onSelect(type)}
      className={`
        group relative text-left rounded-2xl p-6
        transition-all duration-200 hover:-translate-y-0.5
        focus:outline-none focus:ring-2 focus:ring-teal-400 focus:ring-offset-2
        ${
          featured
            ? "bg-gradient-to-br from-teal-50 to-white border border-teal-300 ring-1 ring-teal-100 shadow-md hover:shadow-lg"
            : "bg-white border border-gray-100 hover:border-teal-200 shadow-sm hover:shadow-md"
        }
      `}
    >
      {featured && (
        <span className="absolute top-3 right-3 inline-flex items-center gap-1 rounded-full bg-teal-600 px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-white shadow-sm">
          <Sparkles className="w-3 h-3" strokeWidth={2} />
          Most versatile
        </span>
      )}
      <div className={`${color} mb-4`}>
        <Icon className="w-8 h-8" strokeWidth={1.5} />
      </div>
      <h3
        className={`font-semibold text-foreground mb-2 transition-colors ${
          featured ? "text-teal-700" : "group-hover:text-teal-700"
        }`}
      >
        {displayName}
      </h3>
      <p className="text-sm text-gray-500 leading-relaxed">{description}</p>
      <div
        className={`mt-4 flex items-center text-xs font-medium text-teal-600 transition-opacity ${
          featured ? "opacity-70 group-hover:opacity-100" : "opacity-0 group-hover:opacity-100"
        }`}
      >
        Select template
        <svg className="w-3.5 h-3.5 ml-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
      </div>
    </button>
  );
}
