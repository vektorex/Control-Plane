"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  FileCode2,
  ArrowLeft,
  Save,
  Info,
  AlertTriangle,
  Code,
  ShieldAlert,
} from "lucide-react";
import { promptService } from "@/services/prompts";
import { Button } from "@/components/ui/Button";

const PROMPT_TYPES = [
  { value: "task", label: "Task (General AI execution task)" },
  { value: "planner", label: "Planner (Execution step generation)" },
  { value: "evaluator", label: "Evaluator (Verification & grading)" },
  { value: "workflow", label: "Workflow (Multi-step pipeline prompt)" },
  { value: "system", label: "System (High-level persona & constraints)" },
  { value: "instruction", label: "Instruction (Modular reusable guidance)" },
  { value: "transform", label: "Transform (Data restructuring/formatting)" },
];

export default function NewPromptPage() {
  const router = useRouter();

  const [name, setName] = useState("");
  const [key, setKey] = useState("");
  const [promptType, setPromptType] = useState("task");
  const [description, setDescription] = useState("");
  const [content, setContent] = useState(
    "You are a specialized AI assistant.\n\nTask:\n{{input.topic}}\n\nDetails:\n{{input.details}}\n\nDeliver the output formatted cleanly."
  );
  const [variableSchemaStr, setVariableSchemaStr] = useState(
    JSON.stringify(
      {
        "input.topic": { type: "string", required: true, description: "Main topic or goal" },
        "input.details": { type: "string", required: false, description: "Additional instructions" },
      },
      null,
      2
    )
  );
  const [changeSummary, setChangeSummary] = useState("Initial prompt creation");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    // Validation
    const cleanKey = key.trim().toLowerCase();
    if (!cleanKey) {
      setError("Prompt key is required (e.g. task.my_task)");
      return;
    }
    if (!/^[a-z0-9_-]+(\.[a-z0-9_-]+)+$/.test(cleanKey)) {
      setError("Prompt key must use dot-notation namespace (e.g. task.summarize, workflow.report)");
      return;
    }

    let parsedSchema = null;
    if (variableSchemaStr.trim()) {
      try {
        parsedSchema = JSON.parse(variableSchemaStr);
      } catch (err) {
        setError(`Invalid Variable Schema JSON: ${err.message}`);
        return;
      }
    }

    try {
      setSubmitting(true);
      const res = await promptService.createPrompt({
        key: cleanKey,
        name: name.trim() || cleanKey,
        description: description.trim() || null,
        prompt_type: promptType,
        initial_content: content,
        variable_schema: parsedSchema,
        change_summary: changeSummary,
      });

      router.push(`/app/prompts/${res.id}`);
    } catch (err) {
      console.error("Create prompt error:", err);
      setError(err.message || "Failed to create prompt");
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Breadcrumb & Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div className="flex items-center gap-3">
          <Link
            href="/app/prompts"
            className="p-1.5 rounded-lg border border-slate-800 bg-slate-900 text-slate-400 hover:text-white"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <h1 className="text-xl font-bold text-white flex items-center gap-2">
              Create Governed Prompt
            </h1>
            <p className="text-xs text-slate-400">
              Register a new versioned AI prompt asset with safe variable bindings.
            </p>
          </div>
        </div>
      </div>

      {error && (
        <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0 text-rose-400" />
          <span>{error}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Core Metadata */}
        <div className="p-5 rounded-xl border border-slate-800 bg-slate-900/40 space-y-4">
          <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
            <FileCode2 className="w-4 h-4 text-indigo-400" />
            Prompt Identification & Scope
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">
                Prompt Key <span className="text-rose-400">*</span>
              </label>
              <input
                type="text"
                placeholder="e.g. task.document_analysis"
                value={key}
                onChange={(e) => setKey(e.target.value)}
                required
                className="w-full px-3 py-2 text-xs font-mono bg-slate-950 border border-slate-800 rounded-lg text-slate-100 placeholder-slate-600 focus:outline-none focus:border-indigo-500"
              />
              <p className="text-[11px] text-slate-500 mt-1">
                Unique identifier used by application code and workflows.
              </p>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">
                Display Name <span className="text-rose-400">*</span>
              </label>
              <input
                type="text"
                placeholder="e.g. Document Analysis Engine"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                className="w-full px-3 py-2 text-xs bg-slate-950 border border-slate-800 rounded-lg text-slate-100 placeholder-slate-600 focus:outline-none focus:border-indigo-500"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">
                Prompt Category / Type
              </label>
              <select
                value={promptType}
                onChange={(e) => setPromptType(e.target.value)}
                className="w-full px-3 py-2 text-xs bg-slate-950 border border-slate-800 rounded-lg text-slate-200 focus:outline-none"
              >
                {PROMPT_TYPES.map((t) => (
                  <option key={t.value} value={t.value}>
                    {t.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">
                Description (Optional)
              </label>
              <input
                type="text"
                placeholder="Short summary of this prompt's objective..."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="w-full px-3 py-2 text-xs bg-slate-950 border border-slate-800 rounded-lg text-slate-100 placeholder-slate-600 focus:outline-none focus:border-indigo-500"
              />
            </div>
          </div>
        </div>

        {/* Content & Template Variables */}
        <div className="p-5 rounded-xl border border-slate-800 bg-slate-900/40 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
              <Code className="w-4 h-4 text-emerald-400" />
              Initial Prompt Template (v1 Draft)
            </h2>
            <span className="text-[11px] text-slate-400 font-mono bg-slate-950 px-2 py-0.5 rounded border border-slate-800">
              Safe namespaces: input.*, task.*, project.*, context.*, workflow.*, memory.*
            </span>
          </div>

          <div>
            <textarea
              rows={10}
              value={content}
              onChange={(e) => setContent(e.target.value)}
              className="w-full p-3 font-mono text-xs bg-slate-950 border border-slate-800 rounded-lg text-slate-100 placeholder-slate-600 focus:outline-none focus:border-indigo-500 resize-y"
              placeholder="Enter prompt content with {{namespace.variable}} placeholders..."
            />
          </div>

          <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800 text-[11px] text-slate-400 space-y-1.5">
            <div className="font-semibold text-slate-300 flex items-center gap-1.5">
              <ShieldAlert className="w-3.5 h-3.5 text-amber-400" />
              Security Invariant:
            </div>
            <p>
              Template variables are substituted as literal data in a single pass. Arbitrary Python/JavaScript/eval execution is strictly blocked. Secrets and API keys are blocked by the pre-commit scanner.
            </p>
          </div>
        </div>

        {/* Variable Schema Definition */}
        <div className="p-5 rounded-xl border border-slate-800 bg-slate-900/40 space-y-3">
          <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
            <Info className="w-4 h-4 text-indigo-400" />
            Variable Validation Schema (JSON)
          </h2>
          <p className="text-xs text-slate-400">
            Define allowed variables and types (string, number, boolean, string_array, json) to validate inputs before rendering.
          </p>

          <textarea
            rows={5}
            value={variableSchemaStr}
            onChange={(e) => setVariableSchemaStr(e.target.value)}
            className="w-full p-3 font-mono text-xs bg-slate-950 border border-slate-800 rounded-lg text-slate-100 focus:outline-none focus:border-indigo-500"
          />
        </div>

        {/* Change Summary */}
        <div className="p-5 rounded-xl border border-slate-800 bg-slate-900/40 space-y-2">
          <label className="block text-xs font-medium text-slate-300">
            Change Summary
          </label>
          <input
            type="text"
            value={changeSummary}
            onChange={(e) => setChangeSummary(e.target.value)}
            className="w-full px-3 py-2 text-xs bg-slate-950 border border-slate-800 rounded-lg text-slate-100 focus:outline-none"
          />
        </div>

        {/* Submission actions */}
        <div className="flex items-center justify-end gap-3 pt-2">
          <Link href="/app/prompts">
            <Button variant="ghost" size="sm" type="button">
              Cancel
            </Button>
          </Link>
          <Button
            size="sm"
            type="submit"
            disabled={submitting}
            className="bg-indigo-600 hover:bg-indigo-500 text-white flex items-center gap-1.5"
          >
            <Save className="w-3.5 h-3.5" />
            {submitting ? "Creating Asset..." : "Create Prompt & Initial Draft"}
          </Button>
        </div>
      </form>
    </div>
  );
}
