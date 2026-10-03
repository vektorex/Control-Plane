"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  Database,
  Shield,
  ShieldAlert,
  AlertTriangle,
  GitFork,
  ExternalLink,
  Search,
  Filter,
  KeyRound,
  Eye,
  CheckCircle,
} from "lucide-react";

export function getClassificationBadge(classification) {
  switch ((classification || "").toLowerCase()) {
    case "restricted":
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">
          <ShieldAlert className="w-3 h-3 mr-1" />
          Restricted
        </span>
      );
    case "confidential":
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
          <AlertTriangle className="w-3 h-3 mr-1" />
          Confidential
        </span>
      );
    case "internal":
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-blue-500/10 text-blue-400 border border-blue-500/20">
          <Shield className="w-3 h-3 mr-1" />
          Internal
        </span>
      );
    case "public":
    default:
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
          <CheckCircle className="w-3 h-3 mr-1" />
          Public
        </span>
      );
  }
}

export function AssetListTable({
  assets = [],
  loading = false,
  onReviewClassification,
  onRefresh,
}) {
  const [searchTerm, setSearchTerm] = useState("");
  const [classificationFilter, setClassificationFilter] = useState("all");
  const [secretsFilter, setSecretsFilter] = useState("all");

  const filtered = assets.filter((a) => {
    const matchesSearch =
      !searchTerm ||
      a.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      a.resource_type.toLowerCase().includes(searchTerm.toLowerCase()) ||
      a.asset_type.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesClass =
      classificationFilter === "all" ||
      a.data_classification.toLowerCase() === classificationFilter.toLowerCase();

    const matchesSecrets =
      secretsFilter === "all" ||
      (secretsFilter === "secrets" && a.contains_secrets) ||
      (secretsFilter === "pii" && a.contains_personal_data);

    return matchesSearch && matchesClass && matchesSecrets;
  });

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/60 backdrop-blur-sm overflow-hidden">
      {/* Controls Bar */}
      <div className="p-4 border-b border-slate-800/80 flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="relative w-full sm:w-72">
          <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
          <input
            type="text"
            placeholder="Search assets, types, resources..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 bg-slate-950/80 border border-slate-800 rounded-lg text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-colors"
          />
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          <select
            value={classificationFilter}
            onChange={(e) => setClassificationFilter(e.target.value)}
            className="px-2.5 py-1.5 bg-slate-950/80 border border-slate-800 rounded-lg text-xs text-slate-300 focus:outline-none focus:border-indigo-500"
          >
            <option value="all">All Classifications</option>
            <option value="public">Public</option>
            <option value="internal">Internal</option>
            <option value="confidential">Confidential</option>
            <option value="restricted">Restricted</option>
          </select>

          <select
            value={secretsFilter}
            onChange={(e) => setSecretsFilter(e.target.value)}
            className="px-2.5 py-1.5 bg-slate-950/80 border border-slate-800 rounded-lg text-xs text-slate-300 focus:outline-none focus:border-indigo-500"
          >
            <option value="all">All Privacy Status</option>
            <option value="secrets">Contains Secrets</option>
            <option value="pii">Contains PII</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm text-slate-300">
          <thead className="bg-slate-950/60 text-xs font-semibold uppercase tracking-wider text-slate-400 border-b border-slate-800">
            <tr>
              <th className="py-3 px-4">Asset Name</th>
              <th className="py-3 px-4">Classification</th>
              <th className="py-3 px-4">Type</th>
              <th className="py-3 px-4">Privacy Flags</th>
              <th className="py-3 px-4">Storage</th>
              <th className="py-3 px-4">Status</th>
              <th className="py-3 px-4 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {loading ? (
              [...Array(5)].map((_, i) => (
                <tr key={i} className="animate-pulse">
                  <td colSpan={7} className="py-4 px-4 h-12 bg-slate-900/30" />
                </tr>
              ))
            ) : filtered.length === 0 ? (
              <tr>
                <td colSpan={7} className="py-8 text-center text-slate-400 text-sm">
                  No data assets match the specified filters.
                </td>
              </tr>
            ) : (
              filtered.map((asset) => (
                <tr
                  key={asset.id}
                  className="hover:bg-slate-800/40 transition-colors group"
                >
                  <td className="py-3 px-4">
                    <div className="font-medium text-slate-100 flex items-center gap-2">
                      <Database className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
                      <span className="truncate max-w-xs">{asset.name}</span>
                    </div>
                    <div className="text-xs text-slate-500 font-mono mt-0.5">
                      {asset.resource_id}
                    </div>
                  </td>
                  <td className="py-3 px-4">
                    {getClassificationBadge(asset.data_classification)}
                  </td>
                  <td className="py-3 px-4">
                    <span className="text-xs bg-slate-800 text-slate-300 px-2 py-0.5 rounded font-mono">
                      {asset.asset_type}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-1.5 flex-wrap">
                      {asset.contains_secrets && (
                        <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[11px] font-medium bg-rose-500/10 text-rose-400 border border-rose-500/20">
                          <KeyRound className="w-3 h-3 mr-0.5" />
                          Secret
                        </span>
                      )}
                      {asset.contains_personal_data && (
                        <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[11px] font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20">
                          PII
                        </span>
                      )}
                      {!asset.contains_secrets && !asset.contains_personal_data && (
                        <span className="text-xs text-slate-500">None detected</span>
                      )}
                    </div>
                  </td>
                  <td className="py-3 px-4 text-xs font-mono text-slate-400">
                    <span className="truncate max-w-[120px] block" title={asset.storage_location}>
                      {asset.storage_location}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <span
                      className={`text-xs px-2 py-0.5 rounded ${
                        asset.status === "active"
                          ? "bg-emerald-500/10 text-emerald-400"
                          : asset.status === "deleted"
                          ? "bg-rose-500/10 text-rose-400"
                          : "bg-slate-800 text-slate-400"
                      }`}
                    >
                      {asset.status}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <Link
                        href={`/app/data-governance/assets/${asset.id}`}
                        className="p-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-300 hover:text-white transition-colors"
                        title="View Asset Details & Lineage"
                      >
                        <Eye className="w-3.5 h-3.5" />
                      </Link>
                      {onReviewClassification && (
                        <button
                          onClick={() => onReviewClassification(asset)}
                          className="px-2 py-1 text-xs rounded-lg bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 transition-colors"
                        >
                          Reclassify
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
