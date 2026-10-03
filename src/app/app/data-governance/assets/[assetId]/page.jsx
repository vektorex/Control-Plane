"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  Database,
  ArrowLeft,
  Shield,
  KeyRound,
  Lock,
  GitFork,
  Clock,
  User,
  History,
  AlertTriangle,
  FileCheck2,
  Trash2,
  CheckCircle,
} from "lucide-react";
import { dataGovernanceService } from "@/services/dataGovernance";
import { getClassificationBadge } from "@/components/features/dataGovernance/AssetListTable";
import { LineageGraphViewer } from "@/components/features/dataGovernance/LineageGraphViewer";
import { ClassificationReviewModal } from "@/components/features/dataGovernance/ClassificationReviewModal";

export default function AssetDetailPage() {
  const params = useParams();
  const assetId = params?.assetId;

  const [asset, setAsset] = useState(null);
  const [lineage, setLineage] = useState(null);
  const [accessHistory, setAccessHistory] = useState([]);
  const [evidenceList, setEvidenceList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [reviewModalOpen, setReviewModalOpen] = useState(false);

  useEffect(() => {
    if (!assetId) return;

    async function loadAssetData() {
      setLoading(true);
      setError(null);
      try {
        const [assetRes, lineageRes, accessRes, evidenceRes] = await Promise.allSettled([
          dataGovernanceService.getAsset(assetId),
          dataGovernanceService.getAssetLineage(assetId, { depth: 3 }),
          dataGovernanceService.getAssetAccessHistory(assetId, { limit: 25 }),
          dataGovernanceService.listEvidence({ subjectId: assetId, limit: 25 }),
        ]);

        if (assetRes.status === "fulfilled") setAsset(assetRes.value);
        else throw new Error("Asset not found or access denied.");

        if (lineageRes.status === "fulfilled") setLineage(lineageRes.value);
        if (accessRes.status === "fulfilled") setAccessHistory(accessRes.value || []);
        if (evidenceRes.status === "fulfilled") setEvidenceList(evidenceRes.value || []);
      } catch (err) {
        setError(err.message || "Failed to load asset details.");
      } finally {
        setLoading(false);
      }
    }

    loadAssetData();
  }, [assetId]);

  const handleClassificationSubmit = async (data) => {
    const updated = await dataGovernanceService.reviewClassification(data);
    setAsset(updated);
  };

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-8 space-y-4">
        <div className="h-8 w-48 bg-slate-800 rounded animate-pulse" />
        <div className="h-64 bg-slate-900 border border-slate-800 rounded-xl animate-pulse" />
      </div>
    );
  }

  if (error || !asset) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-12 text-center">
        <AlertTriangle className="w-10 h-10 text-rose-400 mx-auto mb-3" />
        <h2 className="text-lg font-bold text-white">Asset Not Found</h2>
        <p className="text-sm text-slate-400 mt-1">{error || "Unable to inspect specified asset."}</p>
        <Link
          href="/app/data-governance"
          className="inline-flex items-center gap-2 mt-4 px-4 py-2 rounded-lg bg-slate-800 text-slate-200 text-xs font-medium hover:bg-slate-700"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Data Inventory
        </Link>
      </div>
    );
  }

  const findings = asset.findings || [];

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 py-6 space-y-6">
      {/* Back button */}
      <div>
        <Link
          href="/app/data-governance"
          className="inline-flex items-center gap-2 text-xs font-medium text-slate-400 hover:text-white transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Data Inventory
        </Link>
      </div>

      {/* Asset Header Card */}
      <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 backdrop-blur-sm shadow-sm">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              <Database className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <h1 className="text-xl font-bold text-white">{asset.name}</h1>
                {getClassificationBadge(asset.data_classification)}
                <span className="px-2 py-0.5 rounded text-xs bg-slate-800 text-slate-400 font-mono">
                  {asset.asset_type}
                </span>
              </div>
              <p className="text-xs text-slate-400 font-mono mt-1">
                Resource ID: {asset.resource_id} • Type: {asset.resource_type}
              </p>
            </div>
          </div>

          <button
            onClick={() => setReviewModalOpen(true)}
            className="px-3 py-1.5 rounded-lg bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 text-xs font-medium transition-colors"
          >
            Review Classification
          </button>
        </div>

        {/* Core Metadata Grid */}
        <div className="mt-6 grid grid-cols-2 sm:grid-cols-4 gap-4 border-t border-slate-800/80 pt-4 text-xs">
          <div>
            <span className="text-slate-500 block">Logical Storage</span>
            <span className="text-slate-200 font-mono truncate block mt-0.5" title={asset.storage_location}>
              {asset.storage_location}
            </span>
          </div>
          <div>
            <span className="text-slate-500 block">Status</span>
            <span
              className={`inline-block mt-0.5 px-2 py-0.2 rounded font-medium ${
                asset.status === "active"
                  ? "bg-emerald-500/10 text-emerald-400"
                  : "bg-rose-500/10 text-rose-400"
              }`}
            >
              {asset.status}
            </span>
          </div>
          <div>
            <span className="text-slate-500 block">Owner</span>
            <span className="text-slate-300 font-mono truncate block mt-0.5">
              {asset.owner_type}:{asset.owner_id ? asset.owner_id.slice(0, 8) : "system"}
            </span>
          </div>
          <div>
            <span className="text-slate-500 block">Created At (UTC)</span>
            <span className="text-slate-300 font-mono block mt-0.5">
              {asset.created_at ? new Date(asset.created_at).toISOString().slice(0, 19).replace("T", " ") : "-"}
            </span>
          </div>
        </div>
      </div>

      {/* Sensitive Findings Card */}
      <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <KeyRound className="w-4 h-4 text-rose-400" />
            <h3 className="text-sm font-semibold text-white">Sensitive Findings & Privacy Detections</h3>
          </div>
          <span className="text-xs text-slate-500">
            {findings.length} detection{findings.length !== 1 ? "s" : ""}
          </span>
        </div>

        {findings.length === 0 ? (
          <div className="p-4 rounded-xl bg-slate-950/40 border border-slate-800/60 text-xs text-slate-400 flex items-center gap-2">
            <CheckCircle className="w-4 h-4 text-emerald-400" />
            <span>No PII or secrets detected in this data asset.</span>
          </div>
        ) : (
          <div className="space-y-2">
            {findings.map((f) => (
              <div
                key={f.id}
                className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 text-xs"
              >
                <div className="flex items-center gap-2.5">
                  <span className="px-2 py-0.5 rounded font-mono font-medium bg-rose-500/10 text-rose-400 border border-rose-500/20 uppercase text-[10px]">
                    {f.finding_type}
                  </span>
                  <span className="text-slate-300 font-mono">
                    Masked: <span className="text-amber-300">{f.preview_masked || "[REDACTED]"}</span>
                  </span>
                </div>
                <div className="flex items-center gap-4 text-slate-400">
                  <span className="font-mono text-[11px] text-slate-500">
                    Location: {f.location}
                  </span>
                  <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 text-[10px]">
                    Strategy: {f.redaction_strategy}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Provenance Lineage */}
      <LineageGraphViewer
        rootAssetId={asset.id}
        lineageData={lineage}
        loading={false}
      />

      {/* Access History & Audit Trail */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Access History */}
        <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800">
          <div className="flex items-center gap-2 mb-3">
            <History className="w-4 h-4 text-indigo-400" />
            <h3 className="text-sm font-semibold text-white">Data Access History</h3>
          </div>
          <div className="overflow-hidden">
            {accessHistory.length === 0 ? (
              <div className="text-xs text-slate-500 py-6 text-center">
                No recent access events recorded for this asset.
              </div>
            ) : (
              <div className="divide-y divide-slate-800/60 font-mono text-xs">
                {accessHistory.map((rec) => (
                  <div key={rec.id} className="py-2.5 flex items-center justify-between">
                    <div>
                      <span className="font-medium text-slate-200">{rec.action}</span>
                      <span className="text-slate-500 ml-2">by {rec.actor_type}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span
                        className={`px-1.5 py-0.2 rounded text-[10px] ${
                          rec.result === "allowed"
                            ? "text-emerald-400 bg-emerald-500/10"
                            : "text-rose-400 bg-rose-500/10"
                        }`}
                      >
                        {rec.result}
                      </span>
                      <span className="text-slate-500 text-[11px]">
                        {rec.timestamp ? new Date(rec.timestamp).toISOString().slice(11, 19) : "-"}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Compliance Evidence */}
        <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800">
          <div className="flex items-center gap-2 mb-3">
            <FileCheck2 className="w-4 h-4 text-emerald-400" />
            <h3 className="text-sm font-semibold text-white">Immutable Evidence Snapshots</h3>
          </div>
          <div className="overflow-hidden">
            {evidenceList.length === 0 ? (
              <div className="text-xs text-slate-500 py-6 text-center">
                No compliance evidence snapshots bound to this asset.
              </div>
            ) : (
              <div className="divide-y divide-slate-800/60 font-mono text-xs">
                {evidenceList.map((ev) => (
                  <div key={ev.id} className="py-2.5 flex items-center justify-between">
                    <div>
                      <span className="text-slate-300 font-sans">{ev.action}</span>
                      <span className="text-slate-500 ml-2">({ev.evidence_type})</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] text-indigo-400">
                        {ev.evidence_hash.slice(0, 10)}...
                      </span>
                      <span
                        className={`px-1.5 py-0.2 rounded text-[10px] font-sans ${
                          ev.result === "allow" || ev.result === "completed"
                            ? "text-emerald-400 bg-emerald-500/10"
                            : "text-rose-400 bg-rose-500/10"
                        }`}
                      >
                        {ev.result}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Reclassification Modal */}
      <ClassificationReviewModal
        isOpen={reviewModalOpen}
        onClose={() => setReviewModalOpen(false)}
        onSubmit={handleClassificationSubmit}
        asset={asset}
      />
    </div>
  );
}
