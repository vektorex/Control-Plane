import React from "react";
import Link from "next/link";
import { Card } from "@/components/ui/Card";
import { PlusCircle, FolderPlus, Sliders, ShieldCheck, ArrowRight } from "lucide-react";

export function QuickActionCards({ onOpenCreateTask, onOpenCreateProject }) {
  const actions = [
    {
      title: "Dispatch New Task",
      description: "Define a goal, input context, and let the orchestrator route execution",
      icon: PlusCircle,
      color: "text-indigo-400 bg-indigo-950/40 border-indigo-800/60",
      action: onOpenCreateTask,
      href: null,
    },
    {
      title: "Create Project Scope",
      description: "Group tasks, attach unified context sources and custom instructions",
      icon: FolderPlus,
      color: "text-cyan-400 bg-cyan-950/40 border-cyan-800/60",
      action: onOpenCreateProject,
      href: null,
    },
    {
      title: "Configure Engine Providers",
      description: "Manage Anthropic, OpenAI, Gemini, DeepSeek, and local endpoints",
      icon: Sliders,
      color: "text-emerald-400 bg-emerald-950/40 border-emerald-800/60",
      action: null,
      href: "/app/settings",
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {actions.map((item) => {
        const Icon = item.icon;
        const content = (
          <div className="flex items-start gap-4 p-5">
            <div className={`p-3 rounded-xl border ${item.color} shrink-0`}>
              <Icon className="w-5 h-5" />
            </div>
            <div className="space-y-1">
              <div className="flex items-center gap-1.5 font-semibold text-sm text-slate-100 group-hover:text-indigo-300 transition-colors">
                <span>{item.title}</span>
                <ArrowRight className="w-3.5 h-3.5 opacity-0 -translate-x-1 group-hover:opacity-100 group-hover:translate-x-0 transition-all text-indigo-400" />
              </div>
              <p className="text-xs text-slate-400 leading-relaxed">{item.description}</p>
            </div>
          </div>
        );

        if (item.href) {
          return (
            <Link key={item.title} href={item.href} className="group">
              <Card hoverable className="h-full">
                {content}
              </Card>
            </Link>
          );
        }

        return (
          <button
            key={item.title}
            type="button"
            onClick={item.action}
            className="text-left w-full group cursor-pointer"
          >
            <Card hoverable className="h-full">
              {content}
            </Card>
          </button>
        );
      })}
    </div>
  );
}
