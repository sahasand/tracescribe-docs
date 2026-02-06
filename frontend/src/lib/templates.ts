import { TemplateType } from "./types";
import {
  FileText,
  AlertTriangle,
  Shield,
  GraduationCap,
  ClipboardCheck,
  BookOpen,
  type LucideIcon,
} from "lucide-react";

interface TemplateMeta {
  type: TemplateType;
  displayName: string;
  description: string;
  icon: LucideIcon;
  color: string;
}

export const TEMPLATE_META: TemplateMeta[] = [
  {
    type: "sop",
    displayName: "Standard Operating Procedure",
    description:
      "Purpose, scope, roles, procedure steps, documentation & training requirements",
    icon: FileText,
    color: "text-teal-600",
  },
  {
    type: "deviation",
    displayName: "Deviation Report",
    description:
      "Identification, root cause, impact assessment, CAPA, resolution & closure",
    icon: AlertTriangle,
    color: "text-coral-500",
  },
  {
    type: "capa",
    displayName: "CAPA Report",
    description:
      "Problem statement, root cause investigation, corrective & preventive actions",
    icon: Shield,
    color: "text-teal-700",
  },
  {
    type: "training",
    displayName: "Training Record",
    description:
      "Training details, content/objectives, attendance log, assessment & sign-off",
    icon: GraduationCap,
    color: "text-coral-600",
  },
  {
    type: "monitoring",
    displayName: "Monitoring Visit Report",
    description:
      "Visit info, study status, monitoring activities, findings & action items",
    icon: ClipboardCheck,
    color: "text-teal-500",
  },
  {
    type: "general",
    displayName: "General Document",
    description:
      "Cover page, signatures, revision history, numbered sections, references & appendices",
    icon: BookOpen,
    color: "text-gray-600",
  },
];
