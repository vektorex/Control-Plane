"use client";

import React from "react";
import Link from "next/link";
import { ArrowLeft, Terminal, ShieldCheck, BookOpen } from "lucide-react";
import { ApiExplorer } from "@/components/features/developer/ApiExplorer";

export default function DeveloperApiExplorerPage() {
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
        <Link href="/app/developer/docs" className="text-blue-400 hover:underline shrink-0 ml-4 font-medium flex items-center gap-1">
          <BookOpen className="w-3.5 h-3.5" />
          API Reference
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
            <span className="text-slate-200">API Explorer</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <Terminal className="w-6 h-6 text-indigo-400" />
            Public API Explorer
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Interactive request builder and tester for versioned <code className="text-indigo-400">/api/v1</code> endpoints. Test your scoped API keys with real-time response inspection.
          </p>
        </div>
      </div>

      {/* Explorer Component */}
      <ApiExplorer />
    </div>
  );
}
