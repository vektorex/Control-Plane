"use client";

import React, { useState, useEffect, useCallback, use } from "react";
import Link from "next/link";
import {
  ShieldAlert,
  ArrowLeft,
  Clock,
  User,
  Lock,
  RefreshCw,
  CheckCircle2,
  FileCheck2,
  Database,
  Workflow,
  AlertTriangle,
  Flame,
  Layers,
  Activity,
  Plus,
} from "lucide-react";
import { securityService } from "@/services/security";
import { IncidentTimelineViewer } from "@/components/features/security/IncidentTimelineViewer";
import { InvestigationGraphViewer } from "@/components/features/security/InvestigationGraphViewer";
import { ContainmentActionModal } from "@/components/features/security/ContainmentActionModal";

export default function IncidentDetailPage({ params }) {
  const unwrappedParams = use(params);
  const incidentId = unwrappedParams.incidentId;

  const [incident, setIncident] = useState(null);
  const [timeline, setTimeline] = useState([]);
  const [investigation, setInvestigation] = useState(null);
  const [evidence, setEvidence] = useState([]);
  const [containmentActions, setContainmentActions] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState("");
  const [activeTab, setActiveTab] = useState("investigation");
  const [isContainmentModalOpen, setIsContainmentModalOpen] = useState(false);
  const [isResolving, setIsResolving] = useState(false);
  const [resolutionSummary, setResolutionSummary] = useState("");

  const fetchData = useCallback(async () => {
    try {
      setIsLoading(true);
      setErrorMsg("");

      const [incRes, tlRes, invRes, evRes, caRes] = await Promise.allSettled([
        securityService.getIncident(incidentId),
        securityService.getIncidentTimeline(incidentId),
        securityService.getIncidentInvestigation(incidentId),
        securityService.getIncidentEvidence(incidentId),
        securityService.listContainmentActions(incidentId),
      ]);

      if (incRes.status === "fulfilled") setIncident(incRes.value);
      if (tlRes.status === "fulfilled") setTimeline(tlRes.value?.events || []);
      if (invRes.status === "fulfilled") setInvestigation(invRes.value);
      if (evRes.status === "fulfilled") setEvidence(evRes.value?.evidence || []);
      if (caRes.status === "fulfilled") setContainmentActions(caRes.value?.actions || []);
    } catch (err) {
      setErrorMsg(err.message || "Failed to load incident investigation details.");
    } finally {
      setIsLoading(false);
    }
  }, [incidentId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleResolveIncident = async () => {
    if (!resolutionSummary.trim()) {
      alert("Resolution summary documentation is required.");
      return;
    }

    try {
      setIsResolving(true);
      await securityService.updateIncident(incidentId, {
        status: "resolved",
        resolution_summary: resolutionSummary.trim(),
      });
      fetchData();
    } catch (err) {
      alert("Failed to resolve incident: " + (err.message || err));
    } finally {
      setIsResolving(false);
    }
  };

  const getSeverityBadge = (sev) => {
    switch (sev) {
      case "critical":
        return <span className="px-2.5 py-1 text-xs font-semibold rounded bg-red-950 text-red-400 border border-red-800">Critical Severity</span>;
      case "high":
        return <span className="px-2.5 py-1 text-xs font-semibold rounded bg-amber-950 text-amber-400 border border-amber-800">High Severity</span>;
      case "medium":
        return <span className="px-2.5 py-1 text-xs font-medium rounded bg-yellow-950/80 text-yellow-400 border border-yellow-800">Medium Severity</span>;
      default:
        return <span className="px-2.5 py-1 text-xs font-medium rounded bg-blue-950/80 text-blue-400 border border-blue-800">Low Severity</span>;
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case "open":
        return <span className="px-2 py-0.5 text-xs font-medium rounded bg-red-900/40 text-red-300 border border-red-800/60 uppercase">Open</span>;
      case "investigating":
        return <span className="px-2 py-0.5 text-xs font-medium rounded bg-amber-900/40 text-amber-300 border border-amber-800/60 uppercase">Investigating</span>;
      case "contained":
        return <span className="px-2 py-0.5 text-xs font-medium rounded bg-blue-900/40 text-blue-300 border border-blue-800/60 uppercase">Contained</span>;
      case "resolved":
        return <span className="px-2 py-0.5 text-xs font-medium rounded bg-emerald-900/40 text-emerald-300 border border-emerald-800/60 uppercase">Resolved</span>;
      default:
        return <span className="px-2 py-0.5 text-xs font-medium rounded bg-slate-800 text-slate-300 uppercase">{status}</span>;
    }
  };

  if (isLoading && !incident) {
    return (
      <div className="py-24 text-center space-y-3">
        <RefreshCw className="w-6 h-6 animate-spin mx-auto text-indigo-400" />
        <p className="text-xs text-slate-400">Loading incident investigation graph...</p>
      </div>
    );
  }

  if (!incident) {
    return (
      <div className="py-16 text-center space-y-4">
        <AlertTriangle className="w-8 h-8 text-amber-400 mx-auto" />
        <h3 className="text-base font-semibold text-white">Incident Not Found</h3>
        <p className="text-xs text-slate-400">The requested incident does not exist or has been removed.</p>
        <Link
          href="/app/security"
          className="inline-flex items-center gap-1.5 px-4 py-2 text-xs rounded-lg bg-slate-800 text-slate-300 hover:text-white"
        >
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Security Operations
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6 pb-16">
      {/* Back button & top actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div className="flex items-center gap-3">
          <Link
            href="/app/security"
            className="p-2 rounded-lg bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono text-slate-500 uppercase">
                Incident #{incident.id.substring(0, 8)}
              </span>
              {getStatusBadge(incident.status)}
              {getSeverityBadge(incident.severity)}
            </div>
            <h1 className="text-xl font-bold tracking-tight text-white mt-1">
              {incident.title}
            </h1>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => fetchData()}
            disabled={isLoading}
            className="p-2 rounded-lg bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-300 transition-colors"
            title="Refresh"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? "animate-spin text-indigo-400" : ""}`} />
          </button>

          {incident.status !== "resolved" && incident.status !== "dismissed" && (
            <button
              onClick={() => setIsContainmentModalOpen(true)}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-orange-600 hover:bg-orange-500 text-white transition-colors"
            >
              <Lock className="w-3.5 h-3.5" />
              Contain Incident
            </button>
          )}
        </div>
      </div>

      {errorMsg && (
        <div className="p-3 bg-red-950/50 border border-red-800 rounded-lg text-xs text-red-300">
          {errorMsg}
        </div>
      )}

      {/* Incident Metadata Summary Strip */}
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-3 bg-slate-900 border border-slate-800 rounded-xl p-4 text-xs">
        <div>
          <span className="text-slate-500 block">Category</span>
          <strong className="text-white font-mono">{incident.category}</strong>
        </div>
        <div>
          <span className="text-slate-500 block">First Detected</span>
          <span className="text-slate-300 font-mono">
            {new Date(incident.first_seen_at).toLocaleTimeString()}
          </span>
        </div>
        <div>
          <span className="text-slate-500 block">Last Seen</span>
          <span className="text-slate-300 font-mono">
            {new Date(incident.last_seen_at).toLocaleTimeString()}
          </span>
        </div>
        <div>
          <span className="text-slate-500 block">Assigned Responder</span>
          <div className="flex items-center gap-1 text-slate-300">
            <User className="w-3.5 h-3.5 text-slate-500" />
            <span>{incident.assigned_to || "Unassigned"}</span>
          </div>
        </div>
        <div>
          <span className="text-slate-500 block">Correlated Signals</span>
          <strong className="text-amber-400 font-bold">
            {investigation?.signals?.length || 0}
          </strong>
        </div>
        <div>
          <span className="text-slate-500 block">Containments</span>
          <strong className="text-orange-400 font-bold">
            {containmentActions.length}
          </strong>
        </div>
      </div>

      {/* Navigation sub-tabs */}
      <div className="flex items-center border-b border-slate-800 space-x-1">
        <button
          onClick={() => setActiveTab("investigation")}
          className={`px-4 py-2.5 text-xs font-medium border-b-2 transition-colors flex items-center gap-1.5 ${
            activeTab === "investigation"
              ? "border-indigo-500 text-indigo-400 font-semibold"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <Activity className="w-3.5 h-3.5" />
          Investigation Topology
        </button>

        <button
          onClick={() => setActiveTab("timeline")}
          className={`px-4 py-2.5 text-xs font-medium border-b-2 transition-colors flex items-center gap-1.5 ${
            activeTab === "timeline"
              ? "border-indigo-500 text-indigo-400 font-semibold"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <Clock className="w-3.5 h-3.5" />
          Audit Timeline ({timeline.length})
        </button>

        <button
          onClick={() => setActiveTab("evidence")}
          className={`px-4 py-2.5 text-xs font-medium border-b-2 transition-colors flex items-center gap-1.5 ${
            activeTab === "evidence"
              ? "border-indigo-500 text-indigo-400 font-semibold"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <FileCheck2 className="w-3.5 h-3.5" />
          Compliance Evidence ({evidence.length})
        </button>

        <button
          onClick={() => setActiveTab("resolution")}
          className={`px-4 py-2.5 text-xs font-medium border-b-2 transition-colors flex items-center gap-1.5 ${
            activeTab === "resolution"
              ? "border-indigo-500 text-indigo-400 font-semibold"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <CheckCircle2 className="w-3.5 h-3.5" />
          Resolution & Closure
        </button>
      </div>

      {/* Tab Panels */}
      <div>
        {activeTab === "investigation" && (
          <InvestigationGraphViewer investigation={investigation} />
        )}

        {activeTab === "timeline" && (
          <IncidentTimelineViewer events={timeline} />
        )}

        {activeTab === "evidence" && (
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm space-y-4">
            <div>
              <h3 className="text-sm font-semibold text-white">Immutable Compliance Evidence Records</h3>
              <p className="text-xs text-slate-500">
                Cryptographically hashed audit evidence chaining this incident into the Step 33 compliance ledger.
              </p>
            </div>

            {evidence.length === 0 ? (
              <p className="text-xs text-slate-500 py-6 text-center">
                No compliance evidence entries linked to this incident.
              </p>
            ) : (
              <div className="space-y-3">
                {evidence.map((ev) => (
                  <div
                    key={ev.id}
                    className="bg-slate-950 p-3.5 rounded-lg border border-slate-800 text-xs space-y-2"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-white">{ev.title}</span>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800">
                        {ev.evidence_type}
                      </span>
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-slate-400 font-mono text-[11px]">
                      <div>Payload Hash: {ev.payload_hash || "sha256"}</div>
                      <div>Actor: {ev.collected_by || "security_service"}</div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === "resolution" && (
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm space-y-4 max-w-2xl">
            <h3 className="text-sm font-semibold text-white">Incident Resolution & Closure</h3>
            <p className="text-xs text-slate-500">
              Provide factual closure notes documenting containment verification, recovery steps, and policy adjustments.
            </p>

            {incident.status === "resolved" ? (
              <div className="bg-emerald-950/40 border border-emerald-800/50 rounded-lg p-4 space-y-2 text-xs">
                <div className="flex items-center gap-2 text-emerald-400 font-semibold">
                  <CheckCircle2 className="w-4 h-4" /> Incident Resolved
                </div>
                <div className="text-slate-300">
                  Resolved by <strong className="text-white">{incident.resolved_by || "authorized_admin"}</strong> on{" "}
                  {incident.resolved_at ? new Date(incident.resolved_at).toLocaleString() : "-"}
                </div>
                {incident.resolution_summary && (
                  <p className="text-slate-400 bg-slate-950 p-2.5 rounded border border-slate-800 mt-2">
                    {incident.resolution_summary}
                  </p>
                )}
              </div>
            ) : (
              <div className="space-y-3 text-xs">
                <div>
                  <label className="block text-slate-300 font-medium mb-1">
                    Mandatory Resolution Summary:
                  </label>
                  <textarea
                    rows={4}
                    value={resolutionSummary}
                    onChange={(e) => setResolutionSummary(e.target.value)}
                    placeholder="Document root cause findings, containment confirmation, and recovery actions..."
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2.5 text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  />
                </div>

                <div className="flex justify-end">
                  <button
                    onClick={handleResolveIncident}
                    disabled={isResolving || !resolutionSummary.trim()}
                    className="px-4 py-2 font-semibold rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white disabled:opacity-50 flex items-center gap-1.5"
                  >
                    <CheckCircle2 className="w-4 h-4" />
                    {isResolving ? "Resolving..." : "Confirm Incident Resolution"}
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Containment modal */}
      <ContainmentActionModal
        incidentId={incident.id}
        isOpen={isContainmentModalOpen}
        onClose={() => setIsContainmentModalOpen(false)}
        onSuccess={() => fetchData()}
      />
    </div>
  );
}
