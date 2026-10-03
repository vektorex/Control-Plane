"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import {
  Siren,
  ShieldAlert,
  AlertTriangle,
  Flame,
  Activity,
  CheckCircle2,
  RefreshCw,
  Plus,
  BookOpen,
  Lock,
  Layers,
  Search,
} from "lucide-react";
import { securityService } from "@/services/security";
import { SecurityStatsCards } from "@/components/features/security/SecurityStatsCards";
import { IncidentListTable } from "@/components/features/security/IncidentListTable";
import { SecuritySignalTable } from "@/components/features/security/SecuritySignalTable";
import { SecurityIndicatorTable } from "@/components/features/security/SecurityIndicatorTable";
import { PlaybookModal } from "@/components/features/security/PlaybookModal";

export default function SecurityOperationsPage() {
  const [activeTab, setActiveTab] = useState("incidents");
  const [overview, setOverview] = useState(null);
  const [statistics, setStatistics] = useState(null);
  const [incidents, setIncidents] = useState([]);
  const [signals, setSignals] = useState([]);
  const [indicators, setIndicators] = useState([]);
  const [playbooks, setPlaybooks] = useState([]);
  const [detectors, setDetectors] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState("");
  const [isPlaybookModalOpen, setIsPlaybookModalOpen] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      setIsLoading(true);
      setErrorMsg("");

      const [ovRes, statRes, incRes, sigRes, indRes, pbRes, detRes] = await Promise.allSettled([
        securityService.getOverview(),
        securityService.getStatistics({ days: 14 }),
        securityService.listIncidents({ limit: 50 }),
        securityService.listSignals({ limit: 50 }),
        securityService.listIndicators({ limit: 50 }),
        securityService.listPlaybooks({ limit: 50 }),
        securityService.listDetectors(),
      ]);

      if (ovRes.status === "fulfilled") setOverview(ovRes.value);
      if (statRes.status === "fulfilled") setStatistics(statRes.value);
      if (incRes.status === "fulfilled") setIncidents(incRes.value?.items || []);
      if (sigRes.status === "fulfilled") setSignals(sigRes.value?.items || []);
      if (indRes.status === "fulfilled") setIndicators(indRes.value?.items || []);
      if (pbRes.status === "fulfilled") setPlaybooks(pbRes.value?.items || []);
      if (detRes.status === "fulfilled") setDetectors(detRes.value?.detectors || []);
    } catch (err) {
      setErrorMsg(err.message || "Failed to load security operations data.");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Connect to SSE stream for real-time security events
  useEffect(() => {
    let evtSource;
    try {
      evtSource = new EventSource("/api/events/stream");
      evtSource.addEventListener("security.signal.created", () => fetchData());
      evtSource.addEventListener("security.incident.created", () => fetchData());
      evtSource.addEventListener("security.incident.updated", () => fetchData());
      evtSource.addEventListener("security.containment.requested", () => fetchData());
      evtSource.addEventListener("security.containment.completed", () => fetchData());
    } catch (e) {
      // SSE fallback to polling/refresh
    }

    return () => {
      if (evtSource) evtSource.close();
    };
  }, [fetchData]);

  return (
    <div className="space-y-6 pb-12">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-red-950/70 border border-red-800/60 text-red-400">
              <Siren className="w-6 h-6 animate-pulse" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
                Security Operations & Threat Detection
              </h1>
              <p className="text-xs text-slate-400">
                Centralized detection, correlation, containment, and immutable evidence across the AI Work Layer.
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={() => fetchData()}
            disabled={isLoading}
            className="p-2 rounded-lg bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-300 transition-colors disabled:opacity-50"
            title="Refresh Security State"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? "animate-spin text-indigo-400" : ""}`} />
          </button>

          <button
            onClick={() => setIsPlaybookModalOpen(true)}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-colors"
          >
            <BookOpen className="w-3.5 h-3.5 text-indigo-400" />
            New Playbook
          </button>
        </div>
      </div>

      {errorMsg && (
        <div className="p-3 bg-red-950/50 border border-red-800 rounded-lg text-xs text-red-300 flex items-center justify-between">
          <span>{errorMsg}</span>
          <button onClick={() => setErrorMsg("")} className="text-red-400 hover:text-white">✕</button>
        </div>
      )}

      {/* Metrics Banner */}
      <SecurityStatsCards overview={overview} statistics={statistics} />

      {/* Disclaimer Notice: Regulatory & Technical Monitoring */}
      <div className="p-3 bg-slate-950/80 border border-slate-800/80 rounded-lg text-[11px] text-slate-400 flex items-center justify-between">
        <span>
          <strong>Operational Security Principle:</strong> This system provides deterministic technical monitoring,
          threat detection, and incident response controls. Deterministic security policies remain authoritative;
          AI models cannot self-authorize containment or override security controls.
        </span>
        <span className="text-slate-500 font-mono text-[10px] shrink-0 ml-4">Step 34 Active</span>
      </div>

      {/* Navigation Tabs */}
      <div className="flex items-center border-b border-slate-800 space-x-1">
        <button
          onClick={() => setActiveTab("incidents")}
          className={`px-4 py-2.5 text-xs font-medium border-b-2 transition-colors flex items-center gap-1.5 ${
            activeTab === "incidents"
              ? "border-red-500 text-red-400 font-semibold"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <ShieldAlert className="w-3.5 h-3.5" />
          Incidents ({incidents.length})
        </button>

        <button
          onClick={() => setActiveTab("signals")}
          className={`px-4 py-2.5 text-xs font-medium border-b-2 transition-colors flex items-center gap-1.5 ${
            activeTab === "signals"
              ? "border-amber-500 text-amber-400 font-semibold"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <Flame className="w-3.5 h-3.5" />
          Security Signals ({signals.length})
        </button>

        <button
          onClick={() => setActiveTab("indicators")}
          className={`px-4 py-2.5 text-xs font-medium border-b-2 transition-colors flex items-center gap-1.5 ${
            activeTab === "indicators"
              ? "border-blue-500 text-blue-400 font-semibold"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <Activity className="w-3.5 h-3.5" />
          Threat Indicators ({indicators.length})
        </button>

        <button
          onClick={() => setActiveTab("playbooks")}
          className={`px-4 py-2.5 text-xs font-medium border-b-2 transition-colors flex items-center gap-1.5 ${
            activeTab === "playbooks"
              ? "border-emerald-500 text-emerald-400 font-semibold"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <BookOpen className="w-3.5 h-3.5" />
          Response Playbooks ({playbooks.length})
        </button>

        <button
          onClick={() => setActiveTab("detectors")}
          className={`px-4 py-2.5 text-xs font-medium border-b-2 transition-colors flex items-center gap-1.5 ${
            activeTab === "detectors"
              ? "border-purple-500 text-purple-400 font-semibold"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <Layers className="w-3.5 h-3.5" />
          Registered Detectors ({detectors.length})
        </button>
      </div>

      {/* Tab Panels */}
      <div>
        {activeTab === "incidents" && (
          <IncidentListTable incidents={incidents} onRefresh={fetchData} />
        )}

        {activeTab === "signals" && (
          <SecuritySignalTable signals={signals} onRefresh={fetchData} />
        )}

        {activeTab === "indicators" && (
          <SecurityIndicatorTable indicators={indicators} />
        )}

        {activeTab === "playbooks" && (
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <h3 className="text-sm font-semibold text-white">Automated Response Playbooks</h3>
                <p className="text-xs text-slate-500">
                  Allowlisted trigger conditions and mitigation actions. Zero arbitrary code or shell execution.
                </p>
              </div>
              <button
                onClick={() => setIsPlaybookModalOpen(true)}
                className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white flex items-center gap-1"
              >
                <Plus className="w-3.5 h-3.5" /> Create Playbook
              </button>
            </div>

            {playbooks.length === 0 ? (
              <p className="text-xs text-slate-500 py-8 text-center">
                No response playbooks configured. Create a playbook to automate containment.
              </p>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {playbooks.map((pb) => (
                  <div
                    key={pb.id}
                    className="bg-slate-950 p-4 rounded-lg border border-slate-800 space-y-2"
                  >
                    <div className="flex items-center justify-between">
                      <h4 className="text-sm font-semibold text-white">{pb.name}</h4>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800">
                        {pb.enabled ? "Active" : "Disabled"}
                      </span>
                    </div>
                    {pb.description && (
                      <p className="text-xs text-slate-400">{pb.description}</p>
                    )}
                    <div className="pt-2 text-xs space-y-1">
                      <div className="text-slate-500">
                        Triggers: <span className="font-mono text-slate-300">{JSON.stringify(pb.trigger_conditions)}</span>
                      </div>
                      <div className="text-slate-500">
                        Actions:{" "}
                        <span className="font-mono text-indigo-400">
                          {Array.isArray(pb.actions) ? pb.actions.join(", ") : pb.actions}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === "detectors" && (
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm space-y-4">
            <div>
              <h3 className="text-sm font-semibold text-white">Registered Deterministic Detectors</h3>
              <p className="text-xs text-slate-500">
                16 rule-based detectors enforcing Step 32 and Step 33 boundaries without LLM hallucinations.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {detectors.map((det) => (
                <div
                  key={det.name}
                  className="bg-slate-950 p-3 rounded-lg border border-slate-800 flex items-center justify-between"
                >
                  <div className="space-y-0.5">
                    <span className="text-xs font-mono font-semibold text-white">{det.name}</span>
                    <span className="text-[11px] text-slate-500 block">Deterministic Rule Engine</span>
                  </div>
                  <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-emerald-950/80 text-emerald-400 border border-emerald-800/60">
                    {det.status}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Playbook creation modal */}
      <PlaybookModal
        isOpen={isPlaybookModalOpen}
        onClose={() => setIsPlaybookModalOpen(false)}
        onSuccess={() => fetchData()}
      />
    </div>
  );
}
