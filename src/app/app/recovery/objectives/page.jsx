"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { ArrowLeft, Target, Plus, RefreshCw, Clock, X } from "lucide-react";
import { recoveryService } from "@/services/recovery";

export default function RecoveryObjectivesPage() {
  const [objectives, setObjectives] = useState([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [resourceType, setResourceType] = useState("database");
  const [rtoSeconds, setRtoSeconds] = useState(7200);
  const [rpoSeconds, setRpoSeconds] = useState(86400);
  const [priority, setPriority] = useState("tier_1");
  const [isLoading, setIsLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState("");

  const fetchData = useCallback(async () => {
    try {
      setIsLoading(true);
      setErrorMsg("");
      const res = await recoveryService.listObjectives();
      setObjectives(res || []);
    } catch (err) {
      setErrorMsg(err.message || "Failed to load recovery objectives.");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleCreate = async (e) => {
    e.preventDefault();
    try {
      await recoveryService.createObjective({
        resource_type: resourceType,
        rto_seconds: parseInt(rtoSeconds, 10),
        rpo_seconds: parseInt(rpoSeconds, 10),
        priority,
      });
      setIsModalOpen(false);
      fetchData();
    } catch (err) {
      alert(`Error creating objective: ${err.message}`);
    }
  };

  const formatDuration = (sec) => {
    if (sec < 3600) return `${Math.round(sec / 60)}m`;
    return `${(sec / 3600).toFixed(1)}h`;
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div className="space-y-1">
          <Link
            href="/app/recovery"
            className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 transition mb-1"
          >
            <ArrowLeft className="w-3.5 h-3.5" /> Back to Recovery Dashboard
          </Link>
          <div className="flex items-center gap-2">
            <Target className="w-6 h-6 text-indigo-400" />
            <h1 className="text-xl font-bold text-white tracking-tight">
              Recovery Objectives (RTO / RPO)
            </h1>
          </div>
          <p className="text-xs text-slate-400">
            Define Recovery Time Objectives (target restore duration) and Recovery Point Objectives (acceptable data loss interval).
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsModalOpen(true)}
            className="inline-flex items-center gap-2 px-3.5 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-sm transition"
          >
            <Plus className="w-4 h-4" /> Add Objective
          </button>
          <button
            onClick={fetchData}
            disabled={isLoading}
            className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
            title="Refresh"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      {errorMsg && (
        <div className="p-4 rounded-xl bg-red-950/40 border border-red-800 text-red-200 text-sm">
          {errorMsg}
        </div>
      )}

      {/* Objectives Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-white">Configured Operational Targets</h3>
          <span className="text-xs text-slate-500 font-mono">{objectives.length} objectives</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="bg-slate-950/60 text-xs uppercase text-slate-400 border-b border-slate-800">
              <tr>
                <th className="py-3 px-4 font-semibold">Subsystem Resource</th>
                <th className="py-3 px-4 font-semibold">Scope</th>
                <th className="py-3 px-4 font-semibold">Priority Tier</th>
                <th className="py-3 px-4 font-semibold">Target RTO (Restore)</th>
                <th className="py-3 px-4 font-semibold">Target RPO (Data Loss)</th>
                <th className="py-3 px-4 font-semibold text-right">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono text-xs">
              {objectives.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-slate-500 font-sans">
                    No recovery objectives defined. Click &quot;Add Objective&quot; to set RTO/RPO targets.
                  </td>
                </tr>
              ) : (
                objectives.map((obj) => (
                  <tr key={obj.id} className="hover:bg-slate-800/40 transition">
                    <td className="py-3 px-4 font-semibold text-white capitalize font-sans">
                      {obj.resource_type.replace(/_/g, " ")}
                    </td>
                    <td className="py-3 px-4 text-slate-400">{obj.resource_scope}</td>
                    <td className="py-3 px-4 uppercase text-indigo-300 font-semibold">
                      {obj.priority.replace(/_/g, " ")}
                    </td>
                    <td className="py-3 px-4 text-emerald-400 font-bold">
                      {formatDuration(obj.rto_seconds)} ({obj.rto_seconds}s)
                    </td>
                    <td className="py-3 px-4 text-amber-400 font-bold">
                      {formatDuration(obj.rpo_seconds)} ({obj.rpo_seconds}s)
                    </td>
                    <td className="py-3 px-4 text-right font-sans">
                      <span className="text-xs px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800">
                        Active
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-800 rounded-xl w-full max-w-md overflow-hidden shadow-2xl">
            <div className="p-4 border-b border-slate-800 flex items-center justify-between">
              <h2 className="text-sm font-semibold text-white">Add Recovery Objective</h2>
              <button onClick={() => setIsModalOpen(false)} className="text-slate-400 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>
            <form onSubmit={handleCreate} className="p-5 space-y-4 text-xs">
              <div>
                <label className="block text-slate-300 font-medium mb-1">Resource Type</label>
                <input
                  type="text"
                  required
                  value={resourceType}
                  onChange={(e) => setResourceType(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 text-white rounded p-2"
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-300 font-medium mb-1">Target RTO (seconds)</label>
                  <input
                    type="number"
                    required
                    value={rtoSeconds}
                    onChange={(e) => setRtoSeconds(e.target.value)}
                    className="w-full bg-slate-800 border border-slate-700 text-white rounded p-2 font-mono"
                  />
                </div>
                <div>
                  <label className="block text-slate-300 font-medium mb-1">Target RPO (seconds)</label>
                  <input
                    type="number"
                    required
                    value={rpoSeconds}
                    onChange={(e) => setRpoSeconds(e.target.value)}
                    className="w-full bg-slate-800 border border-slate-700 text-white rounded p-2 font-mono"
                  />
                </div>
              </div>
              <div>
                <label className="block text-slate-300 font-medium mb-1">Priority</label>
                <select
                  value={priority}
                  onChange={(e) => setPriority(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 text-white rounded p-2 font-mono"
                >
                  <option value="tier_1">Tier 1 (Mission Critical)</option>
                  <option value="tier_2">Tier 2 (High)</option>
                  <option value="tier_3">Tier 3 (Standard)</option>
                </select>
              </div>
              <div className="flex justify-end gap-2 pt-2 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-3 py-1.5 text-slate-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded font-semibold"
                >
                  Save Objective
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
