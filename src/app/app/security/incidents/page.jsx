"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { ArrowLeft, ShieldAlert, RefreshCw } from "lucide-react";
import { securityService } from "@/services/security";
import { IncidentListTable } from "@/components/features/security/IncidentListTable";

export default function SecurityIncidentsPage() {
  const [incidents, setIncidents] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState("");

  const fetchData = useCallback(async () => {
    try {
      setIsLoading(true);
      setErrorMsg("");
      const res = await securityService.listIncidents({ limit: 100 });
      setIncidents(res?.items || []);
    } catch (err) {
      setErrorMsg(err.message || "Failed to load incidents.");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return (
    <div className="space-y-6 pb-12">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div className="flex items-center gap-3">
          <Link
            href="/app/security"
            className="p-2 rounded-lg bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
              <ShieldAlert className="w-5 h-5 text-red-400" />
              Security Incidents
            </h1>
            <p className="text-xs text-slate-400">
              Correlated security incidents requiring triage, containment, and audit resolution.
            </p>
          </div>
        </div>

        <button
          onClick={() => fetchData()}
          disabled={isLoading}
          className="p-2 rounded-lg bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-300 transition-colors"
        >
          <RefreshCw className={`w-4 h-4 ${isLoading ? "animate-spin text-indigo-400" : ""}`} />
        </button>
      </div>

      {errorMsg && (
        <div className="p-3 bg-red-950/50 border border-red-800 rounded-lg text-xs text-red-300">
          {errorMsg}
        </div>
      )}

      <IncidentListTable incidents={incidents} onRefresh={fetchData} />
    </div>
  );
}
