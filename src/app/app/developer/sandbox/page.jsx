"use client";

import React from "react";
import Link from "next/link";
import { ArrowLeft, Play, ShieldAlert, Sparkles, ShieldCheck } from "lucide-react";
import { SandboxRunner } from "@/components/features/developer/SandboxRunner";

export default function DeveloperSandboxPage() {
  return (
    <div className="space-y-6">
      {/* Disclaimer Banner */}
      <div className="p-3.5 bg-blue-500/10 border border-blue-500/20 rounded-xl flex items-center justify-between text-xs text-blue-300">
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-blue-400 shrink-0" />
          <span>
            The Public API provides controlled programmatic access to the platform. API availability, limits, and capabilities are subject to the platform&apos;s configured policies and operational state.
          </span>
        </div>
        <Link href="/app/developer/docs" className="text-blue-400 hover:underline shrink-0 ml-4 font-medium">
          View Docs
        </Link>
      </div>

      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs text-slate-400 mb-1">
            <Link href="/app/developer" className="hover:text-white transition flex items-center gap-1">
              <ArrowLeft className="w-3.5 h-3.5" />
              Developer Platform
            </Link>
            <span>/</span>
            <span className="text-slate-200">API Sandbox</span>
          </div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
              <Play className="w-6 h-6 text-indigo-400" />
              API Sandbox
            </h1>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center gap-1">
              <Sparkles className="w-3 h-3" />
              Isolated Development Environment
            </span>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Safely test Public API endpoints, view structured requests, inspect raw responses, and verify governance rules without impacting production data.
          </p>
        </div>
      </div>

      {/* Security notice */}
      <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl flex items-start gap-3 text-xs text-slate-400">
        <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold text-slate-300">Sandbox Safety Guarantee:</span>{" "}
          Destructive operations and production key access are strictly blocked in sandbox mode. All requests are routed through Step 32 Governance and tagged with unique request IDs for end-to-end auditability.
        </div>
      </div>

      {/* Sandbox Runner Component */}
      <SandboxRunner />
    </div>
  );
}
