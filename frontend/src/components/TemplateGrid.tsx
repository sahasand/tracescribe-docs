"use client";

import { TemplateType } from "@/lib/types";
import { TEMPLATE_META } from "@/lib/templates";
import { TemplateCard } from "./TemplateCard";

interface TemplateGridProps {
  onSelect: (type: TemplateType) => void;
}

export function TemplateGrid({ onSelect }: TemplateGridProps) {
  return (
    <div>
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold text-foreground mb-2">
          Choose a Template
        </h2>
        <p className="text-gray-500">
          Select the document type you want to create from your source file
        </p>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 max-w-4xl mx-auto">
        {TEMPLATE_META.map((tmpl) => (
          <TemplateCard
            key={tmpl.type}
            type={tmpl.type}
            displayName={tmpl.displayName}
            description={tmpl.description}
            icon={tmpl.icon}
            color={tmpl.color}
            onSelect={onSelect}
          />
        ))}
      </div>
    </div>
  );
}
