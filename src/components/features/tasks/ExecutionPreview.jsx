"use client";

import React from "react";
import {
  Sparkles,
  RefreshCw,
  Shield,
  Search,
  FileText,
  Database,
  Layers,
  Cpu,
  Wrench,
  CheckCircle2,
  AlertTriangle,
  Workflow,
  Info,
  Clock,
  ExternalLink,
} from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";

/**
 * ExecutionPreview Component (Step 20 - AI Task Intelligence)
 *
 * Displays a bounded, user-safe execution preview showing:
 * - Task Type
 * - Execution Mode
 * - Knowledge Sources (Documents, Web, Connectors, Memory)
 * - Required Tools
 * - Model Capabilities
 * - Verification / Evaluation
 * - Human Approval Requirement
 * - Complexity
 *
 * Strictly adheres to safety constraints:
 * - Never exposes chain-of-thought or internal model reasoning.
 * - Displays bounded factual requirements only.
 */
export function ExecutionPreview({
  analysis,
  requirements,
  executionMode = "auto",
  isLoading = false,
  onRefresh,
  error = null,
  className = "",
}) {
  const reqs = requirements || analysis?.requirements || {};
  const taskType = analysis?.task_type || "question_answering";
  const intent = analysis?.intent || "";
  const confidence = analysis?.confidence ? Math.round(analysis.confidence * 100) : null;
  const suggestedMode = analysis?.suggested_execution_mode || "direct";
  const complexity = reqs?.max_execution_complexity?.value || reqs?.max_execution_complexity || "simple";
  const explanation = analysis?.explanation || "Execution requirements resolved via server-side task intelligence.";

  // Format task type for human readability
  const formatTaskType = (type) => {
    if (!type) return "General Task";
    return type
      .split("_")
      .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
      .join(" ");
  };

  // Format execution mode for human readability
  const formatExecutionMode = (mode) => {
    switch (mode) {
      case "direct":
        return "Direct Generation";
      case "retrieval":
        return "Knowledge Retrieval";
      case "tool_assisted":
        return "Tool-Assisted";
      case "orchestrated":
        return "Multi-Step Orchestrated";
      case "workflow":
        return "Workflow Execution";
      default:
        return mode ? mode.charAt(0).toUpperCase() + mode.slice(1) : "Auto";
    }
  };

  // Extract boolean helper from requirement structure (value or boolean)
  const getReqValue = (field) => {
    if (typeof field === "boolean") return field;
    if (field && typeof field.value === "boolean") return field.value;
    return false;
  };

  // Compute what capabilities are used
  const usesWebSearch = getReqValue(reqs.web_search_required || reqs.web_search);
  const usesDocuments = getReqValue(reqs.document_retrieval_required || reqs.documents || reqs.retrieval);
  const usesConnectors = getReqValue(reqs.connector_required || reqs.connectors);
  const usesMemory = getReqValue(reqs.memory_required || reqs.memory);
  const usesTools = getReqValue(reqs.tools_required || reqs.tools);
  const usesEvaluation = getReqValue(reqs.evaluation_required || reqs.evaluation);
  const usesStructuredOutput = getReqValue(reqs.structured_output_required || reqs.structured_output);
  const usesVision = getReqValue(reqs.vision_required || reqs.requires_vision);
  const usesAudio = getReqValue(reqs.audio_required || reqs.requires_audio);
  const usesVideo = getReqValue(reqs.video_required || reqs.requires_video);
  const usesTable = getReqValue(reqs.table_required || reqs.requires_table);
  const usesMultimodal = getReqValue(reqs.multimodal_required || reqs.requires_multimodal) || usesVision || usesAudio || usesVideo || usesTable;
  const requiresApproval = getReqValue(reqs.human_approval_required || reqs.human_approval);

  // Active knowledge sources list
  const knowledgeSources = [];
  if (usesDocuments) knowledgeSources.push("Document Library");
  if (usesWebSearch) knowledgeSources.push("Web Search");
  if (usesConnectors) knowledgeSources.push("External Connectors");
  if (usesMemory) knowledgeSources.push("User Memory");
  if (usesMultimodal) knowledgeSources.push("Multimodal Artifacts");

  // Multimodal capabilities list
  const multimodalCaps = [];
  if (usesVision) multimodalCaps.push("Vision");
  if (usesAudio) multimodalCaps.push("Audio");
  if (usesVideo) multimodalCaps.push("Video");
  if (usesTable) multimodalCaps.push("Structured Tables");

  // Model capabilities list
  const modelCapabilities = Array.isArray(reqs.model_capabilities?.value)
    ? reqs.model_capabilities.value
    : Array.isArray(reqs.model_capabilities)
    ? reqs.model_capabilities
    : [];

  return (
    <div
      className={`rounded-xl border border-indigo-500/20 bg-gradient-to-b from-indigo-950/20 via-slate-900/60 to-slate-900/90 backdrop-blur-md p-5 shadow-lg relative overflow-hidden transition-all ${className}`}
    >
      {/* Decorative top accent glow */}
      <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-indigo-500 to-transparent opacity-80" />

      {/* Header bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-indigo-500/20 border border-indigo-500/30 text-indigo-400">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold uppercase tracking-wider text-indigo-300">
                AI Task Intelligence
              </span>
              {confidence && (
                <span className="text-[11px] px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-300 border border-indigo-500/20">
                  {confidence}% confidence
                </span>
              )}
            </div>
            <h4 className="text-sm font-medium text-slate-200">
              Execution Preview & Requirements
            </h4>
          </div>
        </div>

        {onRefresh && (
          <Button
            variant="ghost"
            size="sm"
            onClick={onRefresh}
            disabled={isLoading}
            className="text-xs text-slate-400 hover:text-slate-200 border border-slate-700/60 hover:bg-slate-800/60 h-8 px-2.5 gap-1.5"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? "animate-spin text-indigo-400" : ""}`} />
            Refresh Analysis
          </Button>
        )}
      </div>

      {/* Error state */}
      {error && (
        <div className="mb-4 p-3 rounded-lg bg-red-950/30 border border-red-800/40 text-xs text-red-300 flex items-start gap-2">
          <AlertTriangle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
          <div>
            <p className="font-medium">Task Intelligence Notice</p>
            <p className="text-red-400/80">{error}</p>
          </div>
        </div>
      )}

      {/* Safe Intent / Explanation */}
      {explanation && (
        <div className="mb-4 p-2.5 rounded-lg bg-slate-800/40 border border-slate-800 text-xs text-slate-300 flex items-start gap-2">
          <Info className="w-3.5 h-3.5 text-indigo-400 shrink-0 mt-0.5" />
          <span>{explanation}</span>
        </div>
      )}

      {/* Primary Attributes Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
        {/* Task Type */}
        <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800/80">
          <span className="text-[11px] text-slate-400 block mb-1">Task Type</span>
          <span className="text-xs font-semibold text-slate-100 flex items-center gap-1.5">
            <Layers className="w-3.5 h-3.5 text-indigo-400" />
            {formatTaskType(taskType)}
          </span>
        </div>

        {/* Execution Mode */}
        <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800/80">
          <span className="text-[11px] text-slate-400 block mb-1">Execution Mode</span>
          <span className="text-xs font-semibold text-slate-100 flex items-center gap-1.5">
            <Workflow className="w-3.5 h-3.5 text-sky-400" />
            {formatExecutionMode(executionMode === "auto" ? suggestedMode : executionMode)}
          </span>
        </div>

        {/* Complexity */}
        <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800/80">
          <span className="text-[11px] text-slate-400 block mb-1">Complexity</span>
          <Badge
            variant={
              complexity === "simple"
                ? "secondary"
                : complexity === "moderate"
                ? "primary"
                : "warning"
            }
            className="capitalize text-[11px] py-0 px-2 font-medium"
          >
            {complexity}
          </Badge>
        </div>

        {/* Human Approval */}
        <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800/80">
          <span className="text-[11px] text-slate-400 block mb-1">Human Approval</span>
          {requiresApproval ? (
            <span className="text-xs font-semibold text-amber-300 flex items-center gap-1.5">
              <Shield className="w-3.5 h-3.5 text-amber-400" />
              Required
            </span>
          ) : (
            <span className="text-xs text-slate-400 flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
              Not required
            </span>
          )}
        </div>
      </div>

      {/* "This task will use" Section */}
      <div className="p-3 rounded-lg bg-slate-900/40 border border-slate-800/60 space-y-2">
        <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 block">
          This task will use:
        </span>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
          {/* Knowledge sources */}
          <div className="flex items-center gap-2 text-slate-300">
            <Database className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
            <span className="text-slate-400">Knowledge:</span>
            <span className="font-medium text-slate-200">
              {knowledgeSources.length > 0 ? knowledgeSources.join(" + ") : "Direct generation"}
            </span>
          </div>

          {/* Tools */}
          <div className="flex items-center gap-2 text-slate-300">
            <Wrench className="w-3.5 h-3.5 text-sky-400 shrink-0" />
            <span className="text-slate-400">Tools:</span>
            <span className="font-medium text-slate-200">
              {usesTools
                ? usesWebSearch
                  ? "Web Search & Registered Tools"
                  : "Registered Tools"
                : "None"}
            </span>
          </div>

          {/* Verification / Evaluation */}
          <div className="flex items-center gap-2 text-slate-300">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
            <span className="text-slate-400">Verification:</span>
            <span className="font-medium text-slate-200">
              {usesEvaluation
                ? reqs.evaluation_mode?.value || reqs.evaluation_mode || "Standard"
                : "Off"}
            </span>
          </div>

          {/* Model Capabilities */}
          <div className="flex items-center gap-2 text-slate-300">
            <Cpu className="w-3.5 h-3.5 text-purple-400 shrink-0" />
            <span className="text-slate-400">Capabilities:</span>
            <span className="font-medium text-slate-200">
              {modelCapabilities.length > 0
                ? modelCapabilities.join(", ")
                : "Standard Chat"}
            </span>
          </div>

          {/* Multimodal Intelligence */}
          {multimodalCaps.length > 0 && (
            <div className="flex items-center gap-2 text-slate-300 sm:col-span-2">
              <Sparkles className="w-3.5 h-3.5 text-pink-400 shrink-0" />
              <span className="text-slate-400">Multimodal:</span>
              <span className="font-medium text-pink-300">
                {multimodalCaps.join(", ")}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Safety Policy Boundary Disclaimer */}
      <div className="mt-3 flex items-center justify-between text-[11px] text-slate-500">
        <span>Server-side policies remain authoritative over all execution requirements.</span>
        <span className="text-indigo-400/80 font-mono">Step 20</span>
      </div>
    </div>
  );
}

export default ExecutionPreview;
