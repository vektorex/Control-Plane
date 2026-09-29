"use client";

import React, { useState, useEffect, use } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Input } from "@/components/ui/Input";
import { workflowService } from "@/services/workflows";
import { StepConfigDrawer } from "@/components/features/workflows/StepConfigDrawer";
import { RunWorkflowModal } from "@/components/features/workflows/RunWorkflowModal";
import {
  Workflow,
  ArrowLeft,
  Plus,
  Play,
  Save,
  CheckCircle2,
  AlertTriangle,
  AlertCircle,
  Sliders,
  Sparkles,
  Search,
  Wrench,
  Bot,
  ShieldCheck,
  Split,
  GitFork,
  FileCheck,
  ChevronUp,
  ChevronDown,
  Trash2,
  Copy,
  Settings2,
  History,
  Check,
  X,
  Loader2,
  Code2,
} from "lucide-react";

const stepIcons = {
  input: Sliders,
  context: Sparkles,
  retrieve: Search,
  tool: Wrench,
  generate: Bot,
  evaluate: ShieldCheck,
  transform: Split,
  condition: GitFork,
  output: FileCheck,
};

const stepColors = {
  input: "text-blue-400 bg-blue-500/10 border-blue-500/20",
  context: "text-purple-400 bg-purple-500/10 border-purple-500/20",
  retrieve: "text-amber-400 bg-amber-500/10 border-amber-500/20",
  tool: "text-orange-400 bg-orange-500/10 border-orange-500/20",
  generate: "text-indigo-400 bg-indigo-500/10 border-indigo-500/20",
  evaluate: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
  transform: "text-cyan-400 bg-cyan-500/10 border-cyan-500/20",
  condition: "text-pink-400 bg-pink-500/10 border-pink-500/20",
  output: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
};

export default function WorkflowBuilderPage({ params }) {
  const unwrappedParams = use(params);
  const workflowId = unwrappedParams.workflowId;
  const router = useRouter();

  const [workflow, setWorkflow] = useState(null);
  const [steps, setSteps] = useState([]);
  const [inputSchema, setInputSchema] = useState({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [publishing, setPublishing] = useState(false);
  const [validating, setValidating] = useState(false);
  const [validationResult, setValidationResult] = useState(null);
  const [activeStepConfig, setActiveStepConfig] = useState(null);
  const [isRunModalOpen, setIsRunModalOpen] = useState(false);
  const [isAddStepOpen, setIsAddStepOpen] = useState(false);
  const [isSchemaModalOpen, setIsSchemaModalOpen] = useState(false);
  const [bannerMessage, setBannerMessage] = useState(null);
  const [error, setError] = useState(null);

  // Load workflow and definition
  const loadWorkflowData = async () => {
    try {
      setLoading(true);
      setError(null);
      const wf = await workflowService.getWorkflow(workflowId);
      const def = await workflowService.getWorkflowDefinition(workflowId);

      setWorkflow(wf);
      setSteps(def?.steps || []);
      setInputSchema(def?.input_schema || {});
    } catch (err) {
      console.error("[WorkflowBuilder] Failed to load workflow:", err);
      setError(err.message || "Failed to load workflow definition");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadWorkflowData();
  }, [workflowId]);

  // Save draft definition
  const handleSaveDraft = async () => {
    try {
      setSaving(true);
      setError(null);
      const payload = {
        steps,
        input_schema: inputSchema,
        output_schema: workflow?.output_schema || {},
        configuration: workflow?.configuration || {},
      };
      const updated = await workflowService.updateWorkflowDefinition(workflowId, payload);
      setWorkflow(updated);
      setBannerMessage({ type: "success", text: "Workflow draft saved successfully." });
      setTimeout(() => setBannerMessage(null), 3500);
    } catch (err) {
      console.error("[WorkflowBuilder] Save error:", err);
      setError(err.message || "Failed to save workflow draft");
    } finally {
      setSaving(false);
    }
  };

  // Validate workflow
  const handleValidate = async () => {
    try {
      setValidating(true);
      // Auto-save current steps first
      await workflowService.updateWorkflowDefinition(workflowId, {
        steps,
        input_schema: inputSchema,
      });
      const val = await workflowService.validateWorkflow(workflowId);
      setValidationResult(val);
    } catch (err) {
      console.error("[WorkflowBuilder] Validation error:", err);
      setError(err.message || "Failed to validate workflow");
    } finally {
      setValidating(false);
    }
  };

  // Publish workflow
  const handlePublish = async () => {
    try {
      setPublishing(true);
      setError(null);
      // Save draft first
      await workflowService.updateWorkflowDefinition(workflowId, {
        steps,
        input_schema: inputSchema,
      });
      const published = await workflowService.publishWorkflow(workflowId);
      setWorkflow(published);
      setValidationResult(null);
      setBannerMessage({
        type: "success",
        text: `Published version ${published.version}! Version snapshot is now immutable.`,
      });
      setTimeout(() => setBannerMessage(null), 4500);
    } catch (err) {
      console.error("[WorkflowBuilder] Publishing error:", err);
      setError(err.message || "Failed to publish workflow. Check validation issues.");
    } finally {
      setPublishing(false);
    }
  };

  // Step operations
  const moveStep = (index, direction) => {
    const targetIndex = index + direction;
    if (targetIndex < 0 || targetIndex >= steps.length) return;
    const next = [...steps];
    const temp = next[index];
    next[index] = next[targetIndex];
    next[targetIndex] = temp;
    setSteps(next);
  };

  const removeStep = (index) => {
    const next = steps.filter((_, i) => i !== index);
    setSteps(next);
  };

  const duplicateStep = (index) => {
    const original = steps[index];
    const newId = `${original.id}_copy_${Date.now().toString().slice(-4)}`;
    const copy = {
      ...original,
      id: newId,
      name: `${original.name} (Copy)`,
    };
    const next = [...steps];
    next.splice(index + 1, 0, copy);
    setSteps(next);
  };

  const toggleStepEnabled = (index) => {
    const next = [...steps];
    next[index] = { ...next[index], enabled: !next[index].enabled };
    setSteps(next);
  };

  const handleAddStep = (stepType) => {
    const defaultConfigs = {
      input: {},
      context: { max_tokens: 2000, include_workspace_context: true },
      retrieve: { mode: "hybrid", top_k: 5, query: "{{input.topic}}" },
      tool: { tool: "web_search", parameters: { query: "{{input.topic}}" }, max_retries: 1 },
      generate: {
        mode: "smart",
        temperature: 0.7,
        prompt_template: "Process data for: {{input.topic}}",
      },
      evaluate: { mode: "grounding", threshold: 0.75 },
      transform: { operation: "select", source: "steps.retrieve.results", fields: ["title", "url"] },
      condition: { left: "steps.evaluate.status", operator: "==", right: "warning" },
      output: { output_template: "{{steps.generate.output}}", format: "markdown" },
    };

    const newStepId = `${stepType}_${Date.now().toString().slice(-4)}`;
    const newStep = {
      id: newStepId,
      name: `${stepType.charAt(0).toUpperCase() + stepType.slice(1)} Step`,
      type: stepType,
      config: defaultConfigs[stepType] || {},
      enabled: true,
    };

    setSteps([...steps, newStep]);
    setIsAddStepOpen(false);
  };

  const handleStepSave = (updatedStep) => {
    setSteps(steps.map((s) => (s.id === updatedStep.id ? updatedStep : s)));
  };

  if (loading) {
    return (
      <div className="p-16 text-center text-slate-400">
        <Loader2 className="w-6 h-6 animate-spin mx-auto mb-2 text-indigo-400" />
        <p className="text-sm">Loading workflow builder...</p>
      </div>
    );
  }

  if (!workflow) {
    return (
      <div className="p-8 text-center text-slate-300">
        <p>Workflow not found.</p>
        <Link href="/app/workflows">
          <Button variant="outline" className="mt-4">
            Back to Workflows
          </Button>
        </Link>
      </div>
    );
  }

  const isPublished = workflow.status === "published";

  return (
    <div className="space-y-6 pb-16 max-w-6xl mx-auto">
      {/* Top Header / Actions Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-800/80">
        <div className="flex items-center gap-3">
          <Link href="/app/workflows">
            <button className="p-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-slate-200 transition-colors">
              <ArrowLeft className="w-4 h-4" />
            </button>
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-bold text-slate-100">{workflow.name}</h1>
              <Badge
                variant={isPublished ? "success" : "default"}
                className="text-[10px] uppercase font-mono"
              >
                {workflow.status}
              </Badge>
              <Badge variant="outline" className="text-[10px] font-mono">
                v{workflow.version}
              </Badge>
            </div>
            <p className="text-xs text-slate-400 mt-0.5 font-mono">
              Slug: {workflow.slug}
            </p>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex flex-wrap items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleValidate}
            disabled={validating}
            className="text-xs gap-1.5"
          >
            {validating ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <CheckCircle2 className="w-3.5 h-3.5 text-indigo-400" />
            )}
            <span>Validate</span>
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={handleSaveDraft}
            disabled={saving}
            className="text-xs gap-1.5"
          >
            {saving ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <Save className="w-3.5 h-3.5" />
            )}
            <span>Save Draft</span>
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={handlePublish}
            disabled={publishing}
            className="text-xs gap-1.5 text-indigo-300 border-indigo-500/30 hover:bg-indigo-500/10"
          >
            {publishing ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <Check className="w-3.5 h-3.5" />
            )}
            <span>Publish Version</span>
          </Button>

          <Button
            variant="primary"
            size="sm"
            onClick={() => setIsRunModalOpen(true)}
            className="text-xs gap-1.5 bg-emerald-600 hover:bg-emerald-500 text-white"
          >
            <Play className="w-3.5 h-3.5 fill-white" />
            <span>Run Pipeline</span>
          </Button>
        </div>
      </div>

      {/* Banner / Alerts */}
      {bannerMessage && (
        <div className="p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-lg text-emerald-400 text-xs flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 shrink-0" />
            <span>{bannerMessage.text}</span>
          </div>
          <button onClick={() => setBannerMessage(null)}>
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {error && (
        <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded-lg text-rose-400 text-xs flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
          <button onClick={() => setError(null)}>
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* Validation Result Drawer */}
      {validationResult && (
        <Card
          className={`p-4 ${
            validationResult.valid
              ? "bg-emerald-500/5 border-emerald-500/30"
              : "bg-rose-500/5 border-rose-500/30"
          }`}
        >
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              {validationResult.valid ? (
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              ) : (
                <AlertTriangle className="w-4 h-4 text-rose-400" />
              )}
              <span
                className={`text-xs font-semibold ${
                  validationResult.valid ? "text-emerald-300" : "text-rose-300"
                }`}
              >
                {validationResult.valid
                  ? "Workflow Definition Validated Successfully"
                  : `Validation Failed (${validationResult.issues?.length || 0} issues)`}
              </span>
            </div>
            <button
              onClick={() => setValidationResult(null)}
              className="text-xs text-slate-400 hover:text-slate-200"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>

          {validationResult.issues?.length > 0 && (
            <ul className="space-y-1.5 mt-2 text-xs">
              {validationResult.issues.map((iss, i) => (
                <li
                  key={i}
                  className={`flex items-start gap-2 ${
                    iss.level === "error" ? "text-rose-400" : "text-amber-400"
                  }`}
                >
                  <span className="font-mono uppercase text-[10px] px-1 py-0.5 rounded bg-slate-900 border border-slate-800 shrink-0">
                    {iss.level}
                  </span>
                  <span>
                    {iss.step_id ? <strong>[{iss.step_id}] </strong> : ""}
                    {iss.message}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </Card>
      )}

      {/* Builder Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Left: Step Sequence & Visual Pipeline */}
        <div className="lg:col-span-3 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                Execution Pipeline ({steps.length} Steps)
              </span>
            </div>
            <Button
              size="sm"
              variant="outline"
              onClick={() => setIsAddStepOpen(true)}
              className="text-xs gap-1.5"
            >
              <Plus className="w-3.5 h-3.5 text-indigo-400" />
              <span>Add Step</span>
            </Button>
          </div>

          {/* Steps List */}
          <div className="space-y-3">
            {steps.map((step, index) => {
              const Icon = stepIcons[step.type] || Sliders;
              const colorClass = stepColors[step.type] || "text-slate-400 bg-slate-800";
              const isFirst = index === 0;
              const isLast = index === steps.length - 1;

              return (
                <Card
                  key={step.id || index}
                  className={`p-4 transition-all duration-150 border-slate-800 bg-slate-900/70 hover:border-slate-700 ${
                    !step.enabled ? "opacity-60 bg-slate-950/40" : ""
                  }`}
                >
                  <div className="flex items-center justify-between gap-3">
                    {/* Left: Step Index & Icon & Info */}
                    <div className="flex items-center gap-3 min-w-0">
                      <div className="w-6 h-6 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-[11px] font-mono font-semibold text-slate-300 shrink-0">
                        {index + 1}
                      </div>

                      <div className={`p-2 rounded-lg border shrink-0 ${colorClass}`}>
                        <Icon className="w-4 h-4" />
                      </div>

                      <div className="min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-semibold text-slate-100 truncate">
                            {step.name}
                          </span>
                          <Badge variant="outline" className="text-[10px] font-mono">
                            {step.type}
                          </Badge>
                          {!step.enabled && (
                            <span className="text-[10px] font-mono text-amber-400 bg-amber-500/10 px-1.5 py-0.5 rounded border border-amber-500/20">
                              Disabled
                            </span>
                          )}
                        </div>
                        <div className="text-xs text-slate-400 font-mono mt-0.5 truncate">
                          ID: <span className="text-indigo-300">{step.id}</span>
                          {step.description && ` • ${step.description}`}
                        </div>
                      </div>
                    </div>

                    {/* Right: Step Action Buttons */}
                    <div className="flex items-center gap-1 shrink-0">
                      {/* Move controls */}
                      <button
                        onClick={() => moveStep(index, -1)}
                        disabled={isFirst}
                        className="p-1 text-slate-400 hover:text-slate-200 disabled:opacity-30 rounded"
                        title="Move Up"
                      >
                        <ChevronUp className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => moveStep(index, 1)}
                        disabled={isLast}
                        className="p-1 text-slate-400 hover:text-slate-200 disabled:opacity-30 rounded"
                        title="Move Down"
                      >
                        <ChevronDown className="w-4 h-4" />
                      </button>

                      <div className="h-4 w-px bg-slate-800 mx-1" />

                      {/* Enable/Disable switch */}
                      <button
                        onClick={() => toggleStepEnabled(index)}
                        className={`text-[10px] px-2 py-1 rounded font-mono border ${
                          step.enabled
                            ? "text-emerald-400 bg-emerald-500/10 border-emerald-500/20"
                            : "text-slate-400 bg-slate-800 border-slate-700"
                        }`}
                        title="Toggle Enable/Disable"
                      >
                        {step.enabled ? "ON" : "OFF"}
                      </button>

                      {/* Duplicate Step */}
                      <button
                        onClick={() => duplicateStep(index)}
                        className="p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded"
                        title="Duplicate Step"
                      >
                        <Copy className="w-3.5 h-3.5" />
                      </button>

                      {/* Configure Step */}
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => setActiveStepConfig(step)}
                        className="h-7 text-xs px-2.5 gap-1 text-slate-200 border-slate-700"
                      >
                        <Settings2 className="w-3 h-3 text-indigo-400" />
                        <span>Config</span>
                      </Button>

                      {/* Delete Step */}
                      <button
                        onClick={() => removeStep(index)}
                        className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 rounded"
                        title="Delete Step"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                </Card>
              );
            })}
          </div>

          {steps.length === 0 && (
            <Card className="p-8 text-center bg-slate-900/40 border-slate-800 border-dashed">
              <p className="text-xs text-slate-400 mb-3">
                No steps in this workflow yet. Click Add Step to begin constructing your pipeline.
              </p>
              <Button size="sm" variant="primary" onClick={() => setIsAddStepOpen(true)}>
                <Plus className="w-4 h-4 mr-1" />
                Add First Step
              </Button>
            </Card>
          )}
        </div>

        {/* Right: Input Schema & Metadata Inspector */}
        <div className="space-y-4">
          <Card className="p-4 bg-slate-900/70 border-slate-800 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5">
                <Code2 className="w-4 h-4 text-indigo-400" />
                <span className="text-xs font-semibold text-slate-200 uppercase tracking-wider">
                  Input Contract
                </span>
              </div>
              <Badge variant="outline" className="text-[10px] font-mono">
                {Object.keys(inputSchema).length} fields
              </Badge>
            </div>

            <p className="text-[11px] text-slate-400 leading-relaxed">
              Define the typed parameters this workflow requires at runtime before execution.
            </p>

            <div className="space-y-2 pt-1">
              {Object.entries(inputSchema).map(([k, spec]) => (
                <div
                  key={k}
                  className="p-2 rounded bg-slate-950/60 border border-slate-800/80 text-xs space-y-0.5"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-slate-200 font-semibold">{k}</span>
                    <span className="text-[10px] font-mono text-indigo-400 uppercase">
                      {spec.type}
                    </span>
                  </div>
                  {spec.description && (
                    <div className="text-[10px] text-slate-400">{spec.description}</div>
                  )}
                </div>
              ))}
            </div>

            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsSchemaModalOpen(true)}
              className="w-full text-xs gap-1.5 mt-2"
            >
              <Sliders className="w-3 h-3 text-indigo-400" />
              <span>Edit Input Schema</span>
            </Button>
          </Card>

          {/* Quick Variable Reference */}
          <Card className="p-4 bg-slate-900/70 border-slate-800 space-y-2 text-xs">
            <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider block">
              Variable Resolution
            </span>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              Reference inputs or previous step outputs anywhere in configurations:
            </p>
            <div className="space-y-1 font-mono text-[11px]">
              <div className="p-1.5 rounded bg-slate-950 text-indigo-300">
                {"{{input.<field_name>}}"}
              </div>
              <div className="p-1.5 rounded bg-slate-950 text-emerald-300">
                {"{{steps.<step_id>.output}}"}
              </div>
              <div className="p-1.5 rounded bg-slate-950 text-amber-300">
                {"{{steps.<step_id>.results}}"}
              </div>
            </div>
          </Card>
        </div>
      </div>

      {/* Add Step Selection Modal */}
      {isAddStepOpen && (
        <AddStepModal
          isOpen={isAddStepOpen}
          onClose={() => setIsAddStepOpen(false)}
          onSelectType={handleAddStep}
        />
      )}

      {/* Step Config Drawer */}
      {activeStepConfig && (
        <StepConfigDrawer
          isOpen={Boolean(activeStepConfig)}
          onClose={() => setActiveStepConfig(null)}
          step={activeStepConfig}
          onSave={handleStepSave}
          allStepIds={steps.map((s) => s.id)}
        />
      )}

      {/* Input Schema Editor Modal */}
      {isSchemaModalOpen && (
        <InputSchemaEditorModal
          isOpen={isSchemaModalOpen}
          onClose={() => setIsSchemaModalOpen(false)}
          schema={inputSchema}
          onSave={(newSchema) => setInputSchema(newSchema)}
        />
      )}

      {/* Run Modal */}
      {isRunModalOpen && (
        <RunWorkflowModal
          isOpen={isRunModalOpen}
          onClose={() => setIsRunModalOpen(false)}
          workflow={{
            ...workflow,
            input_schema: inputSchema,
          }}
        />
      )}
    </div>
  );
}

// Sub-component: AddStepModal
function AddStepModal({ isOpen, onClose, onSelectType }) {
  const stepTypes = [
    { type: "input", name: "Input", desc: "Define or parse incoming workflow parameters" },
    { type: "context", name: "Context", desc: "Inject project context and memory into execution" },
    { type: "retrieve", name: "Retrieve", desc: "Hybrid / semantic retrieval from document vector index" },
    { type: "tool", name: "Tool", desc: "Execute web search or specialized backend tools" },
    { type: "generate", name: "Generate", desc: "Synthesize content using LLM model routing" },
    { type: "evaluate", name: "Evaluate", desc: "Verify grounding, completeness, or factual accuracy" },
    { type: "transform", name: "Transform", desc: "Safe structured data selection, filtering, and joining" },
    { type: "condition", name: "Condition", desc: "Deterministic branching based on step status or values" },
    { type: "output", name: "Output", desc: "Format and emit the final workflow response" },
  ];

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-xs">
      <Card className="w-full max-w-lg p-5 bg-slate-900 border-slate-800 space-y-4">
        <div className="flex items-center justify-between pb-2 border-b border-slate-800">
          <div>
            <h3 className="text-sm font-bold text-slate-100">Add Step to Pipeline</h3>
            <p className="text-xs text-slate-400">Choose a deterministic step type to insert</p>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-200">
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-h-[60vh] overflow-y-auto pr-1">
          {stepTypes.map(({ type, name, desc }) => {
            const Icon = stepIcons[type] || Sliders;
            const colorClass = stepColors[type] || "text-slate-400 bg-slate-800";

            return (
              <button
                key={type}
                onClick={() => onSelectType(type)}
                className="p-3 rounded-lg bg-slate-950/60 border border-slate-800 hover:border-indigo-500/50 hover:bg-indigo-500/5 transition-all text-left flex items-start gap-2.5 group"
              >
                <div className={`p-2 rounded-lg border shrink-0 ${colorClass}`}>
                  <Icon className="w-4 h-4" />
                </div>
                <div>
                  <div className="text-xs font-semibold text-slate-200 group-hover:text-indigo-300">
                    {name}
                  </div>
                  <div className="text-[11px] text-slate-400 mt-0.5 line-clamp-2">{desc}</div>
                </div>
              </button>
            );
          })}
        </div>
      </Card>
    </div>
  );
}

// Sub-component: InputSchemaEditorModal
function InputSchemaEditorModal({ isOpen, onClose, schema, onSave }) {
  const [jsonText, setJsonText] = useState("");
  const [parseError, setParseError] = useState(null);

  useEffect(() => {
    setJsonText(JSON.stringify(schema || {}, null, 2));
    setParseError(null);
  }, [schema]);

  if (!isOpen) return null;

  const handleSave = () => {
    try {
      const parsed = JSON.parse(jsonText);
      onSave(parsed);
      onClose();
    } catch (err) {
      setParseError(`Invalid JSON: ${err.message}`);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-xs">
      <Card className="w-full max-w-lg p-5 bg-slate-900 border-slate-800 space-y-4">
        <div className="flex items-center justify-between pb-2 border-b border-slate-800">
          <div>
            <h3 className="text-sm font-bold text-slate-100">Edit Input Schema</h3>
            <p className="text-xs text-slate-400">Configure typed input contract in JSON format</p>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-200">
            <X className="w-4 h-4" />
          </button>
        </div>

        {parseError && (
          <div className="p-2.5 bg-rose-500/10 border border-rose-500/30 rounded text-rose-400 text-xs">
            {parseError}
          </div>
        )}

        <div>
          <textarea
            rows={10}
            value={jsonText}
            onChange={(e) => {
              setJsonText(e.target.value);
              setParseError(null);
            }}
            className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-xs font-mono text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          />
        </div>

        <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-800">
          <Button variant="outline" size="sm" onClick={onClose}>
            Cancel
          </Button>
          <Button variant="primary" size="sm" onClick={handleSave}>
            Save Schema
          </Button>
        </div>
      </Card>
    </div>
  );
}
