"use client";

import React from "react";
import { ShieldCheck, AlertTriangle, CheckCircle2, XCircle, ArrowUpRight } from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";

export function SideEffectPreviewPanel({ sideEffects = [] }) {
  return (
    <Card className="p-5 border-amber-500/30 bg-zinc-900/80 shadow-md">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 text-amber-400" />
          <h3 className="text-base font-semibold text-zinc-100">
            Actions That Would Have Happened
          </h3>
        </div>
        <Badge variant="outline" className="text-amber-400 border-amber-500/40 bg-amber-950/20">
          {sideEffects.length} Intercepted
        </Badge>
      </div>

      <p className="text-xs text-zinc-400 mb-4">
        The sandbox intercepted the following side effects. In production, these actions would modify external databases, APIs, or systems.
      </p>

      {sideEffects.length === 0 ? (
        <div className="rounded-md border border-zinc-800 bg-zinc-950/40 p-6 text-center text-sm text-zinc-500">
          No external side-effect mutations were attempted during this simulation.
        </div>
      ) : (
        <div className="space-y-3">
          {sideEffects.map((se, idx) => (
            <div
              key={se.id || idx}
              className="p-3.5 rounded-lg border border-zinc-800 bg-zinc-950/60 hover:border-zinc-700 transition"
            >
              <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs font-semibold px-2 py-0.5 rounded bg-zinc-800 text-purple-300">
                    {se.intended_action}
                  </span>
                  <span className="text-xs text-zinc-400">on target</span>
                  <span className="font-mono text-xs text-zinc-200">{se.target}</span>
                </div>

                <div className="flex items-center gap-2">
                  {se.would_require_approval && (
                    <Badge variant="outline" className="border-blue-500/40 text-blue-300 bg-blue-950/20 text-[10px]">
                      WOULD REQUIRE APPROVAL
                    </Badge>
                  )}
                  <Badge variant="outline" className="border-red-500/40 text-red-300 bg-red-950/20 text-[10px]">
                    PRODUCTION: BLOCKED
                  </Badge>
                  <Badge variant="outline" className="border-green-500/40 text-green-300 bg-green-950/20 text-[10px]">
                    SANDBOX: WOULD EXECUTE
                  </Badge>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs mt-2 pt-2 border-t border-zinc-800/80">
                <div>
                  <span className="text-zinc-500 block mb-0.5">Parameters Summary:</span>
                  <pre className="font-mono text-[11px] text-zinc-300 bg-zinc-900/80 p-1.5 rounded overflow-x-auto max-h-24">
                    {typeof se.parameters === "object" ? JSON.stringify(se.parameters, null, 2) : String(se.parameters)}
                  </pre>
                </div>
                <div>
                  <span className="text-zinc-500 block mb-0.5">Simulated Result:</span>
                  <pre className="font-mono text-[11px] text-emerald-300/90 bg-zinc-900/80 p-1.5 rounded overflow-x-auto max-h-24">
                    {typeof se.simulated_result === "object" ? JSON.stringify(se.simulated_result, null, 2) : String(se.simulated_result)}
                  </pre>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}
