"use client";

import React, { useState, useEffect, useCallback, use } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  RotateCcw,
  ArrowLeft,
  RefreshCw,
  CheckCircle2,
  XCircle,
  AlertCircle,
  AlertTriangle,
  Play,
  Copy,
  Check,
  ExternalLink,
  ShieldAlert,
  ShieldCheck,
  Clock,
  Coins,
  Cpu,
  Database,
  Layers,
  Sparkles,
  Workflow,
  Wrench,
  SlidersHorizontal,
  FileCode,
  GitCompare,
  Terminal,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { replayService } from "@/services/replay";
import { runService } from "@/services/runs";
import { formatDate } from "@/lib/utils";

export default function ReplayConsolePage({ params: paramsProp }) {
  const router = useRouter();
  const routeParams = useParams();
  const replayId = routeParams?.replayId || (paramsProp ? use(paramsProp)?.replayId : null);

  const [replay, setReplay] = useState(null);
  const [originalRun, setOriginalRun] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [copiedId, setCopiedId] = useState(false);

  // Replay actions state
  const [actionLoading, setActionLoading] = useState(false);
  const [actionMessage, setActionMessage] = useState(null);
  const [showConfirmModal, setShowConfirmModal] = useState(false);

  // Overrides editor state
  const [showOverridesEditor, setShowOverridesEditor] = useState(false);
  const [overrides, setOverrides] = useState({
    model: "",
    temperature: 0.2,
    planner_mode: "hybrid",
    retrieval_strategy: "hybrid",
    retrieval_top_k: 8,
    evaluation_mode: "standard",
  });

  // Step replay state
  const [replayingStepId, setReplayingStepId] = useState(null);
  const [stepResult, setStepResult] = useState(null);

  const loadReplayData = useCallback(async () => {
    if (!replayId) return;
    try {
      setIsLoading(true);
      setError(null);

      const replayData = await replayService.getReplay(replayId);
      setReplay(replayData);

      if (replayData?.original_run_id) {
        try {
          const runData = await runService.getRun(replayData.original_run_id);
          setOriginalRun(runData);
        } catch {
          // If original run cannot be loaded directly, snapshot contains fallback metadata
        }
      }

      // Initialize overrides from replay metadata if present
      if (replayData?.metadata?.overrides) {
        setOverrides((prev) => ({ ...prev, ...replayData.metadata.overrides }));
      }
    } catch (err) {
      console.error("[ReplayConsole] Failed to load replay details:", err);
      setError(err.message || "Failed to load replay console.");
    } finally {
      setIsLoading(false);
    }
  }, [replayId]);

  useEffect(() => {
    loadReplayData();
  }, [loadReplayData]);

  const copyId = (id) => {
    navigator.clipboard.writeText(id);
    setCopiedId(true);
    setTimeout(() => setCopiedId(false), 2000);
  };

  const handleDryRunAgain = async () => {
    if (!replay?.original_run_id) return;
    try {
      setActionLoading(true);
      setActionMessage(null);
      const newReplay = await replayService.dryRunReplay(replay.original_run_id, overrides);
      router.push(`/app/replays/${newReplay.id}`);
    } catch (err) {
      setActionMessage({ type: "error", text: err.message || "Dry-run failed." });
    } finally {
      setActionLoading(false);
    }
  };

  const handleExecuteLiveReplay = async () => {
    setShowConfirmModal(false);
    if (!replay?.original_run_id) return;
    try {
      setActionLoading(true);
      setActionMessage(null);
      const newReplay = await replayService.executeReplay(replay.original_run_id, {
        overrides,
        dryRun: false,
      });
      router.push(`/app/replays/${newReplay.id}`);
    } catch (err) {
      setActionMessage({ type: "error", text: err.message || "Live replay execution failed." });
    } finally {
      setActionLoading(false);
    }
  };

  const handleCancelReplay = async () => {
    try {
      setActionLoading(true);
      const updated = await replayService.cancelReplay(replayId);
      setReplay(updated);
      setActionMessage({ type: "info", text: "Replay cancelled cooperatively." });
    } catch (err) {
      setActionMessage({ type: "error", text: err.message || "Failed to cancel replay." });
    } finally {
      setActionLoading(false);
    }
  };

  const handleReplayStep = async (stepId) => {
    if (!replay?.original_run_id) return;
    try {
      setReplayingStepId(stepId);
      setStepResult(null);
      const res = await replayService.replayStep(replay.original_run_id, stepId, {
        dryRun: true,
        overrides,
      });
      setStepResult({ stepId, ...res });
    } catch (err) {
      setStepResult({ stepId, error: err.message });
    } finally {
      setReplayingStepId(null);
    }
  };

  if (isLoading) {
    return (
      <div className="p-12 text-center text-xs font-mono text-slate-500">
        <RefreshCw className="w-5 h-5 mx-auto mb-2 animate-spin text-slate-400" />
        Loading replay session...
      </div>
    );
  }

  if (error || !replay) {
    return (
      <div className="p-8 max-w-2xl mx-auto text-center space-y-4">
        <AlertCircle className="w-10 h-10 text-rose-400 mx-auto" />
        <h2 className="text-lg font-bold text-white">Replay Session Not Found</h2>
        <p className="text-xs text-slate-400 font-mono">{error || "The requested replay does not exist in your workspace."}</p>
        <Button variant="outline" size="sm" onClick={() => router.push("/app/replays")}>
          <ArrowLeft className="w-4 h-4 mr-1.5" /> Return to Replays
        </Button>
      </div>
    );
  }

  const meta = replay.metadata || {};
  const isModified = !!meta.modified_replay;
  const isRunning = replay.status === "running";
  const steps = replay.execution_steps || originalRun?.execution_steps || [];
  const snapshot = replay.snapshot || {};

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Top Header & Breadcrumbs */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="xs"
              onClick={() => router.push("/app/replays")}
              className="text-slate-400 hover:text-white"
            >
              <ArrowLeft className="w-4 h-4 mr-1" />
              Replays
            </Button>
            <span className="text-slate-600">/</span>
            <span className="text-xs font-mono text-indigo-400">Console</span>
          </div>

          <div className="flex flex-wrap items-center gap-2.5 pt-1">
            <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
              Replay Console
            </h1>

            <Badge
              variant={
                replay.status === "completed"
                  ? "success"
                  : replay.status === "running"
                  ? "warning"
                  : replay.status === "failed"
                  ? "destructive"
                  : "outline"
              }
              className="text-xs font-mono uppercase"
            >
              {replay.status}
            </Badge>

            <span className="px-2 py-0.5 rounded text-[11px] font-mono border font-medium bg-blue-950/60 text-blue-300 border-blue-800">
              Mode: {replay.replay_mode}
            </span>

            {replay.dry_run && (
              <span className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-emerald-950/50 text-emerald-400 border border-emerald-800">
                DRY-RUN (SAFE)
              </span>
            )}

            {isModified && (
              <span className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-amber-950/60 text-amber-300 border border-amber-800">
                Modified Replay
              </span>
            )}
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-wrap items-center gap-2">
          <Link href={`/app/runs/${replay.original_run_id}`}>
            <Button variant="outline" size="sm" className="text-xs">
              <ExternalLink className="w-3.5 h-3.5 mr-1 text-slate-400" />
              Inspect Original Run
            </Button>
          </Link>

          <Button
            variant="outline"
            size="sm"
            onClick={() => router.push(`/app/replays/${replay.id}/compare`)}
            className="text-xs text-indigo-300 border-indigo-700/50 hover:bg-indigo-950"
          >
            <GitCompare className="w-3.5 h-3.5 mr-1 text-indigo-400" />
            Compare Diff
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowOverridesEditor(!showOverridesEditor)}
            className="text-xs"
          >
            <SlidersHorizontal className="w-3.5 h-3.5 mr-1 text-slate-400" />
            {showOverridesEditor ? "Hide Config" : "Edit Config"}
          </Button>

          {isRunning ? (
            <Button
              variant="destructive"
              size="sm"
              onClick={handleCancelReplay}
              disabled={actionLoading}
              className="text-xs"
            >
              Cancel Replay
            </Button>
          ) : (
            <>
              <Button
                variant="outline"
                size="sm"
                onClick={handleDryRunAgain}
                disabled={actionLoading}
                className="text-xs"
              >
                <RefreshCw className={`w-3.5 h-3.5 mr-1 ${actionLoading ? "animate-spin" : ""}`} />
                Dry Run Again
              </Button>

              <Button
                size="sm"
                onClick={() => setShowConfirmModal(true)}
                disabled={actionLoading}
                className="bg-indigo-600 hover:bg-indigo-500 text-xs font-semibold"
              >
                <Play className="w-3.5 h-3.5 mr-1" />
                Live Replay
              </Button>
            </>
          )}
        </div>
      </div>

      {/* Safety Notice */}
      <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 text-xs text-slate-300 flex items-start gap-2.5">
        <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold text-white">Side-Effect Isolation Active:</span> External writes (e.g. GitHub issues, database writes) are disabled by default. If a step attempts an external side effect, it simulates the operation safely. For real side effects, a fresh human approval is strictly required.
        </div>
      </div>

      {actionMessage && (
        <div
          className={`p-3 rounded-lg text-xs font-mono border ${
            actionMessage.type === "error"
              ? "bg-rose-950/60 border-rose-800 text-rose-300"
              : "bg-blue-950/60 border-blue-800 text-blue-300"
          }`}
        >
          {actionMessage.text}
        </div>
      )}

      {/* Safe Configuration Overrides Editor */}
      {showOverridesEditor && (
        <Card className="bg-slate-900/90 border-indigo-700/40">
          <CardHeader className="p-4 border-b border-slate-800">
            <CardTitle className="text-sm flex items-center gap-2 text-indigo-300">
              <SlidersHorizontal className="w-4 h-4 text-indigo-400" />
              Safe Replay Configuration Editor
            </CardTitle>
            <CardDescription className="text-xs">
              Safely adjust execution parameters without modifying security policies, workspace boundaries, or original run state.
            </CardDescription>
          </CardHeader>
          <CardContent className="p-4 space-y-4 text-xs">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <label className="block text-slate-400 font-medium mb-1">Target Model</label>
                <input
                  type="text"
                  placeholder="e.g. gpt-4o-mini"
                  value={overrides.model}
                  onChange={(e) => setOverrides({ ...overrides, model: e.target.value })}
                  className="w-full px-2.5 py-1.5 bg-slate-950 border border-slate-800 rounded text-xs text-white"
                />
              </div>

              <div>
                <label className="block text-slate-400 font-medium mb-1">Temperature ({overrides.temperature})</label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  value={overrides.temperature}
                  onChange={(e) => setOverrides({ ...overrides, temperature: parseFloat(e.target.value) })}
                  className="w-full accent-indigo-500"
                />
              </div>

              <div>
                <label className="block text-slate-400 font-medium mb-1">Planner Mode</label>
                <select
                  value={overrides.planner_mode}
                  onChange={(e) => setOverrides({ ...overrides, planner_mode: e.target.value })}
                  className="w-full px-2.5 py-1.5 bg-slate-950 border border-slate-800 rounded text-xs text-white"
                >
                  <option value="hybrid">Hybrid</option>
                  <option value="llm">LLM</option>
                  <option value="deterministic">Deterministic</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-400 font-medium mb-1">Retrieval Strategy</label>
                <select
                  value={overrides.retrieval_strategy}
                  onChange={(e) => setOverrides({ ...overrides, retrieval_strategy: e.target.value })}
                  className="w-full px-2.5 py-1.5 bg-slate-950 border border-slate-800 rounded text-xs text-white"
                >
                  <option value="hybrid">Hybrid (Vector + BM25)</option>
                  <option value="vector">Vector Only</option>
                  <option value="keyword">Keyword Only</option>
                  <option value="multi_query">Multi-Query</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-400 font-medium mb-1">Retrieval Top K</label>
                <input
                  type="number"
                  min="1"
                  max="25"
                  value={overrides.retrieval_top_k}
                  onChange={(e) => setOverrides({ ...overrides, retrieval_top_k: parseInt(e.target.value) || 5 })}
                  className="w-full px-2.5 py-1.5 bg-slate-950 border border-slate-800 rounded text-xs text-white"
                />
              </div>

              <div>
                <label className="block text-slate-400 font-medium mb-1">Evaluation Mode</label>
                <select
                  value={overrides.evaluation_mode}
                  onChange={(e) => setOverrides({ ...overrides, evaluation_mode: e.target.value })}
                  className="w-full px-2.5 py-1.5 bg-slate-950 border border-slate-800 rounded text-xs text-white"
                >
                  <option value="standard">Standard</option>
                  <option value="strict">Strict</option>
                  <option value="basic">Basic</option>
                  <option value="off">Disabled</option>
                </select>
              </div>
            </div>

            <div className="flex items-center justify-between pt-2 border-t border-slate-800">
              <span className="text-slate-500 font-mono text-[11px]">
                Replays launched with overrides are recorded as &quot;Modified Replay&quot;.
              </span>
              <Button size="xs" onClick={handleDryRunAgain} className="bg-indigo-600 hover:bg-indigo-500">
                Apply &amp; Dry Run
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Comparison Snapshot Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
          <span className="text-[10px] uppercase font-semibold text-slate-400 block tracking-wider">
            Duration
          </span>
          <div className="flex items-baseline gap-2 mt-1">
            <span className="text-lg font-bold font-mono text-white">
              {meta.duration_ms ?? "—"} ms
            </span>
            {originalRun?.latency_ms && (
              <span className="text-xs font-mono text-slate-500">
                (orig: {originalRun.latency_ms} ms)
              </span>
            )}
          </div>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
          <span className="text-[10px] uppercase font-semibold text-slate-400 block tracking-wider">
            Total Tokens
          </span>
          <div className="flex items-baseline gap-2 mt-1">
            <span className="text-lg font-bold font-mono text-cyan-300">
              {meta.token_usage?.total_tokens ?? originalRun?.total_tokens ?? "—"}
            </span>
            {originalRun?.total_tokens && (
              <span className="text-xs font-mono text-slate-500">
                (orig: {originalRun.total_tokens})
              </span>
            )}
          </div>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
          <span className="text-[10px] uppercase font-semibold text-slate-400 block tracking-wider">
            Target Model
          </span>
          <div className="mt-1">
            <span className="text-xs font-bold font-mono text-slate-200 block truncate">
              {meta.final_model || snapshot?.model_configuration?.model_name || originalRun?.model_name || "gpt-4o-mini"}
            </span>
            <span className="text-[10px] font-mono text-slate-500 block">
              Provider: {meta.model_provider || snapshot?.model_configuration?.model_provider || "openai"}
            </span>
          </div>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
          <span className="text-[10px] uppercase font-semibold text-slate-400 block tracking-wider">
            Blocked Side-Effects
          </span>
          <div className="mt-1 flex items-center gap-1.5">
            <span className="text-lg font-bold font-mono text-emerald-400">
              {meta.side_effects_blocked_count ?? (replay.dry_run ? 1 : 0)}
            </span>
            <span className="text-[10px] font-mono text-slate-500">
              simulated safely
            </span>
          </div>
        </div>
      </div>

      {/* Main Content Area: Replay Output vs Original Output */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Replay Output Card */}
        <Card className="bg-slate-900/60 border-slate-800">
          <CardHeader className="p-4 border-b border-slate-800 flex flex-row items-center justify-between">
            <div>
              <CardTitle className="text-sm flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-cyan-400" />
                Replay Generated Output
              </CardTitle>
              <CardDescription className="text-xs">
                Output generated during this replay execution.
              </CardDescription>
            </div>
            <Badge variant="outline" className="text-[10px] font-mono">
              {replay.replay_output ? `${replay.replay_output.length} chars` : "0 chars"}
            </Badge>
          </CardHeader>
          <CardContent className="p-4">
            {replay.replay_output ? (
              <div className="p-3 bg-slate-950 border border-slate-800 rounded-lg text-xs font-mono text-slate-200 whitespace-pre-wrap max-h-96 overflow-y-auto leading-relaxed">
                {replay.replay_output}
              </div>
            ) : (
              <div className="py-12 text-center text-xs text-slate-500 font-mono">
                No replay output content generated.
              </div>
            )}
          </CardContent>
        </Card>

        {/* Original Output Card */}
        <Card className="bg-slate-900/60 border-slate-800">
          <CardHeader className="p-4 border-b border-slate-800 flex flex-row items-center justify-between">
            <div>
              <CardTitle className="text-sm flex items-center gap-2">
                <Clock className="w-4 h-4 text-indigo-400" />
                Original Run Output
              </CardTitle>
              <CardDescription className="text-xs">
                Historical baseline output captured in snapshot.
              </CardDescription>
            </div>
            <Badge variant="outline" className="text-[10px] font-mono">
              {originalRun?.output_content ? `${originalRun.output_content.length} chars` : "Snapshot baseline"}
            </Badge>
          </CardHeader>
          <CardContent className="p-4">
            <div className="p-3 bg-slate-950 border border-slate-800 rounded-lg text-xs font-mono text-slate-300 whitespace-pre-wrap max-h-96 overflow-y-auto leading-relaxed">
              {originalRun?.output_content || snapshot?.task_configuration?.instructions || "Original baseline output available in snapshot."}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Execution Steps Inspector */}
      <Card className="bg-slate-900/60 border-slate-800">
        <CardHeader className="p-4 border-b border-slate-800">
          <CardTitle className="text-sm flex items-center gap-2">
            <Workflow className="w-4 h-4 text-indigo-400" />
            Execution Steps &amp; Step Replay ({steps.length})
          </CardTitle>
          <CardDescription className="text-xs">
            Inspect individual plan execution steps or safely replay an isolated step in dry-run mode.
          </CardDescription>
        </CardHeader>
        <CardContent className="p-4 space-y-3">
          {stepResult && (
            <div className="p-3 rounded-lg bg-indigo-950/50 border border-indigo-700/50 text-xs font-mono space-y-1">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-indigo-300">
                  Step Replay Result (#{stepResult.stepId}):
                </span>
                <button onClick={() => setStepResult(null)} className="text-slate-400 hover:text-white">
                  ✕
                </button>
              </div>
              <pre className="text-[11px] text-slate-300 whitespace-pre-wrap">
                {JSON.stringify(stepResult, null, 2)}
              </pre>
            </div>
          )}

          {steps.length === 0 ? (
            <div className="py-8 text-center text-xs text-slate-500 font-mono">
              No individual plan steps recorded for this execution.
            </div>
          ) : (
            <div className="space-y-2">
              {steps.map((st, idx) => {
                const sId = st.id || st.step_id || `step-${idx + 1}`;
                const sType = st.type || st.step_type || "operation";
                const isStepReplaying = replayingStepId === sId;

                return (
                  <div
                    key={sId}
                    className="p-3 bg-slate-950 border border-slate-800 rounded-lg flex items-center justify-between text-xs"
                  >
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-slate-400 text-[10px] px-1.5 py-0.5 rounded bg-slate-900 border border-slate-800">
                          #{idx + 1}
                        </span>
                        <span className="font-semibold text-white font-mono">{sId}</span>
                        <Badge variant="outline" className="text-[10px] capitalize">
                          {sType}
                        </Badge>
                        {st.tool && (
                          <span className="text-[11px] font-mono text-emerald-400">
                            tool: {st.tool}
                          </span>
                        )}
                      </div>
                      <p className="text-[11px] text-slate-400">
                        {st.description || st.title || "Plan execution step"}
                      </p>
                    </div>

                    <Button
                      variant="ghost"
                      size="xs"
                      onClick={() => handleReplayStep(sId)}
                      disabled={isStepReplaying}
                      className="text-indigo-400 hover:text-indigo-300 text-xs"
                    >
                      {isStepReplaying ? (
                        <RefreshCw className="w-3 h-3 animate-spin mr-1" />
                      ) : (
                        <Play className="w-3 h-3 mr-1" />
                      )}
                      Replay Step
                    </Button>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Snapshot Metadata Viewer */}
      <Card className="bg-slate-900/60 border-slate-800">
        <CardHeader className="p-4 border-b border-slate-800">
          <CardTitle className="text-sm flex items-center gap-2">
            <FileCode className="w-4 h-4 text-purple-400" />
            Sanitized Execution Snapshot Metadata
          </CardTitle>
          <CardDescription className="text-xs">
            Complete, deterministic snapshot captured for this replay. Zero secrets, tokens, or private credentials persisted.
          </CardDescription>
        </CardHeader>
        <CardContent className="p-4">
          <pre className="p-3 bg-slate-950 border border-slate-800 rounded-lg text-[11px] font-mono text-slate-300 max-h-72 overflow-y-auto">
            {JSON.stringify(snapshot, null, 2)}
          </pre>
        </CardContent>
      </Card>

      {/* Confirmation Modal for Live Replay */}
      {showConfirmModal && (
        <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-md w-full p-6 space-y-4 shadow-xl">
            <div className="flex items-center gap-3 text-amber-400">
              <AlertTriangle className="w-6 h-6 shrink-0" />
              <h3 className="text-base font-bold text-white">Confirm Live Replay Execution</h3>
            </div>

            <p className="text-xs text-slate-300 leading-relaxed">
              This action will re-execute AI model computation via the active AI Gateway providers.
            </p>

            <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 text-[11px] text-slate-400 space-y-1">
              <div className="flex items-center gap-1.5 text-amber-300 font-semibold">
                <ShieldAlert className="w-3.5 h-3.5" />
                <span>Notice:</span>
              </div>
              <p>• External writes and mutations remain dry-run by default unless approved fresh.</p>
              <p>• This action may consume AI provider tokens.</p>
              <p>• Original historical runs are never altered.</p>
            </div>

            <div className="flex items-center justify-end gap-2 pt-2">
              <Button variant="ghost" size="sm" onClick={() => setShowConfirmModal(false)} className="text-xs">
                Cancel
              </Button>
              <Button size="sm" onClick={handleExecuteLiveReplay} className="bg-indigo-600 hover:bg-indigo-500 text-xs font-semibold">
                Confirm &amp; Replay
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
