"use client";

import React, { useState, useEffect } from "react";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { workflowService } from "@/services/workflows";
import { useRouter } from "next/navigation";
import {
  Sparkles,
  BookOpen,
  FileSearch,
  CheckCircle2,
  Layers,
  ArrowRight,
  Loader2,
} from "lucide-react";

const templateIcons = {
  "research-assistant": FileSearch,
  "document-qa": BookOpen,
  "summarize-and-verify": CheckCircle2,
  "research-report": Layers,
};

export function TemplateGallery({ onTemplateInstalled }) {
  const router = useRouter();
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [installingId, setInstallingId] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function loadTemplates() {
      try {
        setLoading(true);
        const res = await workflowService.listTemplates();
        setTemplates(res?.templates || []);
      } catch (err) {
        console.error("[TemplateGallery] Error loading templates:", err);
      } finally {
        setLoading(false);
      }
    }
    loadTemplates();
  }, []);

  const handleInstall = async (tpl) => {
    try {
      setInstallingId(tpl.id);
      setError(null);
      const installed = await workflowService.installTemplate(tpl.id);
      if (onTemplateInstalled) onTemplateInstalled(installed);
      router.push(`/app/workflows/${installed.id}`);
    } catch (err) {
      console.error("[TemplateGallery] Install error:", err);
      setError(err.message || "Failed to install template");
    } finally {
      setInstallingId(null);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8 text-slate-400">
        <Loader2 className="w-5 h-5 animate-spin mr-2" />
        <span>Loading workflow templates...</span>
      </div>
    );
  }

  if (templates.length === 0) {
    return null;
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-indigo-400" />
          <h2 className="text-sm font-semibold text-slate-200 tracking-wide uppercase">
            Start from a Template
          </h2>
        </div>
        <span className="text-xs text-slate-400">Pre-configured production pipelines</span>
      </div>

      {error && (
        <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded-lg text-rose-400 text-xs">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {templates.map((tpl) => {
          const Icon = templateIcons[tpl.id] || Sparkles;
          const isInstalling = installingId === tpl.id;
          const stepCount = tpl.definition?.steps?.length || 0;

          return (
            <Card
              key={tpl.id}
              className="p-4 flex flex-col justify-between hover:border-indigo-500/40 transition-all duration-200 bg-slate-900/60 backdrop-blur-sm group"
            >
              <div className="space-y-2.5">
                <div className="flex items-start justify-between">
                  <div className="p-2.5 rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 group-hover:scale-105 transition-transform">
                    <Icon className="w-5 h-5" />
                  </div>
                  <Badge variant="outline" className="text-[10px] font-mono">
                    {stepCount} Steps
                  </Badge>
                </div>

                <div>
                  <h3 className="text-sm font-semibold text-slate-100 group-hover:text-indigo-300 transition-colors">
                    {tpl.name}
                  </h3>
                  <p className="text-xs text-slate-400 line-clamp-2 mt-1 leading-relaxed">
                    {tpl.description}
                  </p>
                </div>

                {/* Step preview pill flow */}
                <div className="pt-1 flex flex-wrap gap-1">
                  {tpl.definition?.steps?.slice(0, 4).map((s, idx) => (
                    <span
                      key={idx}
                      className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 font-mono"
                    >
                      {s.type}
                    </span>
                  ))}
                  {stepCount > 4 && (
                    <span className="text-[10px] px-1 py-0.5 text-slate-400">
                      +{stepCount - 4}
                    </span>
                  )}
                </div>
              </div>

              <div className="pt-4 mt-2 border-t border-slate-800/80">
                <Button
                  size="sm"
                  variant="outline"
                  className="w-full justify-between group-hover:border-indigo-500/50 group-hover:bg-indigo-500/10 text-xs"
                  onClick={() => handleInstall(tpl)}
                  disabled={isInstalling}
                >
                  <span>{isInstalling ? "Installing..." : "Use Template"}</span>
                  {isInstalling ? (
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  ) : (
                    <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
                  )}
                </Button>
              </div>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
