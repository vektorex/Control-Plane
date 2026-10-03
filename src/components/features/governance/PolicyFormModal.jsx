"use client";

import React, { useState } from "react";
import { X, Plus, Trash2, Shield, AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";

const RULE_TYPES = [
  "model",
  "provider",
  "tool",
  "connector",
  "workflow",
  "prompt",
  "artifact",
  "data",
  "cache",
  "hitl",
  "budget",
  "rate_limit",
];

const ACTIONS = [
  "allow",
  "deny",
  "require_approval",
  "modify",
  "route_to",
  "notify",
];

const OPERATORS = [
  "EQUALS",
  "NOT_EQUALS",
  "CONTAINS",
  "NOT_CONTAINS",
  "IN_LIST",
  "NOT_IN_LIST",
  "GREATER_THAN",
  "LESS_THAN",
  "MATCHES_REGEX",
];

export function PolicyFormModal({
  isOpen,
  onClose,
  onSubmit,
  initialData = null,
  workspaceId = null,
}) {
  const [name, setName] = useState(initialData?.name || "");
  const [description, setDescription] = useState(initialData?.description || "");
  const [scope, setScope] = useState(initialData?.scope || "workspace");
  const [policyType, setPolicyType] = useState(initialData?.policy_type || "model");
  const [failSafeMode, setFailSafeMode] = useState(initialData?.fail_safe_mode || "fail_closed");
  const [rules, setRules] = useState(
    initialData?.active_version?.rules || [
      {
        rule_id: "rule_1",
        rule_type: "model",
        action: "deny",
        priority: 100,
        description: "Default guardrail rule",
        conditions: [
          {
            field: "model_id",
            operator: "IN_LIST",
            value: ["claude-3-opus-restricted"],
          },
        ],
      },
    ]
  );
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  if (!isOpen) return null;

  const handleAddRule = () => {
    setRules([
      ...rules,
      {
        rule_id: `rule_${rules.length + 1}`,
        rule_type: policyType,
        action: "deny",
        priority: 100,
        description: "",
        conditions: [
          {
            field: "model_id",
            operator: "EQUALS",
            value: "",
          },
        ],
      },
    ]);
  };

  const handleRemoveRule = (idx) => {
    setRules(rules.filter((_, i) => i !== idx));
  };

  const handleRuleChange = (idx, field, val) => {
    const updated = [...rules];
    updated[idx][field] = val;
    setRules(updated);
  };

  const handleConditionChange = (rIdx, cIdx, field, val) => {
    const updated = [...rules];
    if (field === "value" && (updated[rIdx].conditions[cIdx].operator === "IN_LIST" || updated[rIdx].conditions[cIdx].operator === "NOT_IN_LIST")) {
      // Split comma separated list if text
      const listVal = typeof val === "string" ? val.split(",").map((s) => s.trim()).filter(Boolean) : val;
      updated[rIdx].conditions[cIdx][field] = listVal;
    } else {
      updated[rIdx].conditions[cIdx][field] = val;
    }
    setRules(updated);
  };

  const handleAddCondition = (rIdx) => {
    const updated = [...rules];
    updated[rIdx].conditions.push({
      field: "task_type",
      operator: "EQUALS",
      value: "",
    });
    setRules(updated);
  };

  const handleRemoveCondition = (rIdx, cIdx) => {
    const updated = [...rules];
    updated[rIdx].conditions = updated[rIdx].conditions.filter((_, i) => i !== cIdx);
    setRules(updated);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!name.trim()) {
      setError("Policy name is required");
      return;
    }
    setError(null);
    setSubmitting(true);
    try {
      await onSubmit({
        name,
        description,
        scope,
        policy_type: policyType,
        fail_safe_mode: failSafeMode,
        workspace_id: scope === "workspace" ? workspaceId : null,
        initial_rules: rules,
      });
      onClose();
    } catch (err) {
      setError(err?.message || "Failed to save policy");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm overflow-y-auto">
      <div className="relative w-full max-w-3xl rounded-xl bg-slate-900 border border-slate-800 shadow-2xl p-6 my-8 text-xs text-slate-200">
        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-indigo-500/10 flex items-center justify-center text-indigo-400 border border-indigo-500/20">
              <Shield className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-white">
                {initialData ? "Edit Governance Policy" : "Create Governance Policy"}
              </h2>
              <p className="text-[11px] text-slate-400">
                Define deterministic guardrails and security constraints for execution engines.
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
          <div className="mt-4 p-3 rounded-lg bg-rose-950/50 border border-rose-800/60 text-rose-300 flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
            <span className="text-xs">{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="mt-5 space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-[11px] font-semibold text-slate-300 uppercase tracking-wider mb-1">
                Policy Name *
              </label>
              <input
                type="text"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Block Unapproved Frontier Models"
                className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-100 focus:outline-none focus:border-indigo-500 text-xs"
              />
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-slate-300 uppercase tracking-wider mb-1">
                Scope
              </label>
              <select
                value={scope}
                onChange={(e) => setScope(e.target.value)}
                className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-100 focus:outline-none focus:border-indigo-500 text-xs"
              >
                <option value="workspace">Workspace Scope</option>
                <option value="organization">Organization Scope</option>
                <option value="project">Project Scope</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-[11px] font-semibold text-slate-300 uppercase tracking-wider mb-1">
                Policy Type
              </label>
              <select
                value={policyType}
                onChange={(e) => setPolicyType(e.target.value)}
                className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-100 focus:outline-none focus:border-indigo-500 text-xs capitalize"
              >
                {RULE_TYPES.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-slate-300 uppercase tracking-wider mb-1">
                Fail-Safe Mode
              </label>
              <select
                value={failSafeMode}
                onChange={(e) => setFailSafeMode(e.target.value)}
                className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-100 focus:outline-none focus:border-indigo-500 text-xs"
              >
                <option value="fail_closed">Fail Closed (Default - Deny on unknown/unreachable)</option>
                <option value="fail_open">Fail Open (Allow with audit alert on unreachable)</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-[11px] font-semibold text-slate-300 uppercase tracking-wider mb-1">
              Description / Business Rationale
            </label>
            <input
              type="text"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="e.g. Compliance guardrail preventing execution of unvetted models or tools"
              className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-100 focus:outline-none focus:border-indigo-500 text-xs"
            />
          </div>

          {/* Rules Builder */}
          <div className="pt-2">
            <div className="flex items-center justify-between pb-2 border-b border-slate-800">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-300">
                Policy Rules ({rules.length})
              </span>
              <button
                type="button"
                onClick={handleAddRule}
                className="inline-flex items-center gap-1 px-2 py-1 rounded bg-indigo-600/20 text-indigo-300 hover:bg-indigo-600/30 border border-indigo-500/30 text-[11px] font-medium transition-colors"
              >
                <Plus className="w-3 h-3" />
                Add Rule
              </button>
            </div>

            <div className="mt-3 space-y-3 max-h-72 overflow-y-auto pr-1">
              {rules.map((r, rIdx) => (
                <div
                  key={rIdx}
                  className="p-3 rounded-lg bg-slate-950/80 border border-slate-800/80 space-y-2.5"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-[10px] text-slate-400">
                      Rule #{rIdx + 1}
                    </span>
                    <button
                      type="button"
                      onClick={() => handleRemoveRule(rIdx)}
                      className="text-slate-400 hover:text-rose-400 transition-colors p-1"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                    <div>
                      <span className="text-[10px] text-slate-400">Action</span>
                      <select
                        value={r.action}
                        onChange={(e) => handleRuleChange(rIdx, "action", e.target.value)}
                        className="w-full mt-0.5 px-2 py-1 rounded bg-slate-900 border border-slate-800 text-slate-100 text-xs"
                      >
                        {ACTIONS.map((a) => (
                          <option key={a} value={a}>
                            {a}
                          </option>
                        ))}
                      </select>
                    </div>

                    <div>
                      <span className="text-[10px] text-slate-400">Priority</span>
                      <input
                        type="number"
                        min="1"
                        max="1000"
                        value={r.priority}
                        onChange={(e) => handleRuleChange(rIdx, "priority", parseInt(e.target.value) || 100)}
                        className="w-full mt-0.5 px-2 py-1 rounded bg-slate-900 border border-slate-800 text-slate-100 text-xs"
                      />
                    </div>

                    <div>
                      <span className="text-[10px] text-slate-400">Rule Description</span>
                      <input
                        type="text"
                        value={r.description || ""}
                        onChange={(e) => handleRuleChange(rIdx, "description", e.target.value)}
                        placeholder="Rationale"
                        className="w-full mt-0.5 px-2 py-1 rounded bg-slate-900 border border-slate-800 text-slate-100 text-xs"
                      />
                    </div>
                  </div>

                  {/* Conditions */}
                  <div className="pt-1.5 border-t border-slate-850 space-y-1.5">
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] text-slate-400 font-semibold uppercase">
                        Conditions (ALL must match)
                      </span>
                      <button
                        type="button"
                        onClick={() => handleAddCondition(rIdx)}
                        className="text-[10px] text-indigo-400 hover:text-indigo-300 font-medium"
                      >
                        + Condition
                      </button>
                    </div>

                    {r.conditions?.map((c, cIdx) => (
                      <div key={cIdx} className="flex items-center gap-2">
                        <input
                          type="text"
                          value={c.field}
                          onChange={(e) => handleConditionChange(rIdx, cIdx, "field", e.target.value)}
                          placeholder="field (e.g. model_id)"
                          className="flex-1 px-2 py-1 rounded bg-slate-900 border border-slate-800 text-slate-100 text-[11px]"
                        />
                        <select
                          value={c.operator}
                          onChange={(e) => handleConditionChange(rIdx, cIdx, "operator", e.target.value)}
                          className="w-28 px-1.5 py-1 rounded bg-slate-900 border border-slate-800 text-slate-100 text-[11px]"
                        >
                          {OPERATORS.map((op) => (
                            <option key={op} value={op}>
                              {op}
                            </option>
                          ))}
                        </select>
                        <input
                          type="text"
                          value={Array.isArray(c.value) ? c.value.join(", ") : c.value ?? ""}
                          onChange={(e) => handleConditionChange(rIdx, cIdx, "value", e.target.value)}
                          placeholder="value or comma separated"
                          className="flex-1 px-2 py-1 rounded bg-slate-900 border border-slate-800 text-slate-100 text-[11px]"
                        />
                        {r.conditions.length > 1 && (
                          <button
                            type="button"
                            onClick={() => handleRemoveCondition(rIdx, cIdx)}
                            className="text-slate-400 hover:text-rose-400 p-1"
                          >
                            <Trash2 className="w-3 h-3" />
                          </button>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="pt-4 border-t border-slate-800 flex items-center justify-end gap-2.5">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700 transition-colors font-medium text-xs"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="px-4 py-2 rounded-lg bg-indigo-600 text-white hover:bg-indigo-500 transition-colors font-medium text-xs disabled:opacity-50"
            >
              {submitting ? "Saving Policy..." : "Save Policy"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
