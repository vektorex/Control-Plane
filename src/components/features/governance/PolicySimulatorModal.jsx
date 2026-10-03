"use client";

import React, { useState } from "react";
import { X, Play, ShieldAlert, ShieldCheck, AlertTriangle, CheckCircle, Clock, Cpu } from "lucide-react";
import { cn } from "@/lib/utils";
import { governanceService } from "@/services/governance";

export function PolicySimulatorModal({
  isOpen,
  onClose,
  workspaceId,
  policyToSimulate = null,
}) {
  const [enforcementPoint, setEnforcementPoint] = useState("task_execution");
  const [modelId, setModelId] = useState("gpt-4o");
  const [provider, setProvider] = useState("openai");
  const [taskType, setTaskType] = useState("general");
  const [tools, setTools] = useState("");
  const [prompt, setPrompt] = useState("Explain quantum entanglement");
  const [classification, setClassification] = useState("internal");
  const [simulating, setSimulating] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  if (!isOpen) return null;

  const handleSimulate = async () => {
    setSimulating(true);
    setError(null);
    setResult(null);
    try {
      const toolList = tools ? tools.split(",").map((t) => t.trim()).filter(Boolean) : [];
      const simReq = {
        evaluation: {
          enforcement_point: enforcementPoint,
          workspace_id: workspaceId,
          model_id: modelId,
          model_provider: provider,
          task_type: taskType,
          requested_tools: toolList,
          parameters: { prompt },
          data_classification: classification,
        },
      };
      const res = await governanceService.simulate(simReq);
      setResult(res);
    } catch (err) {
      setError(err?.message || "Simulation failed");
    } finally {
      setSimulating(false);
    }
  };

  const decision = result?.decision?.decision;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm overflow-y-auto">
      <div className="relative w-full max-w-2xl rounded-xl bg-slate-900 border border-slate-800 shadow-2xl p-6 text-xs text-slate-200">
        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-indigo-500/10 flex items-center justify-center text-indigo-400 border border-indigo-500/20">
              <Play className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-white">Policy Decision Simulator</h2>
              <p className="text-[11px] text-slate-400">
                Dry-run governance evaluation without creating side effects or executing tasks.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {error && (
          <div className="mt-4 p-3 rounded-lg bg-rose-950/50 border border-rose-800/60 text-rose-300">
            {error}
          </div>
        )}

        <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <label className="block text-[10px] font-semibold text-slate-400 uppercase mb-1">
              Enforcement Point
            </label>
            <select
              value={enforcementPoint}
              onChange={(e) => setEnforcementPoint(e.target.value)}
              className="w-full px-2.5 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-slate-100 text-xs"
            >
              <option value="task_execution">Task Execution</option>
              <option value="orchestration_dispatch">Orchestration Dispatch</option>
              <option value="model_invocation">Model Invocation</option>
              <option value="tool_execution">Tool Execution</option>
              <option value="connector_call">Connector Call</option>
              <option value="workflow_step">Workflow Step</option>
              <option value="cache_read">Cache Read</option>
              <option value="cache_write">Cache Write</option>
            </select>
          </div>

          <div>
            <label className="block text-[10px] font-semibold text-slate-400 uppercase mb-1">
              Target Model
            </label>
            <input
              type="text"
              value={modelId}
              onChange={(e) => setModelId(e.target.value)}
              placeholder="e.g. gpt-4o, claude-3-5-sonnet"
              className="w-full px-2.5 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-slate-100 text-xs font-mono"
            />
          </div>

          <div>
            <label className="block text-[10px] font-semibold text-slate-400 uppercase mb-1">
              Model Provider
            </label>
            <input
              type="text"
              value={provider}
              onChange={(e) => setProvider(e.target.value)}
              placeholder="openai, anthropic, google"
              className="w-full px-2.5 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-slate-100 text-xs"
            />
          </div>

          <div>
            <label className="block text-[10px] font-semibold text-slate-400 uppercase mb-1">
              Data Classification
            </label>
            <select
              value={classification}
              onChange={(e) => setClassification(e.target.value)}
              className="w-full px-2.5 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-slate-100 text-xs"
            >
              <option value="public">Public</option>
              <option value="internal">Internal</option>
              <option value="confidential">Confidential</option>
              <option value="restricted">Restricted (PHI/PII/Financial)</option>
            </select>
          </div>
        </div>

        <div className="mt-3">
          <label className="block text-[10px] font-semibold text-slate-400 uppercase mb-1">
            Requested Tools (comma separated)
          </label>
          <input
            type="text"
            value={tools}
            onChange={(e) => setTools(e.target.value)}
            placeholder="e.g. bash_execution, file_delete, send_slack_message"
            className="w-full px-2.5 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-slate-100 text-xs font-mono"
          />
        </div>

        <div className="mt-3">
          <label className="block text-[10px] font-semibold text-slate-400 uppercase mb-1">
            Prompt / Intent Text
          </label>
          <textarea
            rows={2}
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            className="w-full px-2.5 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-slate-100 text-xs font-mono"
          />
        </div>

        <div className="mt-4 flex justify-end">
          <button
            type="button"
            onClick={handleSimulate}
            disabled={simulating}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-indigo-600 text-white hover:bg-indigo-500 font-medium text-xs transition-colors disabled:opacity-50"
          >
            <Play className="w-3.5 h-3.5" />
            {simulating ? "Evaluating Policies..." : "Run Simulation"}
          </button>
        </div>

        {/* Results Panel */}
        {result && (
          <div className="mt-5 p-4 rounded-xl bg-slate-950/80 border border-slate-800 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-semibold uppercase text-slate-400">
                Simulation Decision
              </span>
              <span
                className={cn(
                  "inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold border",
                  decision === "allow"
                    ? "bg-emerald-950/60 text-emerald-300 border-emerald-800/60"
                    : decision === "allow_with_constraints"
                    ? "bg-cyan-950/60 text-cyan-300 border-cyan-800/60"
                    : decision === "require_approval"
                    ? "bg-amber-950/60 text-amber-300 border-amber-800/60"
                    : "bg-rose-950/60 text-rose-300 border-rose-800/60"
                )}
              >
                {decision === "allow" ? (
                  <CheckCircle className="w-3.5 h-3.5" />
                ) : decision === "deny" ? (
                  <ShieldAlert className="w-3.5 h-3.5" />
                ) : (
                  <AlertTriangle className="w-3.5 h-3.5" />
                )}
                {decision}
              </span>
            </div>

            {/* Reasons */}
            {result.decision?.reasons?.length > 0 && (
              <div>
                <span className="text-[10px] text-slate-400 font-medium">Evaluation Reasons:</span>
                <ul className="mt-1 space-y-1">
                  {result.decision.reasons.map((r, i) => (
                    <li key={i} className="text-xs text-slate-300 flex items-start gap-1.5">
                      <span className="text-slate-400">•</span>
                      <span>{r}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Matched Policies */}
            {result.decision?.matched_policies?.length > 0 && (
              <div>
                <span className="text-[10px] text-slate-400 font-medium">Matched Policies:</span>
                <div className="mt-1 flex flex-wrap gap-1.5">
                  {result.decision.matched_policies.map((p, i) => (
                    <span
                      key={i}
                      className="px-2 py-0.5 rounded text-[10px] font-mono bg-slate-900 border border-slate-800 text-indigo-300"
                    >
                      {p}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Constraints */}
            {result.decision?.constraints && Object.keys(result.decision.constraints).length > 0 && (
              <div className="pt-2 border-t border-slate-850">
                <span className="text-[10px] text-slate-400 font-medium">Active Constraints:</span>
                <pre className="mt-1 p-2 rounded bg-slate-900 text-[10px] font-mono text-cyan-300 overflow-x-auto">
                  {JSON.stringify(result.decision.constraints, null, 2)}
                </pre>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
