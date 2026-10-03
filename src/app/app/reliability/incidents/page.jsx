"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  ShieldAlert,
  AlertTriangle,
  RefreshCw,
  ExternalLink,
  Flame,
  CheckCircle2,
  Info,
} from "lucide-react";
import { securityService } from "@/services/security";

export default function ReliabilityIncidentsBridgePage() {
  const [incidents, setIncidents] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState("");

  const fetchData = useCallback(async () => {
    try {
      setIsLoading(true);
      setErrorMsg("");
      const res = await securityService.listIncidents({ limit: 50 });
      // Filter for reliability-linked incidents (e.g. tag or category related to outages, resource exhaustion, denial of service)
      const all = res?.items || [];
      setIncidents(all);
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
            <ShieldAlert className="w-6 h-6 text-indigo-400" />
            <h1 className="text-xl font-bold text-white tracking-tight">
              Reliability & Security Incidents
            </h1>
          </div>
          <p className="text-xs text-slate-400">
            Per system architecture, reliability does not create a parallel incident tracker. Security-implicated reliability failures correlate directly into Step 34 Security Operations.
          </p>
        </div>

        <button
          onClick={fetchData}
          disabled={isLoading}
          className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
          title="Refresh incidents"
        >
          <RefreshCw className={`w-4 h-4 ${isLoading ? "animate-spin" : ""}`} />
        </button>
      </div>

      <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-indigo-950/50 rounded-lg text-indigo-400">
            <Info className="w-5 h-5" />
          </div>
          <div className="text-xs">
            <div className="font-semibold text-white">Unified Incident Architecture</div>
            <div className="text-slate-400 mt-0.5">
              Normal transient retries and circuit trips are handled automatically. Only failures with adversarial, exfiltration, or quarantine implications trigger a formal incident.
            </div>
          </div>
        </div>

        <Link
          href="/app/security"
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-sm transition shrink-0"
        >
          Open Security Operations <ExternalLink className="w-3.5 h-3.5" />
        </Link>
      </div>

      {errorMsg && (
        <div className="p-4 rounded-xl bg-red-950/40 border border-red-800 text-red-200 text-sm">
          {errorMsg}
        </div>
      )}

      {/* Incidents Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-white flex items-center gap-2">
            <Flame className="w-4 h-4 text-amber-400" />
            Correlated Active Incidents ({incidents.length})
          </h3>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="bg-slate-950/60 text-xs uppercase text-slate-400 border-b border-slate-800">
              <tr>
                <th className="py-3 px-4 font-semibold">Incident Title</th>
                <th className="py-3 px-4 font-semibold">Severity</th>
                <th className="py-3 px-4 font-semibold">Status</th>
                <th className="py-3 px-4 font-semibold">Category</th>
                <th className="py-3 px-4 font-semibold">Logged At</th>
                <th className="py-3 px-4 font-semibold text-right">View</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono text-xs">
              {incidents.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-slate-500 font-sans">
                    No active security or reliability-implicated incidents.
                  </td>
                </tr>
              ) : (
                incidents.map((inc) => (
                  <tr key={inc.id} className="hover:bg-slate-800/40 transition">
                    <td className="py-3 px-4 font-sans font-semibold text-white">
                      {inc.title}
                    </td>
                    <td className="py-3 px-4 uppercase font-bold text-amber-400">
                      {inc.severity}
                    </td>
                    <td className="py-3 px-4 text-slate-300">
                      {inc.status}
                    </td>
                    <td className="py-3 px-4 text-slate-400">
                      {inc.category}
                    </td>
                    <td className="py-3 px-4 text-slate-500">
                      {new Date(inc.created_at).toLocaleTimeString()}
                    </td>
                    <td className="py-3 px-4 text-right font-sans">
                      <Link
                        href={`/app/security`}
                        className="text-xs text-indigo-400 hover:text-indigo-300 font-medium"
                      >
                        Inspect →
                      </Link>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
