"use client";

import React, { useState, useEffect, useCallback, use } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  GitCompare,
  ArrowLeft,
  RefreshCw,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Sparkles,
  Clock,
  Coins,
  Cpu,
  Database,
  Layers,
  ShieldCheck,
  Workflow,
  Wrench,
  Info,
  Check,
  FileText,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { replayService } from "@/services/replay";

export default function ReplayComparePage({ params: paramsProp }) {
  const router = useRouter();
  const routeParams = useParams();
  const replayId = routeParams?.replayId || (paramsProp ? use(paramsProp)?.replayId : null);

  const [comparison, setComparison] = useState(null);
  const [replay, setReplay] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadComparison = useCallback(async () => {
    if (!replayId) return;
    try {
      setIsLoading(true);
      setError(null);
      const [compRes, replayRes] = await Promise.all([
        replayService.compareReplay(replayId),
        replayService.getReplay(replayId),
      ]);
      setComparison(compRes);
      setReplay(replayRes);
    } catch (err) {
      console.error("[ReplayCompare] Failed to load comparison:", err);
      setError(err.message || "Failed to load execution comparison.");
    } finally {
      setIsLoading(false);
    }
  }, [replayId]);

  useEffect(() => {
    loadComparison();
  }, [loadComparison]);

  if (isLoading) {
    return (
      <div className="p-12 text-center text-xs font-mono text-slate-500">
        <RefreshCw className="w-5 h-5 mx-auto mb-2 animate-spin text-slate-400" />
        Calculating factual execution diffs...
      </div>
    );
  }

  if (error || !comparison) {
    return (
      <div className="p-8 max-w-2xl mx-auto text-center space-y-4">
        <AlertCircle className="w-10 h-10 text-rose-400 mx-auto" />
        <h2 className="text-lg font-bold text-white">Comparison Failed</h2>
        <p className="text-xs text-slate-400 font-mono">{error || "Could not calculate run diffs."}</p>
        <Button variant="outline" size="sm" onClick={() => router.push(`/app/replays/${replayId}`)}>
          <ArrowLeft className="w-4 h-4 mr-1.5" /> Return to Replay Console
        </Button>
      </div>
    );
  }

  const outDiff = comparison.output_diff || {};
  const modelDiff = comparison.model_diff || {};
  const usageDiff = comparison.usage_diff || {};
  const ctxDiff = comparison.context_diff || {};
  const evalDiff = comparison.evaluation_diff || {};
  const toolDiff = comparison.tool_diff || {};
  const detInfo = comparison.determinism_indicators || {};

  const tokensDelta = usageDiff.tokens_delta ?? usageDiff.tokens?.total_difference ?? 0;
  const latencyDelta = usageDiff.duration_ms_delta ?? usageDiff.latency_ms?.latency_difference_ms ?? 0;
  const costDelta = usageDiff.cost_delta ?? usageDiff.cost?.cost_difference ?? 0;

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Top Header & Breadcrumbs */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="xs"
              onClick={() => router.push(`/app/replays/${replayId}`)}
              className="text-slate-400 hover:text-white"
            >
              <ArrowLeft className="w-4 h-4 mr-1" />
              Console
            </Button>
            <span className="text-slate-600">/</span>
            <span className="text-xs font-mono text-indigo-400">Diff Comparison</span>
          </div>

          <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2 pt-1">
            <GitCompare className="w-5 h-5 text-indigo-400" />
            Execution Comparison &amp; Diff
          </h1>
          <p className="text-xs text-slate-400">
            Factual discrepancies between Original Run ({comparison.original_run_id?.slice(0, 8)}...) and Replay Run ({comparison.replay_id?.slice(0, 8)}...).
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={loadComparison} disabled={isLoading} className="text-xs">
            <RefreshCw className={`w-3.5 h-3.5 mr-1.5 ${isLoading ? "animate-spin" : ""}`} />
            Recalculate
          </Button>
          <Link href={`/app/replays/${replayId}`}>
            <Button size="sm" variant="outline" className="text-xs">
              View Console
            </Button>
          </Link>
        </div>
      </div>

      {/* Determinism & Reproducibility Notice */}
      <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 text-xs space-y-2">
        <div className="flex items-center gap-2 text-amber-300 font-semibold">
          <Info className="w-4 h-4 text-amber-400" />
          <span>Factual Reproducibility Notice</span>
        </div>
        <p className="text-slate-300 leading-relaxed">
          {detInfo.notice || "Replay may differ from the original because model responses, external data, and provider behavior can change over time."}
        </p>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2 text-[11px] font-mono">
          <div className="p-2 rounded bg-slate-950 border border-slate-800 flex items-center justify-between">
            <span className="text-slate-400">Same Model:</span>
            <span className={detInfo.same_model ? "text-emerald-400" : "text-amber-400"}>
              {detInfo.same_model ? "Yes" : "No (Changed)"}
            </span>
          </div>
          <div className="p-2 rounded bg-slate-950 border border-slate-800 flex items-center justify-between">
            <span className="text-slate-400">Same Workflow:</span>
            <span className={detInfo.same_workflow_version ? "text-emerald-400" : "text-amber-400"}>
              {detInfo.same_workflow_version ? "Yes" : "Modified"}
            </span>
          </div>
          <div className="p-2 rounded bg-slate-950 border border-slate-800 flex items-center justify-between">
            <span className="text-slate-400">Same Retrieval:</span>
            <span className={detInfo.same_retrieval_configuration ? "text-emerald-400" : "text-amber-400"}>
              {detInfo.same_retrieval_configuration ? "Yes" : "Modified"}
            </span>
          </div>
          <div className="p-2 rounded bg-slate-950 border border-slate-800 flex items-center justify-between">
            <span className="text-slate-400">Same Tools:</span>
            <span className={detInfo.same_tool_configuration ? "text-emerald-400" : "text-amber-400"}>
              {detInfo.same_tool_configuration ? "Yes" : "Modified"}
            </span>
          </div>
        </div>
      </div>

      {/* Delta Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
          <span className="text-[10px] uppercase font-semibold text-slate-400 block tracking-wider">
            Output Match
          </span>
          <div className="flex items-center gap-2 mt-1">
            <span className="text-base font-bold font-mono text-white">
              {outDiff.exact_match ? "Identical" : `${Math.round((outDiff.similarity_ratio || 0) * 100)}% Similar`}
            </span>
            <Badge variant={outDiff.exact_match ? "success" : "outline"} className="text-[10px]">
              {outDiff.exact_match ? "Exact" : "Diverged"}
            </Badge>
          </div>
          <span className="text-[10px] text-slate-500 font-mono block mt-1">
            Length delta: {outDiff.length_difference > 0 ? `+${outDiff.length_difference}` : outDiff.length_difference} chars
          </span>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
          <span className="text-[10px] uppercase font-semibold text-slate-400 block tracking-wider">
            Token Usage Delta
          </span>
          <div className="flex items-baseline gap-2 mt-1">
            <span className={`text-base font-bold font-mono ${tokensDelta > 0 ? "text-amber-400" : tokensDelta < 0 ? "text-emerald-400" : "text-slate-200"}`}>
              {tokensDelta > 0 ? `+${tokensDelta}` : tokensDelta}
            </span>
            <span className="text-xs font-mono text-slate-500">tokens</span>
          </div>
          <span className="text-[10px] text-slate-500 font-mono block mt-1">
            Total tokens: {usageDiff.tokens?.replay_total ?? "—"}
          </span>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
          <span className="text-[10px] uppercase font-semibold text-slate-400 block tracking-wider">
            Latency Delta
          </span>
          <div className="flex items-baseline gap-2 mt-1">
            <span className={`text-base font-bold font-mono ${latencyDelta > 0 ? "text-amber-400" : latencyDelta < 0 ? "text-emerald-400" : "text-slate-200"}`}>
              {latencyDelta > 0 ? `+${latencyDelta}` : latencyDelta} ms
            </span>
          </div>
          <span className="text-[10px] text-slate-500 font-mono block mt-1">
            Replay duration: {usageDiff.latency_ms?.replay_latency_ms ?? "—"} ms
          </span>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
          <span className="text-[10px] uppercase font-semibold text-slate-400 block tracking-wider">
            Estimated Cost Delta
          </span>
          <div className="flex items-baseline gap-2 mt-1">
            <span className="text-base font-bold font-mono text-white">
              ${costDelta > 0 ? `+${costDelta.toFixed(5)}` : costDelta.toFixed(5)}
            </span>
          </div>
          <span className="text-[10px] text-slate-500 font-mono block mt-1">
            Replay cost: ${(usageDiff.cost?.replay_cost || 0).toFixed(5)}
          </span>
        </div>
      </div>

      {/* 1. Output Difference Section */}
      <Card className="bg-slate-900/60 border-slate-800">
        <CardHeader className="p-4 border-b border-slate-800 flex flex-row items-center justify-between">
          <div>
            <CardTitle className="text-sm flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-cyan-400" />
              Output Text Difference
            </CardTitle>
            <CardDescription className="text-xs">
              Factual line-by-line additions and removals compared to the original execution output.
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-emerald-950/60 text-emerald-400 border border-emerald-800">
              +{outDiff.additions_count || 0} additions
            </span>
            <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-rose-950/60 text-rose-400 border border-rose-800">
              -{outDiff.removals_count || 0} removals
            </span>
          </div>
        </CardHeader>
        <CardContent className="p-4 space-y-3">
          {outDiff.exact_match ? (
            <div className="p-4 rounded-lg bg-emerald-950/20 border border-emerald-800/40 text-xs text-emerald-300 flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4" />
              <span>Outputs are factually identical. No text divergence detected.</span>
            </div>
          ) : (
            <div className="space-y-2">
              {outDiff.removals_sample?.length > 0 && (
                <div className="space-y-1">
                  <span className="text-[11px] font-semibold text-rose-400 block font-mono">
                    Original Lines Removed or Altered:
                  </span>
                  <div className="p-3 bg-rose-950/30 border border-rose-900/50 rounded-lg text-xs font-mono text-rose-200/90 whitespace-pre-wrap space-y-0.5">
                    {outDiff.removals_sample.map((line, i) => (
                      <div key={i} className="flex items-start gap-2">
                        <span className="text-rose-500 select-none">-</span>
                        <span>{line}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {outDiff.additions_sample?.length > 0 && (
                <div className="space-y-1">
                  <span className="text-[11px] font-semibold text-emerald-400 block font-mono">
                    Replay Lines Added or Modified:
                  </span>
                  <div className="p-3 bg-emerald-950/30 border border-emerald-900/50 rounded-lg text-xs font-mono text-emerald-200/90 whitespace-pre-wrap space-y-0.5">
                    {outDiff.additions_sample.map((line, i) => (
                      <div key={i} className="flex items-start gap-2">
                        <span className="text-emerald-500 select-none">+</span>
                        <span>{line}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* 2. Model & Generation Difference */}
      <Card className="bg-slate-900/60 border-slate-800">
        <CardHeader className="p-4 border-b border-slate-800">
          <CardTitle className="text-sm flex items-center gap-2">
            <Cpu className="w-4 h-4 text-indigo-400" />
            Model &amp; Provider Comparison
          </CardTitle>
        </CardHeader>
        <CardContent className="p-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs font-mono">
            <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 space-y-1.5">
              <span className="text-[10px] text-slate-500 uppercase font-semibold block">Original Execution</span>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Model:</span>
                <span className="text-white font-bold">{modelDiff.original_model || "gpt-4o-mini"}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Provider:</span>
                <span className="text-slate-300">{modelDiff.original_provider || "openai"}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Temperature:</span>
                <span className="text-slate-300">{modelDiff.temperature_original ?? 0.2}</span>
              </div>
            </div>

            <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 space-y-1.5">
              <span className="text-[10px] text-slate-500 uppercase font-semibold block">Replay Execution</span>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Model:</span>
                <span className={modelDiff.same_model ? "text-emerald-400 font-bold" : "text-amber-400 font-bold"}>
                  {modelDiff.replay_model || modelDiff.original_model || "gpt-4o-mini"}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Provider:</span>
                <span className="text-slate-300">{modelDiff.replay_provider || modelDiff.original_provider || "openai"}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Temperature:</span>
                <span className="text-slate-300">{modelDiff.temperature_replay ?? 0.2}</span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 3. Context & Knowledge Difference */}
      <Card className="bg-slate-900/60 border-slate-800">
        <CardHeader className="p-4 border-b border-slate-800">
          <CardTitle className="text-sm flex items-center gap-2">
            <Database className="w-4 h-4 text-purple-400" />
            Context &amp; Retrieval Source Differences
          </CardTitle>
          <CardDescription className="text-xs">
            Documents and knowledge chunks assembled for prompt context in both runs.
          </CardDescription>
        </CardHeader>
        <CardContent className="p-4 space-y-3 text-xs">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-1">
              <span className="text-slate-400 font-semibold font-mono text-[11px] block">
                Sources Added in Replay ({ctxDiff.sources_added?.length || 0}):
              </span>
              {ctxDiff.sources_added?.length > 0 ? (
                <div className="p-2.5 rounded bg-slate-950 border border-slate-800 font-mono text-[11px] text-emerald-300 space-y-1">
                  {ctxDiff.sources_added.map((src, i) => (
                    <div key={i} className="truncate">+ {src}</div>
                  ))}
                </div>
              ) : (
                <div className="p-2.5 rounded bg-slate-950 border border-slate-800 text-slate-500 font-mono text-[11px]">
                  No new context sources added.
                </div>
              )}
            </div>

            <div className="space-y-1">
              <span className="text-slate-400 font-semibold font-mono text-[11px] block">
                Sources Removed in Replay ({ctxDiff.sources_removed?.length || 0}):
              </span>
              {ctxDiff.sources_removed?.length > 0 ? (
                <div className="p-2.5 rounded bg-slate-950 border border-slate-800 font-mono text-[11px] text-rose-300 space-y-1">
                  {ctxDiff.sources_removed.map((src, i) => (
                    <div key={i} className="truncate">- {src}</div>
                  ))}
                </div>
              ) : (
                <div className="p-2.5 rounded bg-slate-950 border border-slate-800 text-slate-500 font-mono text-[11px]">
                  No original context sources omitted.
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 4. Evaluation Difference */}
      <Card className="bg-slate-900/60 border-slate-800">
        <CardHeader className="p-4 border-b border-slate-800">
          <CardTitle className="text-sm flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            Evaluation &amp; Verification Findings Diff
          </CardTitle>
        </CardHeader>
        <CardContent className="p-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs font-mono">
            <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 space-y-1">
              <span className="text-[10px] text-slate-500 uppercase font-semibold block">Original Evaluation</span>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Status:</span>
                <span className="text-white font-bold">{evalDiff.original_status || "Passed"}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Mode:</span>
                <span className="text-slate-300">{evalDiff.original_mode || "Standard"}</span>
              </div>
            </div>

            <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 space-y-1">
              <span className="text-[10px] text-slate-500 uppercase font-semibold block">Replay Evaluation</span>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Status:</span>
                <span className={evalDiff.status_match ? "text-emerald-400 font-bold" : "text-amber-400 font-bold"}>
                  {evalDiff.replay_status || "Passed"}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Status Match:</span>
                <span className={evalDiff.status_match ? "text-emerald-400" : "text-amber-400"}>
                  {evalDiff.status_match ? "Matched" : "Diverged"}
                </span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 5. Tool Usage & Side Effects Difference */}
      <Card className="bg-slate-900/60 border-slate-800">
        <CardHeader className="p-4 border-b border-slate-800">
          <CardTitle className="text-sm flex items-center gap-2">
            <Wrench className="w-4 h-4 text-amber-400" />
            Tool Executions &amp; Side-Effect Policy Diff
          </CardTitle>
        </CardHeader>
        <CardContent className="p-4 space-y-2 text-xs font-mono">
          <div className="flex items-center justify-between p-2.5 rounded bg-slate-950 border border-slate-800">
            <span className="text-slate-400">Side Effects Blocked / Simulated Safely:</span>
            <span className="text-emerald-400 font-bold">{toolDiff.side_effects_blocked_count ?? 1}</span>
          </div>
          <div className="flex items-center justify-between p-2.5 rounded bg-slate-950 border border-slate-800">
            <span className="text-slate-400">Original Tool Call Count:</span>
            <span className="text-white">{toolDiff.original_call_count ?? 0}</span>
          </div>
          <div className="flex items-center justify-between p-2.5 rounded bg-slate-950 border border-slate-800">
            <span className="text-slate-400">Replay Tool Call Count:</span>
            <span className="text-white">{toolDiff.replay_call_count ?? 0}</span>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
