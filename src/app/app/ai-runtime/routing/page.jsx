"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  Sliders,
  ArrowLeft,
  RefreshCw,
  Cpu,
  Layers,
  ShieldCheck,
  CheckCircle,
  HelpCircle,
  ExternalLink,
} from "lucide-react";
import { previewGatewayRouting, listGatewayProviders } from "@/services/gateway";

export default function ModelRoutingPreviewPage() {
  const [taskType, setTaskType] = useState("general");
  const [streaming, setStreaming] = useState(true);
  const [toolsRequired, setToolsRequired] = useState(false);
  const [structuredOutput, setStructuredOutput] = useState(false);
  const [visionRequired, setVisionRequired] = useState(false);
  const [contextTokens, setContextTokens] = useState(4000);
  const [providerPref, setProviderPref] = useState("");
  const [latencyPref, setLatencyPref] = useState("balanced");
  const [costPref, setCostPref] = useState("balanced");

  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [providers, setProviders] = useState([]);

  useEffect(() => {
    listGatewayProviders().then((res) => setProviders(res || [])).catch(() => {});
  }, []);

  const handlePreview = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = {
        model: "auto",
        provider: providerPref || undefined,
        stream: streaming,
        tools: toolsRequired ? [{ name: "search" }] : undefined,
        response_format: structuredOutput ? { type: "json_object" } : undefined,
        latency_preference: latencyPref,
        cost_preference: costPref,
      };
      const res = await previewGatewayRouting(data);
      setPreview(res);
    } catch (err) {
      setError(err.message || "Failed to generate routing preview.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    handlePreview();
  }, [taskType, streaming, toolsRequired, structuredOutput, visionRequired, contextTokens, providerPref, latencyPref, costPref]);

  return (
    <div className="space-y-8 max-w-6xl mx-auto p-4 sm:p-6 lg:p-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border/40 pb-6">
        <div>
          <Link
            href="/app/ai-runtime"
            className="inline-flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground mb-2 transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            Back to AI Runtime
          </Link>
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-primary/10 border border-primary/20 text-primary">
              <Sliders className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl sm:text-3xl font-bold tracking-tight">Model Routing Preview</h1>
              <p className="text-muted-foreground text-sm mt-1">
                Deterministic matching of task requirements against provider capabilities. (No subjective rankings).
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Controls Column */}
        <div className="p-6 rounded-2xl border border-border/60 bg-card space-y-6 shadow-sm">
          <h2 className="font-semibold text-base flex items-center gap-2">
            <Layers className="w-4 h-4 text-primary" />
            Routing Constraints
          </h2>

          <div className="space-y-4 text-sm">
            <div>
              <label className="block text-xs font-medium text-muted-foreground mb-1.5">Task Category</label>
              <select
                value={taskType}
                onChange={(e) => setTaskType(e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-border bg-background focus:ring-1 focus:ring-primary text-sm"
              >
                <option value="general">General Synthesis & Generation</option>
                <option value="coding">Code & Technical Architecture</option>
                <option value="reasoning">Complex Step-by-Step Reasoning</option>
                <option value="extraction">Structured Data Extraction</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-muted-foreground mb-1.5">Provider Preference</label>
              <select
                value={providerPref}
                onChange={(e) => setProviderPref(e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-border bg-background focus:ring-1 focus:ring-primary text-sm"
              >
                <option value="">Any Available Provider</option>
                {providers.map((p) => (
                  <option key={p.name} value={p.name}>
                    {p.display_name} ({p.name})
                  </option>
                ))}
              </select>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1.5">Latency</label>
                <select
                  value={latencyPref}
                  onChange={(e) => setLatencyPref(e.target.value)}
                  className="w-full px-2.5 py-1.5 rounded-lg border border-border bg-background text-xs"
                >
                  <option value="low">Low Latency</option>
                  <option value="balanced">Balanced</option>
                  <option value="high_quality">High Quality</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1.5">Cost</label>
                <select
                  value={costPref}
                  onChange={(e) => setCostPref(e.target.value)}
                  className="w-full px-2.5 py-1.5 rounded-lg border border-border bg-background text-xs"
                >
                  <option value="low">Cost Efficient</option>
                  <option value="balanced">Balanced</option>
                  <option value="quality">Deep Capacity</option>
                </select>
              </div>
            </div>

            <div className="pt-2 border-t border-border/40 space-y-3">
              <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider block">
                Required Capabilities
              </label>

              <label className="flex items-center gap-2.5 cursor-pointer">
                <input
                  type="checkbox"
                  checked={streaming}
                  onChange={(e) => setStreaming(e.target.checked)}
                  className="rounded border-border text-primary focus:ring-primary"
                />
                <span>Streaming tokens required</span>
              </label>

              <label className="flex items-center gap-2.5 cursor-pointer">
                <input
                  type="checkbox"
                  checked={toolsRequired}
                  onChange={(e) => setToolsRequired(e.target.checked)}
                  className="rounded border-border text-primary focus:ring-primary"
                />
                <span>Tool / function calling</span>
              </label>

              <label className="flex items-center gap-2.5 cursor-pointer">
                <input
                  type="checkbox"
                  checked={structuredOutput}
                  onChange={(e) => setStructuredOutput(e.target.checked)}
                  className="rounded border-border text-primary focus:ring-primary"
                />
                <span>Strict JSON schema output</span>
              </label>

              <label className="flex items-center gap-2.5 cursor-pointer">
                <input
                  type="checkbox"
                  checked={visionRequired}
                  onChange={(e) => setVisionRequired(e.target.checked)}
                  className="rounded border-border text-primary focus:ring-primary"
                />
                <span>Vision / Multimodal input</span>
              </label>
            </div>
          </div>
        </div>

        {/* Results Column */}
        <div className="lg:col-span-2 space-y-6">
          {loading && (
            <div className="p-12 text-center text-muted-foreground flex flex-col items-center justify-center gap-3">
              <RefreshCw className="w-6 h-6 animate-spin text-primary" />
              <span className="text-sm">Evaluating deterministic routing policies...</span>
            </div>
          )}

          {error && (
            <div className="p-4 rounded-xl border border-rose-500/20 bg-rose-500/10 text-rose-400 text-sm">
              {error}
            </div>
          )}

          {preview && !loading && (
            <>
              {/* Selected Target */}
              <div className="p-6 rounded-2xl border border-primary/30 bg-primary/5 space-y-4 shadow-sm">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold uppercase tracking-wider text-primary">
                    Optimal Selected Model
                  </span>
                  <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                    <CheckCircle className="w-3.5 h-3.5" />
                    Policy Compliant
                  </span>
                </div>

                <div className="flex flex-col sm:flex-row sm:items-baseline justify-between gap-2">
                  <div>
                    <h3 className="text-2xl font-bold tracking-tight text-foreground">
                      {preview.display_name}
                    </h3>
                    <p className="text-xs font-mono text-muted-foreground mt-0.5">
                      {preview.selected_provider} / {preview.selected_model}
                    </p>
                  </div>
                </div>

                <div className="p-3.5 rounded-xl bg-background/60 border border-border/40 text-xs text-muted-foreground">
                  <span className="font-semibold text-foreground">Routing Rationale: </span>
                  {preview.routing_reason}
                </div>

                {preview.satisfied_requirements?.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 pt-1">
                    {preview.satisfied_requirements.map((req, idx) => (
                      <span
                        key={idx}
                        className="inline-flex items-center px-2 py-0.5 rounded-md text-[11px] font-medium bg-muted text-foreground border border-border/40"
                      >
                        ✓ {req}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {/* Fallback Sequence */}
              <div className="p-6 rounded-2xl border border-border/60 bg-card space-y-4 shadow-sm">
                <h3 className="font-semibold text-base flex items-center gap-2">
                  <Cpu className="w-4 h-4 text-amber-500" />
                  Deterministic Fallback Sequence
                </h3>
                <p className="text-xs text-muted-foreground">
                  If the primary model encounters a transient rate limit, timeout, or network error, the AI Gateway will transition through this sequence:
                </p>

                {preview.fallback_candidates?.length === 0 ? (
                  <div className="p-4 rounded-xl bg-muted/20 border border-border/30 text-xs text-muted-foreground text-center">
                    No compatible fallback candidate available matching all hard capability constraints.
                  </div>
                ) : (
                  <div className="space-y-3">
                    {preview.fallback_candidates.map((fb, idx) => (
                      <div
                        key={fb.model_id}
                        className="p-3.5 rounded-xl border border-border/40 bg-muted/20 flex items-center justify-between gap-4"
                      >
                        <div className="flex items-center gap-3">
                          <span className="w-6 h-6 rounded-full bg-muted flex items-center justify-center text-xs font-bold text-muted-foreground">
                            {idx + 1}
                          </span>
                          <div>
                            <div className="font-medium text-sm text-foreground">{fb.display_name}</div>
                            <div className="text-xs font-mono text-muted-foreground">
                              {fb.provider} / {fb.model_id}
                            </div>
                          </div>
                        </div>
                        <span className="text-xs text-muted-foreground text-right">{fb.reason}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
