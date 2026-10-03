"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import {
  FileCheck2,
  Database,
  GitFork,
  Clock,
  Trash2,
  Lock,
  Download,
  ShieldCheck,
  RefreshCw,
  Plus,
  AlertTriangle,
  FileSpreadsheet,
  CheckCircle2,
  XCircle,
  Eye,
} from "lucide-react";
import { useWorkspace } from "@/lib/workspaceContext";
import { dataGovernanceService } from "@/services/dataGovernance";
import { DataGovernanceStatsCards } from "@/components/features/dataGovernance/DataGovernanceStatsCards";
import { AssetListTable } from "@/components/features/dataGovernance/AssetListTable";
import { LineageGraphViewer } from "@/components/features/dataGovernance/LineageGraphViewer";
import { EvidenceExplorerTable } from "@/components/features/dataGovernance/EvidenceExplorerTable";
import { LegalHoldModal } from "@/components/features/dataGovernance/LegalHoldModal";
import { DeletionRequestModal } from "@/components/features/dataGovernance/DeletionRequestModal";
import { ClassificationReviewModal } from "@/components/features/dataGovernance/ClassificationReviewModal";

export default function DataGovernanceDashboardPage() {
  const { currentWorkspace } = useWorkspace();
  const workspaceId = currentWorkspace?.id;

  const [activeTab, setActiveTab] = useState("inventory");
  const [overview, setOverview] = useState(null);
  const [assets, setAssets] = useState([]);
  const [evidence, setEvidence] = useState([]);
  const [retentionPolicies, setRetentionPolicies] = useState([]);
  const [legalHolds, setLegalHolds] = useState([]);
  const [deletions, setDeletions] = useState([]);
  const [privacyRequests, setPrivacyRequests] = useState([]);
  const [exportsList, setExportsList] = useState([]);
  const [reports, setReports] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Modals state
  const [legalHoldModalOpen, setLegalHoldModalOpen] = useState(false);
  const [deletionModalOpen, setDeletionModalOpen] = useState(false);
  const [reviewModalOpen, setReviewModalOpen] = useState(false);
  const [selectedAsset, setSelectedAsset] = useState(null);

  const loadData = useCallback(async () => {
    if (!workspaceId) return;
    setLoading(true);
    setError(null);
    try {
      const [
        overviewRes,
        assetsRes,
        evidenceRes,
        retentionRes,
        holdsRes,
        deletionsRes,
        privacyRes,
        exportsRes,
        retentionRepRes,
      ] = await Promise.allSettled([
        dataGovernanceService.getOverview({ workspaceId }),
        dataGovernanceService.listAssets({ workspaceId, limit: 100 }),
        dataGovernanceService.listEvidence({ workspaceId, limit: 100 }),
        dataGovernanceService.listRetentionPolicies({ workspaceId }),
        dataGovernanceService.listLegalHolds({ workspaceId }),
        dataGovernanceService.listDeletions({ workspaceId }),
        dataGovernanceService.listPrivacyRequests({ workspaceId }),
        dataGovernanceService.listExports({ workspaceId }),
        dataGovernanceService.getRetentionReport(),
      ]);

      if (overviewRes.status === "fulfilled") setOverview(overviewRes.value);
      if (assetsRes.status === "fulfilled") setAssets(assetsRes.value || []);
      if (evidenceRes.status === "fulfilled") setEvidence(evidenceRes.value || []);
      if (retentionRes.status === "fulfilled") setRetentionPolicies(retentionRes.value || []);
      if (holdsRes.status === "fulfilled") setLegalHolds(holdsRes.value || []);
      if (deletionsRes.status === "fulfilled") setDeletions(deletionsRes.value || []);
      if (privacyRes.status === "fulfilled") setPrivacyRequests(privacyRes.value || []);
      if (exportsRes.status === "fulfilled") setExportsList(exportsRes.value || []);
      if (retentionRepRes.status === "fulfilled") {
        setReports((prev) => ({ ...prev, retention: retentionRepRes.value }));
      }
    } catch (err) {
      setError(err?.message || "Failed to load data governance telemetry.");
    } finally {
      setLoading(false);
    }
  }, [workspaceId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Handlers
  const handleCreateLegalHold = async (data) => {
    await dataGovernanceService.createLegalHold({
      ...data,
      workspace_id: workspaceId,
    });
    await loadData();
  };

  const handleCreateDeletion = async (data) => {
    await dataGovernanceService.createDeletion({
      ...data,
      workspace_id: workspaceId,
    });
    await loadData();
  };

  const handleReviewClassification = (asset) => {
    setSelectedAsset(asset);
    setReviewModalOpen(true);
  };

  const handleSubmitClassificationReview = async (data) => {
    await dataGovernanceService.reviewClassification(data);
    await loadData();
  };

  const handleReleaseHold = async (holdId) => {
    const reason = prompt("Enter the reason for releasing this legal hold:");
    if (!reason) return;
    try {
      await dataGovernanceService.releaseLegalHold(holdId, { reason });
      await loadData();
    } catch (err) {
      alert("Failed to release legal hold: " + err.message);
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto px-4 sm:px-6 py-6">
      {/* Disclaimer Banner */}
      <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 text-xs text-slate-400 flex items-start gap-2.5 shadow-sm">
        <AlertTriangle className="w-4 h-4 text-indigo-400 shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold text-slate-200">
            Technical Privacy & Compliance Control Plane:
          </span>{" "}
          This system provides deterministic data classification, SHA-256 evidence chain verification, safe deletion workflows, and protective legal holds. It is a technical enforcement layer and does not constitute a certified legal or regulatory compliance guarantee.
        </div>
      </div>

      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2.5">
            <FileCheck2 className="w-6 h-6 text-indigo-400" />
            Data Governance & Compliance Evidence
          </h1>
          <p className="mt-1 text-sm text-slate-400">
            Cryptographic provenance, deterministic privacy detection, retention lifecycle, and immutable audit evidence.
          </p>
        </div>

        <div className="flex items-center gap-2.5 flex-wrap">
          <button
            onClick={loadData}
            disabled={loading}
            className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition-colors disabled:opacity-50"
            title="Refresh Data"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          </button>
          <button
            onClick={() => setLegalHoldModalOpen(true)}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-amber-500/10 hover:bg-amber-500/20 text-amber-300 border border-amber-500/30 text-xs font-medium transition-colors"
          >
            <Lock className="w-3.5 h-3.5" />
            New Legal Hold
          </button>
          <button
            onClick={() => setDeletionModalOpen(true)}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-300 border border-rose-500/30 text-xs font-medium transition-colors"
          >
            <Trash2 className="w-3.5 h-3.5" />
            Request Deletion
          </button>
        </div>
      </div>

      {/* Metrics Cards */}
      <DataGovernanceStatsCards overview={overview} loading={loading} />

      {/* Navigation Tabs */}
      <div className="border-b border-slate-800">
        <nav className="flex space-x-6 overflow-x-auto">
          {[
            { id: "inventory", label: "Data Inventory", icon: Database, count: assets.length },
            { id: "lineage", label: "Lineage Graph", icon: GitFork },
            { id: "evidence", label: "Compliance Evidence", icon: FileCheck2, count: evidence.length },
            { id: "legal_holds", label: "Legal Holds", icon: Lock, count: legalHolds.filter((h) => h.status === "active").length },
            { id: "deletions", label: "Deletions", icon: Trash2, count: deletions.length },
            { id: "retention", label: "Retention Policies", icon: Clock, count: retentionPolicies.length },
            { id: "privacy", label: "Privacy Requests", icon: ShieldCheck, count: privacyRequests.length },
            { id: "exports", label: "Data Exports", icon: Download, count: exportsList.length },
          ].map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-3 px-1 border-b-2 font-medium text-xs sm:text-sm flex items-center gap-2 whitespace-nowrap transition-colors ${
                  isActive
                    ? "border-indigo-500 text-indigo-400 font-semibold"
                    : "border-transparent text-slate-400 hover:text-slate-200 hover:border-slate-700"
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{tab.label}</span>
                {tab.count !== undefined && (
                  <span
                    className={`ml-1 px-1.5 py-0.2 rounded-full text-[10px] ${
                      isActive ? "bg-indigo-500/20 text-indigo-300" : "bg-slate-800 text-slate-400"
                    }`}
                  >
                    {tab.count}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Tab Contents */}
      {activeTab === "inventory" && (
        <AssetListTable
          assets={assets}
          loading={loading}
          onReviewClassification={handleReviewClassification}
          onRefresh={loadData}
        />
      )}

      {activeTab === "lineage" && (
        <div>
          {assets.length > 0 ? (
            <LineageGraphViewer
              rootAssetId={assets[0]?.id}
              lineageData={{
                nodes: assets.slice(0, 12),
                edges: [],
              }}
              loading={loading}
            />
          ) : (
            <div className="p-8 text-center text-slate-400 bg-slate-900/60 rounded-xl border border-slate-800 text-sm">
              No assets available to trace lineage. Register or ingest data assets first.
            </div>
          )}
        </div>
      )}

      {activeTab === "evidence" && (
        <EvidenceExplorerTable evidence={evidence} loading={loading} onRefresh={loadData} />
      )}

      {activeTab === "legal_holds" && (
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 backdrop-blur-sm overflow-hidden">
          <div className="p-4 border-b border-slate-800 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white">Active and Released Legal Holds</h3>
            <span className="text-xs text-slate-500">
              Preserves data integrity during litigation or regulatory inquiry
            </span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="bg-slate-950/60 text-xs font-semibold uppercase text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4">Hold Name</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Reason</th>
                  <th className="py-3 px-4">Created At</th>
                  <th className="py-3 px-4">Protected Assets</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-xs">
                {legalHolds.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="py-8 text-center text-slate-400">
                      No active legal holds.
                    </td>
                  </tr>
                ) : (
                  legalHolds.map((h) => (
                    <tr key={h.id} className="hover:bg-slate-800/40">
                      <td className="py-3 px-4 font-medium text-slate-200">{h.name}</td>
                      <td className="py-3 px-4">
                        <span
                          className={`px-2 py-0.5 rounded font-semibold ${
                            h.status === "active"
                              ? "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                              : "bg-slate-800 text-slate-400"
                          }`}
                        >
                          {h.status}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-slate-400 truncate max-w-xs">{h.reason}</td>
                      <td className="py-3 px-4 text-slate-400 font-mono">
                        {h.created_at ? new Date(h.created_at).toISOString().slice(0, 10) : "-"}
                      </td>
                      <td className="py-3 px-4 font-mono text-slate-300">{h.asset_count || 0}</td>
                      <td className="py-3 px-4 text-right">
                        {h.status === "active" && (
                          <button
                            onClick={() => handleReleaseHold(h.id)}
                            className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-amber-300 transition-colors"
                          >
                            Release Hold
                          </button>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === "deletions" && (
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 backdrop-blur-sm overflow-hidden">
          <div className="p-4 border-b border-slate-800 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white">Safe Deletion Log & Verifications</h3>
            <span className="text-xs text-slate-500">
              Zero blind cascading; verifiable and blocked if under legal hold
            </span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="bg-slate-950/60 text-xs font-semibold uppercase text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4">Target Scope</th>
                  <th className="py-3 px-4">Identifier</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Verification</th>
                  <th className="py-3 px-4">Requested At</th>
                  <th className="py-3 px-4">Error / Block Reason</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-xs font-mono">
                {deletions.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="py-8 text-center text-slate-400 font-sans">
                      No deletion requests recorded.
                    </td>
                  </tr>
                ) : (
                  deletions.map((d) => (
                    <tr key={d.id} className="hover:bg-slate-800/40">
                      <td className="py-3 px-4 text-slate-300">{d.scope_type}</td>
                      <td className="py-3 px-4 text-slate-400 truncate max-w-[120px]">{d.scope_id}</td>
                      <td className="py-3 px-4 font-sans">
                        <span
                          className={`px-2 py-0.5 rounded font-semibold ${
                            d.status === "completed"
                              ? "bg-emerald-500/10 text-emerald-400"
                              : d.status === "blocked"
                              ? "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                              : "bg-slate-800 text-slate-300"
                          }`}
                        >
                          {d.status}
                        </span>
                      </td>
                      <td className="py-3 px-4 font-sans text-slate-300">
                        {d.verification_status || "pending"}
                      </td>
                      <td className="py-3 px-4 text-slate-400">
                        {d.requested_at ? new Date(d.requested_at).toISOString().slice(0, 16) : "-"}
                      </td>
                      <td className="py-3 px-4 text-rose-400 truncate max-w-xs font-sans">
                        {d.error || "-"}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === "retention" && (
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 backdrop-blur-sm overflow-hidden">
          <div className="p-4 border-b border-slate-800 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white">Configured Retention Policies</h3>
            <span className="text-xs text-slate-500">
              Resolved hierarchically: System → Org → Workspace → Resource
            </span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="bg-slate-950/60 text-xs font-semibold uppercase text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4">Policy Name</th>
                  <th className="py-3 px-4">Resource Type</th>
                  <th className="py-3 px-4">Lifecycle Action</th>
                  <th className="py-3 px-4">Retention Window</th>
                  <th className="py-3 px-4">Grace Period</th>
                  <th className="py-3 px-4">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-xs">
                {retentionPolicies.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="py-8 text-center text-slate-400">
                      No custom retention policies defined. Default system retention applies.
                    </td>
                  </tr>
                ) : (
                  retentionPolicies.map((p) => (
                    <tr key={p.id} className="hover:bg-slate-800/40">
                      <td className="py-3 px-4 font-medium text-slate-200">{p.name}</td>
                      <td className="py-3 px-4 font-mono text-slate-400">{p.resource_type}</td>
                      <td className="py-3 px-4">
                        <span className="px-2 py-0.5 rounded bg-slate-800 text-indigo-300 font-mono uppercase text-[10px]">
                          {p.action}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-slate-300">
                        {p.retention_days ? `${p.retention_days} days` : "Indefinite"}
                      </td>
                      <td className="py-3 px-4 text-slate-400">{p.grace_period_days} days</td>
                      <td className="py-3 px-4">
                        <span
                          className={`px-2 py-0.5 rounded ${
                            p.enabled ? "bg-emerald-500/10 text-emerald-400" : "bg-slate-800 text-slate-500"
                          }`}
                        >
                          {p.enabled ? "Active" : "Disabled"}
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === "privacy" && (
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 backdrop-blur-sm overflow-hidden">
          <div className="p-4 border-b border-slate-800 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white">Privacy Requests</h3>
            <span className="text-xs text-slate-500">
              Platform data rights workflows (Access, Export, Deletion, Restriction)
            </span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="bg-slate-950/60 text-xs font-semibold uppercase text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4">Request ID</th>
                  <th className="py-3 px-4">Type</th>
                  <th className="py-3 px-4">Scope</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Verification</th>
                  <th className="py-3 px-4">Requested At</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-xs font-mono">
                {privacyRequests.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="py-8 text-center text-slate-400 font-sans">
                      No active privacy requests.
                    </td>
                  </tr>
                ) : (
                  privacyRequests.map((pr) => (
                    <tr key={pr.id} className="hover:bg-slate-800/40">
                      <td className="py-3 px-4 text-slate-400">{pr.id.slice(0, 8)}...</td>
                      <td className="py-3 px-4 font-sans font-medium text-slate-200 uppercase text-[11px]">
                        {pr.request_type}
                      </td>
                      <td className="py-3 px-4 text-slate-300">{pr.scope}</td>
                      <td className="py-3 px-4 font-sans">
                        <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                          {pr.status}
                        </span>
                      </td>
                      <td className="py-3 px-4 font-sans text-emerald-400">
                        {pr.verification_status}
                      </td>
                      <td className="py-3 px-4 text-slate-400">
                        {pr.created_at ? new Date(pr.created_at).toISOString().slice(0, 16) : "-"}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === "exports" && (
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 backdrop-blur-sm overflow-hidden">
          <div className="p-4 border-b border-slate-800 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white">Sanitized Data Exports</h3>
            <span className="text-xs text-slate-500">
              Secrets and private credentials are automatically stripped prior to generation
            </span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="bg-slate-950/60 text-xs font-semibold uppercase text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4">Export ID</th>
                  <th className="py-3 px-4">Format</th>
                  <th className="py-3 px-4">Scope</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Expires At</th>
                  <th className="py-3 px-4">Sanitized Manifest</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-xs font-mono">
                {exportsList.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="py-8 text-center text-slate-400 font-sans">
                      No exports generated yet.
                    </td>
                  </tr>
                ) : (
                  exportsList.map((exp) => (
                    <tr key={exp.id} className="hover:bg-slate-800/40">
                      <td className="py-3 px-4 text-slate-400">{exp.id.slice(0, 8)}...</td>
                      <td className="py-3 px-4 uppercase text-indigo-300">{exp.format}</td>
                      <td className="py-3 px-4 text-slate-300 font-sans">{exp.scope_type}</td>
                      <td className="py-3 px-4 font-sans">
                        <span
                          className={`px-2 py-0.5 rounded font-semibold ${
                            exp.status === "completed"
                              ? "bg-emerald-500/10 text-emerald-400"
                              : "bg-slate-800 text-slate-400"
                          }`}
                        >
                          {exp.status}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-slate-400">
                        {exp.expires_at ? new Date(exp.expires_at).toISOString().slice(0, 10) : "-"}
                      </td>
                      <td className="py-3 px-4 font-sans text-emerald-400">
                        {exp.manifest?.sanitized ? "Secrets Redacted" : "Standard"}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Modals */}
      <LegalHoldModal
        isOpen={legalHoldModalOpen}
        onClose={() => setLegalHoldModalOpen(false)}
        onSubmit={handleCreateLegalHold}
        assets={assets}
      />

      <DeletionRequestModal
        isOpen={deletionModalOpen}
        onClose={() => setDeletionModalOpen(false)}
        onSubmit={handleCreateDeletion}
        assets={assets}
      />

      <ClassificationReviewModal
        isOpen={reviewModalOpen}
        onClose={() => {
          setReviewModalOpen(false);
          setSelectedAsset(null);
        }}
        onSubmit={handleSubmitClassificationReview}
        asset={selectedAsset}
      />
    </div>
  );
}
