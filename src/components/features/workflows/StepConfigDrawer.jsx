"use client";

import React, { useState, useEffect } from "react";
import { Modal } from "@/components/ui/Modal";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Badge } from "@/components/ui/Badge";
import {
  Sliders,
  Sparkles,
  Search,
  Wrench,
  Bot,
  ShieldCheck,
  Split,
  GitFork,
  FileCheck,
  X,
  Plus,
  Trash2,
} from "lucide-react";

const stepTypeIcons = {
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

export function StepConfigDrawer({ isOpen, onClose, step, onSave, allStepIds = [] }) {
  const [config, setConfig] = useState({});
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");

  useEffect(() => {
    if (step) {
      setConfig({ ...(step.config || {}) });
      setName(step.name || "");
      setDescription(step.description || "");
    }
  }, [step]);

  if (!step) return null;

  const Icon = stepTypeIcons[step.type] || Sliders;

  const handleFieldChange = (field, val) => {
    setConfig((prev) => ({
      ...prev,
      [field]: val,
    }));
  };

  const handleSave = () => {
    onSave({
      ...step,
      name: name.trim() || step.name,
      description: description.trim() || null,
      config,
    });
    onClose();
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`Configure Step: ${name || step.id}`}
      description={`Step Type: ${step.type.toUpperCase()}`}
    >
      <div className="space-y-4 max-h-[65vh] overflow-y-auto pr-1">
        {/* Step Metadata Header */}
        <div className="p-3 bg-slate-900 border border-slate-800 rounded-lg flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              <Icon className="w-4 h-4" />
            </div>
            <div>
              <div className="text-xs font-mono text-slate-400">ID: {step.id}</div>
              <div className="text-xs font-medium text-slate-200">Type: {step.type}</div>
            </div>
          </div>
          <Badge variant="outline" className="font-mono text-[10px]">
            {step.type}
          </Badge>
        </div>

        {/* Name and Description */}
        <div className="grid grid-cols-1 gap-3">
          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">
              Step Label
            </label>
            <Input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Descriptive label..."
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">
              Description (Optional)
            </label>
            <Input
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="What this step does..."
            />
          </div>
        </div>

        {/* Step Type Specific Forms */}
        <div className="pt-2 border-t border-slate-800/80 space-y-3">
          <div className="text-xs font-semibold text-indigo-400 uppercase tracking-wider">
            Step Configuration
          </div>

          {/* INPUT STEP */}
          {step.type === "input" && (
            <div className="p-3 bg-slate-900/60 rounded-lg border border-slate-800 text-xs text-slate-400 space-y-2">
              <p>
                The input step captures runtime parameters based on the workflow input schema and makes them available to subsequent steps via <code className="text-indigo-300 bg-slate-800 px-1 py-0.5 rounded">{"{{input.<field>}}"}</code>.
              </p>
            </div>
          )}

          {/* CONTEXT STEP */}
          {step.type === "context" && (
            <div className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Max Context Tokens</label>
                <Input
                  type="number"
                  value={config.max_tokens ?? 2000}
                  onChange={(e) => handleFieldChange("max_tokens", parseInt(e.target.value) || 2000)}
                />
              </div>
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="include_workspace_context"
                  checked={config.include_workspace_context ?? true}
                  onChange={(e) => handleFieldChange("include_workspace_context", e.target.checked)}
                  className="rounded bg-slate-900 border-slate-700 text-indigo-600 focus:ring-indigo-500 w-4 h-4"
                />
                <label htmlFor="include_workspace_context" className="text-xs text-slate-300 cursor-pointer">
                  Include Workspace Knowledge Context
                </label>
              </div>
            </div>
          )}

          {/* RETRIEVE STEP */}
          {step.type === "retrieve" && (
            <div className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Query Template (Supports variables)
                </label>
                <Input
                  value={config.query ?? "{{input.topic}}"}
                  onChange={(e) => handleFieldChange("query", e.target.value)}
                  placeholder="e.g. {{input.topic}} or {{input.query}}"
                />
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Mode</label>
                  <select
                    className="w-full bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-200"
                    value={config.mode ?? "hybrid"}
                    onChange={(e) => handleFieldChange("mode", e.target.value)}
                  >
                    <option value="hybrid">Hybrid (Semantic + Keyword)</option>
                    <option value="semantic">Semantic (Vector)</option>
                    <option value="keyword">Keyword (BM25)</option>
                    <option value="auto">Auto Router</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Top K Results</label>
                  <Input
                    type="number"
                    min={1}
                    max={20}
                    value={config.top_k ?? 5}
                    onChange={(e) => handleFieldChange("top_k", parseInt(e.target.value) || 5)}
                  />
                </div>
              </div>
            </div>
          )}

          {/* TOOL STEP */}
          {step.type === "tool" && (
            <div className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Tool Name</label>
                <select
                  className="w-full bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-200"
                  value={config.tool ?? "web_search"}
                  onChange={(e) => handleFieldChange("tool", e.target.value)}
                >
                  <option value="web_search">Web Search (Tavily)</option>
                  <option value="document_extractor">Document Extractor</option>
                  <option value="custom_tool">Custom Tool</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Parameters (JSON or variable map)
                </label>
                <textarea
                  rows={3}
                  value={
                    typeof config.parameters === "object"
                      ? JSON.stringify(config.parameters, null, 2)
                      : config.parameters ?? `{\n  "query": "{{input.topic}}",\n  "max_results": 5\n}`
                  }
                  onChange={(e) => {
                    try {
                      handleFieldChange("parameters", JSON.parse(e.target.value));
                    } catch {
                      handleFieldChange("parameters", e.target.value);
                    }
                  }}
                  className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-xs font-mono text-slate-200"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Max Retries (0-2)</label>
                <Input
                  type="number"
                  min={0}
                  max={2}
                  value={config.max_retries ?? 1}
                  onChange={(e) => handleFieldChange("max_retries", parseInt(e.target.value) || 0)}
                />
              </div>
            </div>
          )}

          {/* GENERATE STEP */}
          {step.type === "generate" && (
            <div className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Prompt Template (Use <code className="text-indigo-300">{"{{input.key}}"}</code> or <code className="text-indigo-300">{"{{steps.id.output}}"}</code>)
                </label>
                <textarea
                  rows={4}
                  value={config.prompt_template ?? "Synthesize answer for: {{input.topic}}"}
                  onChange={(e) => handleFieldChange("prompt_template", e.target.value)}
                  placeholder="Write prompt instructions with dynamic variables..."
                  className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-xs font-mono text-slate-200"
                />
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Routing Mode</label>
                  <select
                    className="w-full bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-200"
                    value={config.mode ?? "smart"}
                    onChange={(e) => handleFieldChange("mode", e.target.value)}
                  >
                    <option value="smart">Smart Router (Tier-Aware)</option>
                    <option value="quality">High Quality (GPT-4o / Claude 3.5)</option>
                    <option value="fast">Fast / Cost-Efficient (GPT-4o-mini)</option>
                    <option value="custom">Specific Model</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Temperature (0.0 - 1.0)</label>
                  <Input
                    type="number"
                    step="0.1"
                    min="0"
                    max="1"
                    value={config.temperature ?? 0.7}
                    onChange={(e) => handleFieldChange("temperature", parseFloat(e.target.value) || 0.7)}
                  />
                </div>
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  System Instructions (Optional)
                </label>
                <textarea
                  rows={2}
                  value={config.system_prompt ?? ""}
                  onChange={(e) => handleFieldChange("system_prompt", e.target.value)}
                  placeholder="You are an expert research analyst..."
                  className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200"
                />
              </div>
            </div>
          )}

          {/* EVALUATE STEP */}
          {step.type === "evaluate" && (
            <div className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Target Output to Evaluate
                </label>
                <Input
                  value={config.target ?? "{{steps.generate.output}}"}
                  onChange={(e) => handleFieldChange("target", e.target.value)}
                  placeholder="e.g. {{steps.generate.output}}"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Context / Grounding Source
                </label>
                <Input
                  value={config.context_source ?? "{{steps.retrieve.results}}"}
                  onChange={(e) => handleFieldChange("context_source", e.target.value)}
                  placeholder="e.g. {{steps.retrieve.results}}"
                />
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Evaluation Mode</label>
                  <select
                    className="w-full bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-200"
                    value={config.mode ?? "grounding"}
                    onChange={(e) => handleFieldChange("mode", e.target.value)}
                  >
                    <option value="grounding">Grounding & Hallucination</option>
                    <option value="completeness">Completeness Check</option>
                    <option value="factual">Factual Accuracy</option>
                    <option value="combined">Comprehensive Multi-Check</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Min Score Threshold</label>
                  <Input
                    type="number"
                    step="0.05"
                    min="0"
                    max="1"
                    value={config.threshold ?? 0.75}
                    onChange={(e) => handleFieldChange("threshold", parseFloat(e.target.value) || 0.75)}
                  />
                </div>
              </div>
            </div>
          )}

          {/* TRANSFORM STEP */}
          {step.type === "transform" && (
            <div className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Operation</label>
                <select
                  className="w-full bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-200"
                  value={config.operation ?? "select"}
                  onChange={(e) => handleFieldChange("operation", e.target.value)}
                >
                  <option value="select">Select Fields</option>
                  <option value="rename">Rename Fields</option>
                  <option value="join">Join Array to String</option>
                  <option value="truncate">Truncate Text</option>
                  <option value="filter">Filter Array</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Source Variable</label>
                <Input
                  value={config.source ?? "steps.retrieve.results"}
                  onChange={(e) => handleFieldChange("source", e.target.value)}
                  placeholder="e.g. steps.retrieve.results"
                />
              </div>
              {config.operation === "select" && (
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Fields (comma-separated)
                  </label>
                  <Input
                    value={Array.isArray(config.fields) ? config.fields.join(", ") : config.fields ?? "title, url, snippet"}
                    onChange={(e) =>
                      handleFieldChange(
                        "fields",
                        e.target.value.split(",").map((s) => s.trim()).filter(Boolean)
                      )
                    }
                    placeholder="title, snippet, url"
                  />
                </div>
              )}
              {config.operation === "join" && (
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Delimiter</label>
                  <Input
                    value={config.delimiter ?? "\n\n"}
                    onChange={(e) => handleFieldChange("delimiter", e.target.value)}
                  />
                </div>
              )}
              {config.operation === "truncate" && (
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Max Characters</label>
                  <Input
                    type="number"
                    value={config.max_length ?? 1000}
                    onChange={(e) => handleFieldChange("max_length", parseInt(e.target.value) || 1000)}
                  />
                </div>
              )}
            </div>
          )}

          {/* CONDITION STEP */}
          {step.type === "condition" && (
            <div className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Left Operand (e.g. <code className="text-indigo-300">steps.evaluate.status</code>)
                </label>
                <Input
                  value={config.left ?? "steps.evaluate.status"}
                  onChange={(e) => handleFieldChange("left", e.target.value)}
                  placeholder="steps.evaluate.status"
                />
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Operator</label>
                  <select
                    className="w-full bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-200"
                    value={config.operator ?? "=="}
                    onChange={(e) => handleFieldChange("operator", e.target.value)}
                  >
                    <option value="==">== (Equals)</option>
                    <option value="!=">!= (Not Equals)</option>
                    <option value=">">&gt; (Greater Than)</option>
                    <option value=">=">&gt;= (Greater or Equal)</option>
                    <option value="<">&lt; (Less Than)</option>
                    <option value="<=">&lt;= (Less or Equal)</option>
                    <option value="exists">exists (Key Exists & Truthy)</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Right Operand</label>
                  <Input
                    value={config.right ?? "warning"}
                    onChange={(e) => handleFieldChange("right", e.target.value)}
                    placeholder="warning, true, 0"
                    disabled={config.operator === "exists"}
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-2 pt-1">
                <div>
                  <label className="block text-xs font-medium text-emerald-400 mb-1">
                    If True Jump To Step
                  </label>
                  <select
                    className="w-full bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-200"
                    value={config.if_true ?? ""}
                    onChange={(e) => handleFieldChange("if_true", e.target.value)}
                  >
                    <option value="">Next Sequential Step</option>
                    {allStepIds
                      .filter((id) => id !== step.id)
                      .map((id) => (
                        <option key={id} value={id}>
                          {id}
                        </option>
                      ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-rose-400 mb-1">
                    If False Jump To Step
                  </label>
                  <select
                    className="w-full bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-200"
                    value={config.if_false ?? ""}
                    onChange={(e) => handleFieldChange("if_false", e.target.value)}
                  >
                    <option value="">Next Sequential Step</option>
                    {allStepIds
                      .filter((id) => id !== step.id)
                      .map((id) => (
                        <option key={id} value={id}>
                          {id}
                        </option>
                      ))}
                  </select>
                </div>
              </div>
            </div>
          )}

          {/* OUTPUT STEP */}
          {step.type === "output" && (
            <div className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Final Output Template
                </label>
                <textarea
                  rows={3}
                  value={config.output_template ?? "{{steps.generate.output}}"}
                  onChange={(e) => handleFieldChange("output_template", e.target.value)}
                  placeholder="{{steps.generate.output}}"
                  className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-xs font-mono text-slate-200"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Format</label>
                <select
                  className="w-full bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-200"
                  value={config.format ?? "markdown"}
                  onChange={(e) => handleFieldChange("format", e.target.value)}
                >
                  <option value="markdown">Markdown Text</option>
                  <option value="json">Structured JSON</option>
                  <option value="text">Plain Text</option>
                </select>
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="flex items-center justify-end gap-2.5 pt-4 border-t border-slate-850 mt-4">
        <Button variant="outline" onClick={onClose}>
          Cancel
        </Button>
        <Button variant="primary" onClick={handleSave}>
          Save Configuration
        </Button>
      </div>
    </Modal>
  );
}
