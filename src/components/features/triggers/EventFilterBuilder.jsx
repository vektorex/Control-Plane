"use client";

import React from "react";
import { Plus, Trash2, Sliders, CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Badge } from "@/components/ui/Badge";

const OPERATORS = [
  { value: "equals", label: "Equals (==)" },
  { value: "not_equals", label: "Not Equals (!=)" },
  { value: "contains", label: "Contains (in list/string)" },
  { value: "starts_with", label: "Starts With" },
  { value: "ends_with", label: "Ends With" },
  { value: "exists", label: "Exists / Is Present" },
  { value: "greater_than", label: "Greater Than (>)" },
  { value: "less_than", label: "Less Than (<)" },
  { value: "greater_or_equal", label: "Greater or Equal (>=)" },
  { value: "less_or_equal", label: "Less or Equal (<=)" },
];

export function EventFilterBuilder({ filterConfig, onChange }) {
  const logic = filterConfig?.logic || "AND";
  const rules = filterConfig?.rules || [];

  const handleAddRule = () => {
    const updated = {
      logic,
      rules: [
        ...rules,
        { field: "payload.repository.full_name", operator: "equals", value: "" },
      ],
    };
    onChange(updated);
  };

  const handleRemoveRule = (index) => {
    const nextRules = rules.filter((_, i) => i !== index);
    onChange({ logic, rules: nextRules });
  };

  const handleUpdateRule = (index, key, val) => {
    const nextRules = [...rules];
    nextRules[index] = { ...nextRules[index], [key]: val };
    onChange({ logic, rules: nextRules });
  };

  const toggleLogic = () => {
    onChange({ logic: logic === "AND" ? "OR" : "AND", rules });
  };

  return (
    <div className="space-y-4 rounded-xl border border-slate-800 bg-slate-900/60 p-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Sliders className="h-4 w-4 text-indigo-400" />
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-300">
            Event Filtering Rules
          </span>
          <Badge variant="outline" className="text-[10px]">
            {rules.length} condition{rules.length === 1 ? "" : "s"}
          </Badge>
        </div>

        {rules.length > 1 && (
          <div className="flex items-center gap-1.5 rounded-lg border border-slate-700 bg-slate-800 p-0.5">
            <button
              type="button"
              onClick={toggleLogic}
              className={`rounded px-2 py-0.5 text-xs font-semibold transition-all ${
                logic === "AND"
                  ? "bg-indigo-600 text-white shadow-sm"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              AND (All Match)
            </button>
            <button
              type="button"
              onClick={toggleLogic}
              className={`rounded px-2 py-0.5 text-xs font-semibold transition-all ${
                logic === "OR"
                  ? "bg-amber-600 text-white shadow-sm"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              OR (Any Match)
            </button>
          </div>
        )}
      </div>

      {rules.length === 0 ? (
        <div className="rounded-lg border border-dashed border-slate-800 p-4 text-center">
          <p className="text-xs text-slate-500">
            No filter rules defined. All incoming events will trigger the workflow.
          </p>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={handleAddRule}
            className="mt-2 text-xs text-indigo-400 hover:text-indigo-300"
          >
            <Plus className="mr-1 h-3.5 w-3.5" />
            Add First Rule
          </Button>
        </div>
      ) : (
        <div className="space-y-2.5">
          {rules.map((rule, idx) => (
            <div
              key={idx}
              className="flex items-center gap-2 rounded-lg border border-slate-800/80 bg-slate-950/60 p-2 text-xs"
            >
              {idx > 0 && (
                <span
                  className={`shrink-0 rounded px-1.5 py-0.5 text-[10px] font-bold ${
                    logic === "AND" ? "bg-indigo-950 text-indigo-300 border border-indigo-800/50" : "bg-amber-950 text-amber-300 border border-amber-800/50"
                  }`}
                >
                  {logic}
                </span>
              )}

              <div className="flex-1">
                <input
                  type="text"
                  value={rule.field}
                  onChange={(e) => handleUpdateRule(idx, "field", e.target.value)}
                  placeholder="e.g. payload.repository.full_name"
                  className="w-full rounded-md border border-slate-700 bg-slate-900 px-2.5 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:border-indigo-500 focus:outline-none"
                />
              </div>

              <div className="w-48">
                <select
                  value={rule.operator}
                  onChange={(e) => handleUpdateRule(idx, "operator", e.target.value)}
                  className="w-full rounded-md border border-slate-700 bg-slate-900 px-2 py-1.5 text-xs text-slate-200 focus:border-indigo-500 focus:outline-none"
                >
                  {OPERATORS.map((op) => (
                    <option key={op.value} value={op.value}>
                      {op.label}
                    </option>
                  ))}
                </select>
              </div>

              {rule.operator !== "exists" && (
                <div className="flex-1">
                  <input
                    type="text"
                    value={rule.value ?? ""}
                    onChange={(e) => handleUpdateRule(idx, "value", e.target.value)}
                    placeholder="Expected value, e.g. bug"
                    className="w-full rounded-md border border-slate-700 bg-slate-900 px-2.5 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:border-indigo-500 focus:outline-none"
                  />
                </div>
              )}

              <button
                type="button"
                onClick={() => handleRemoveRule(idx)}
                className="shrink-0 p-1 text-slate-500 hover:text-rose-400"
                title="Remove condition"
              >
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
          ))}

          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={handleAddRule}
            className="text-xs text-slate-300"
          >
            <Plus className="mr-1 h-3.5 w-3.5" />
            Add Rule
          </Button>
        </div>
      )}

      {/* Live Preview Expression */}
      {rules.length > 0 && (
        <div className="rounded-lg border border-slate-800/80 bg-slate-950/80 p-2.5">
          <div className="flex items-center gap-1.5 text-[11px] text-slate-400">
            <CheckCircle2 className="h-3 w-3 text-emerald-400" />
            <span className="font-semibold text-slate-300">Deterministic Match Expression:</span>
          </div>
          <p className="mt-1 font-mono text-[11px] text-indigo-300">
            {rules
              .map((r) =>
                r.operator === "exists"
                  ? `${r.field} exists`
                  : `${r.field} ${r.operator} "${r.value ?? ""}"`
              )
              .join(` ${logic} `)}
          </p>
        </div>
      )}
    </div>
  );
}
