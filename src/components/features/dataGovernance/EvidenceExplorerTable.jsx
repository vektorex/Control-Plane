"use client";

import React, { useState } from "react";
import {
  FileCheck2,
  Copy,
  Check,
  Search,
  Filter,
  Link as LinkIcon,
  ShieldAlert,
  ShieldCheck,
  User,
  Clock,
} from "lucide-react";

export function EvidenceExplorerTable({
  evidence = [],
  loading = false,
  onRefresh,
}) {
  const [searchTerm, setSearchTerm] = useState("");
  const [typeFilter, setTypeFilter] = useState("all");
  const [resultFilter, setResultFilter] = useState("all");
  const [copiedHash, setCopiedHash] = useState(null);

  const handleCopy = (hash) => {
    if (!hash) return;
    navigator.clipboard.writeText(hash);
    setCopiedHash(hash);
    setTimeout(() => setCopiedHash(null), 2000);
  };

  const filtered = evidence.filter((item) => {
    const matchesSearch =
      !searchTerm ||
      item.subject_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.action.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (item.actor_id && item.actor_id.toLowerCase().includes(searchTerm.toLowerCase()));

    const matchesType =
      typeFilter === "all" || item.evidence_type.toLowerCase() === typeFilter.toLowerCase();

    const matchesResult =
      resultFilter === "all" || item.result.toLowerCase() === resultFilter.toLowerCase();

    return matchesSearch && matchesType && matchesResult;
  });

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/60 backdrop-blur-sm overflow-hidden">
      {/* Search and Filters */}
      <div className="p-4 border-b border-slate-800/80 flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="relative w-full sm:w-72">
          <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
          <input
            type="text"
            placeholder="Search subjects, actors, actions..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 bg-slate-950/80 border border-slate-800 rounded-lg text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
          />
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="px-2.5 py-1.5 bg-slate-950/80 border border-slate-800 rounded-lg text-xs text-slate-300 focus:outline-none focus:border-indigo-500"
          >
            <option value="all">All Evidence Types</option>
            <option value="governance_decision">Governance Decisions</option>
            <option value="access_check">Access Checks</option>
            <option value="classification">Classifications</option>
            <option value="retention_evaluation">Retention</option>
            <option value="deletion">Deletions</option>
            <option value="export">Exports</option>
            <option value="legal_hold">Legal Holds</option>
            <option value="approval">Approvals</option>
          </select>

          <select
            value={resultFilter}
            onChange={(e) => setResultFilter(e.target.value)}
            className="px-2.5 py-1.5 bg-slate-950/80 border border-slate-800 rounded-lg text-xs text-slate-300 focus:outline-none focus:border-indigo-500"
          >
            <option value="all">All Results</option>
            <option value="allow">Allow</option>
            <option value="deny">Deny</option>
            <option value="blocked">Blocked</option>
            <option value="completed">Completed</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm text-slate-300">
          <thead className="bg-slate-950/60 text-xs font-semibold uppercase tracking-wider text-slate-400 border-b border-slate-800">
            <tr>
              <th className="py-3 px-4">Timestamp (UTC)</th>
              <th className="py-3 px-4">Type</th>
              <th className="py-3 px-4">Subject</th>
              <th className="py-3 px-4">Action & Result</th>
              <th className="py-3 px-4">Actor</th>
              <th className="py-3 px-4">SHA-256 Hash Chain</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 font-mono text-xs">
            {loading ? (
              [...Array(5)].map((_, i) => (
                <tr key={i} className="animate-pulse">
                  <td colSpan={6} className="py-4 px-4 h-12 bg-slate-900/30" />
                </tr>
              ))
            ) : filtered.length === 0 ? (
              <tr>
                <td colSpan={6} className="py-8 text-center text-slate-400 font-sans text-sm">
                  No compliance evidence records found.
                </td>
              </tr>
            ) : (
              filtered.map((item) => {
                const isDenyOrBlock =
                  item.result.toLowerCase() === "deny" ||
                  item.result.toLowerCase() === "blocked";
                const isSuccess =
                  item.result.toLowerCase() === "allow" ||
                  item.result.toLowerCase() === "completed" ||
                  item.result.toLowerCase() === "success";

                return (
                  <tr
                    key={item.id}
                    className="hover:bg-slate-800/40 transition-colors"
                  >
                    <td className="py-3 px-4 text-slate-400">
                      <div className="flex items-center gap-1.5">
                        <Clock className="w-3 h-3 text-slate-500" />
                        <span>
                          {item.timestamp ? new Date(item.timestamp).toISOString().replace("T", " ").slice(0, 19) : "-"}
                        </span>
                      </div>
                    </td>

                    <td className="py-3 px-4 font-sans">
                      <span className="px-2 py-0.5 rounded bg-slate-800 border border-slate-700/60 text-[11px] text-slate-300">
                        {item.evidence_type}
                      </span>
                    </td>

                    <td className="py-3 px-4">
                      <div className="text-slate-200">
                        {item.subject_type}:
                        <span className="text-slate-400 ml-1 truncate max-w-[120px] inline-block align-bottom">
                          {item.subject_id}
                        </span>
                      </div>
                    </td>

                    <td className="py-3 px-4 font-sans">
                      <div className="flex items-center gap-2">
                        <span className="text-slate-300 font-medium">{item.action}</span>
                        <span
                          className={`px-1.5 py-0.5 rounded text-[10px] font-semibold uppercase ${
                            isDenyOrBlock
                              ? "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                              : isSuccess
                              ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                              : "bg-slate-800 text-slate-400"
                          }`}
                        >
                          {item.result}
                        </span>
                      </div>
                    </td>

                    <td className="py-3 px-4 text-slate-400 font-sans">
                      <div className="flex items-center gap-1">
                        <User className="w-3 h-3 text-slate-500" />
                        <span className="truncate max-w-[100px]">
                          {item.actor_type || "system"}
                        </span>
                      </div>
                    </td>

                    <td className="py-3 px-4">
                      <div className="flex items-center gap-2">
                        <div className="flex flex-col gap-0.5">
                          <div className="flex items-center gap-1 text-[11px] text-indigo-400">
                            <span className="text-slate-500 text-[10px]">curr:</span>
                            <span>{item.evidence_hash.slice(0, 14)}...</span>
                            <button
                              onClick={() => handleCopy(item.evidence_hash)}
                              className="text-slate-500 hover:text-white"
                              title="Copy full SHA-256 hash"
                            >
                              {copiedHash === item.evidence_hash ? (
                                <Check className="w-3 h-3 text-emerald-400" />
                              ) : (
                                <Copy className="w-3 h-3" />
                              )}
                            </button>
                          </div>
                          {item.previous_evidence_hash && (
                            <div className="flex items-center gap-1 text-[10px] text-slate-500">
                              <span>prev:</span>
                              <span>{item.previous_evidence_hash.slice(0, 10)}...</span>
                            </div>
                          )}
                        </div>
                        <div
                          className="w-2 h-2 rounded-full bg-emerald-400 shrink-0"
                          title="Chained cryptographic hash verified"
                        />
                      </div>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
