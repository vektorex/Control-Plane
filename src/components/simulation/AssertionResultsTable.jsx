"use client";

import React from "react";
import { CheckCircle2, XCircle, AlertCircle, ShieldCheck } from "lucide-react";
import { Badge } from "@/components/ui/Badge";

export function AssertionResultsTable({ assertions = [] }) {
  if (!assertions || assertions.length === 0) {
    return (
      <div className="rounded-lg border border-zinc-800 bg-zinc-950/40 p-6 text-center text-sm text-zinc-500">
        No assertions configured for this run.
      </div>
    );
  }

  const passedCount = assertions.filter((a) => a.passed).length;

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between text-xs text-zinc-400">
        <span>Evaluated {assertions.length} assertions</span>
        <span className="font-medium text-emerald-400">
          {passedCount} / {assertions.length} Passed
        </span>
      </div>

      <div className="rounded-lg border border-zinc-800 overflow-hidden bg-zinc-900/60">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="border-b border-zinc-800 bg-zinc-950/80 text-zinc-400">
              <th className="p-3 font-medium">Status</th>
              <th className="p-3 font-medium">Assertion Type</th>
              <th className="p-3 font-medium">Expected</th>
              <th className="p-3 font-medium">Actual</th>
              <th className="p-3 font-medium">Severity</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-800/60">
            {assertions.map((a, idx) => (
              <tr key={a.id || idx} className="hover:bg-zinc-800/30 transition">
                <td className="p-3">
                  {a.passed ? (
                    <span className="inline-flex items-center gap-1 text-emerald-400 font-medium">
                      <CheckCircle2 className="w-4 h-4 text-emerald-400" /> Passed
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 text-rose-400 font-medium">
                      <XCircle className="w-4 h-4 text-rose-400" /> Failed
                    </span>
                  )}
                </td>
                <td className="p-3 font-mono text-zinc-200">{a.assertion_type}</td>
                <td className="p-3 font-mono text-zinc-400">
                  {a.expected !== undefined && a.expected !== null ? JSON.stringify(a.expected) : "—"}
                </td>
                <td className="p-3 font-mono text-zinc-300">
                  {a.actual !== undefined && a.actual !== null ? (
                    typeof a.actual === "object" ? JSON.stringify(a.actual) : String(a.actual)
                  ) : "—"}
                </td>
                <td className="p-3">
                  <Badge
                    variant="outline"
                    className={
                      a.severity === "error"
                        ? "border-rose-500/30 text-rose-300 bg-rose-950/20 text-[10px]"
                        : "border-amber-500/30 text-amber-300 bg-amber-950/20 text-[10px]"
                    }
                  >
                    {a.severity?.toUpperCase() || "ERROR"}
                  </Badge>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
