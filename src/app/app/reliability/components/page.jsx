"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { ArrowLeft, Server, RefreshCw } from "lucide-react";
import { reliabilityService } from "@/services/reliability";
import { ComponentListTable } from "@/components/features/reliability/ComponentListTable";

export default function ReliabilityComponentsPage() {
  const [components, setComponents] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState("");

  const fetchData = useCallback(async () => {
    try {
      setIsLoading(true);
      setErrorMsg("");
      const res = await reliabilityService.listComponents({ limit: 100 });
      setComponents(res || []);
    } catch (err) {
      setErrorMsg(err.message || "Failed to load components.");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div className="space-y-1">
          <Link
            href="/app/reliability"
            className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 transition mb-1"
          >
            <ArrowLeft className="w-3.5 h-3.5" /> Back to Reliability Dashboard
          </Link>
          <div className="flex items-center gap-2">
            <Server className="w-6 h-6 text-indigo-400" />
            <h1 className="text-xl font-bold text-white tracking-tight">
              Component Registry
            </h1>
          </div>
          <p className="text-xs text-slate-400">
            All registered AI Work Layer subsystems with real-time operational health and failure counters.
          </p>
        </div>

        <button
          onClick={fetchData}
          disabled={isLoading}
          className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
          title="Refresh components"
        >
          <RefreshCw className={`w-4 h-4 ${isLoading ? "animate-spin" : ""}`} />
        </button>
      </div>

      {errorMsg && (
        <div className="p-4 rounded-xl bg-red-950/40 border border-red-800 text-red-200 text-sm">
          {errorMsg}
        </div>
      )}

      <ComponentListTable components={components} onRefresh={fetchData} />
    </div>
  );
}
