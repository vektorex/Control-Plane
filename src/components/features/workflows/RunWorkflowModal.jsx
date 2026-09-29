"use client";

import React, { useState, useEffect } from "react";
import { Modal } from "@/components/ui/Modal";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { workflowService } from "@/services/workflows";
import { useRouter } from "next/navigation";
import { Play, AlertCircle, Loader2 } from "lucide-react";

export function RunWorkflowModal({ isOpen, onClose, workflow }) {
  const router = useRouter();
  const [formData, setFormData] = useState({});
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState(null);

  const inputSchema = workflow?.input_schema || {};
  const schemaKeys = Object.keys(inputSchema);

  useEffect(() => {
    if (workflow) {
      const initial = {};
      Object.entries(inputSchema).forEach(([k, spec]) => {
        if (spec.default !== undefined) {
          initial[k] = spec.default;
        } else if (spec.type === "boolean") {
          initial[k] = false;
        } else if (spec.type === "number") {
          initial[k] = 0;
        } else if (spec.type === "object" || spec.type === "array") {
          initial[k] = "";
        } else {
          initial[k] = "";
        }
      });
      setFormData(initial);
      setError(null);
    }
  }, [workflow]);

  const handleChange = (key, value) => {
    setFormData((prev) => ({
      ...prev,
      [key]: value,
    }));
  };

  const handleExecute = async (e) => {
    e.preventDefault();
    if (!workflow?.id) return;

    try {
      setIsRunning(true);
      setError(null);

      // Format payload based on types
      const processed = {};
      for (const [k, spec] of Object.entries(inputSchema)) {
        let val = formData[k];
        if (spec.type === "number") {
          val = val === "" || isNaN(Number(val)) ? 0 : Number(val);
        } else if (spec.type === "boolean") {
          val = Boolean(val);
        } else if ((spec.type === "object" || spec.type === "array") && typeof val === "string" && val.trim()) {
          try {
            val = JSON.parse(val);
          } catch (pErr) {
            throw new Error(`Field '${k}' must be valid JSON: ${pErr.message}`);
          }
        }
        processed[k] = val;
      }

      const res = await workflowService.runWorkflow(workflow.id, {
        input_data: processed,
        version: workflow.version,
      });

      onClose();
      router.push(`/app/workflows/${workflow.id}/runs/${res.id}`);
    } catch (err) {
      console.error("[RunWorkflowModal] Execution error:", err);
      setError(err.message || "Failed to execute workflow run");
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`Run Workflow: ${workflow?.name || ""}`}
      description={`Execute version ${workflow?.version || 1} with parameters`}
    >
      <form onSubmit={handleExecute} className="space-y-4">
        {error && (
          <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded-lg text-rose-400 text-xs flex items-start gap-2">
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        {schemaKeys.length === 0 ? (
          <div className="p-4 bg-slate-900 border border-slate-800 rounded-lg text-slate-300 text-xs">
            This workflow defines no required input parameters. Click Run to trigger execution.
          </div>
        ) : (
          <div className="space-y-3.5 max-h-[60vh] overflow-y-auto pr-1">
            {schemaKeys.map((key) => {
              const spec = inputSchema[key] || {};
              const isRequired = spec.required ?? true;
              const type = spec.type || "string";

              return (
                <div key={key} className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <label className="text-xs font-semibold text-slate-300">
                      {key}{" "}
                      {isRequired ? (
                        <span className="text-rose-400">*</span>
                      ) : (
                        <span className="text-slate-400 text-[10px] font-normal">(optional)</span>
                      )}
                    </label>
                    <span className="text-[10px] text-indigo-400 font-mono uppercase">
                      {type}
                    </span>
                  </div>

                  {spec.description && (
                    <p className="text-[11px] text-slate-400">{spec.description}</p>
                  )}

                  {type === "boolean" ? (
                    <div className="flex items-center gap-2 pt-1">
                      <input
                        type="checkbox"
                        id={`input-${key}`}
                        checked={Boolean(formData[key])}
                        onChange={(e) => handleChange(key, e.target.checked)}
                        className="rounded bg-slate-900 border-slate-700 text-indigo-600 focus:ring-indigo-500 w-4 h-4"
                      />
                      <label htmlFor={`input-${key}`} className="text-xs text-slate-300 cursor-pointer">
                        Enable {key}
                      </label>
                    </div>
                  ) : type === "number" ? (
                    <Input
                      type="number"
                      value={formData[key] ?? ""}
                      onChange={(e) => handleChange(key, e.target.value)}
                      placeholder={spec.description || `Enter ${key}...`}
                      required={isRequired}
                    />
                  ) : type === "object" || type === "array" ? (
                    <textarea
                      rows={3}
                      value={typeof formData[key] === "object" ? JSON.stringify(formData[key], null, 2) : formData[key] ?? ""}
                      onChange={(e) => handleChange(key, e.target.value)}
                      placeholder={type === "array" ? `["item1", "item2"]` : `{"key": "value"}`}
                      className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-xs font-mono text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 resize-y"
                      required={isRequired}
                    />
                  ) : (
                    <textarea
                      rows={2}
                      value={formData[key] ?? ""}
                      onChange={(e) => handleChange(key, e.target.value)}
                      placeholder={spec.description || `Enter ${key}...`}
                      className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 resize-y"
                      required={isRequired}
                    />
                  )}
                </div>
              );
            })}
          </div>
        )}

        <div className="flex items-center justify-end gap-2.5 pt-3 border-t border-slate-850">
          <Button type="button" variant="outline" onClick={onClose} disabled={isRunning}>
            Cancel
          </Button>
          <Button
            type="submit"
            variant="primary"
            disabled={isRunning}
            className="gap-2 bg-emerald-600 hover:bg-emerald-500 text-white"
          >
            {isRunning ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Executing Pipeline...</span>
              </>
            ) : (
              <>
                <Play className="w-4 h-4 fill-white" />
                <span>Start Run</span>
              </>
            )}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
