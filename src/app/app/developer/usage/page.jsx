"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  Activity,
  ArrowLeft,
  RefreshCw,
  BarChart3,
  Clock,
  Zap,
  CheckCircle2,
  AlertTriangle,
  Coins,
  ShieldCheck,
  Filter,
} from "lucide-react";
import { developerService } from "@/services/developer";

export default function DeveloperUsagePage() {
  const [applications, setApplications] = useState([]);
  const [selectedAppId, setSelectedAppId] = useState("");
  const [periodHours, setPeriodHours] = useState("24");
  const [usageData, setUsageData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function loadApps() {
      try {
        const appsRes = await developerService.listApplications();
        const apps = appsRes.items || [];
        setApplications(apps);
        if (apps.length > 0) {
          setSelectedAppId(apps[0].id);
        } else {
          setLoading(false);
        }
      } catch (err) {
        console.error("Failed to load applications for usage:", err);
        setError("Failed to load applications.");
        setLoading(false);
      }
    }
    loadApps();
  }, []);

  useEffect(() => {
    if (!selectedAppId) return;
    loadUsage();
  }, [selectedAppId, periodHours]);

  async function loadUsage() {
    setLoading(true);
    setError(null);
    try {
      const data = await developerService.getApplicationUsage(selectedAppId, {
        periodHours: parseInt(periodHours, 10),
      });
      setUsageData(data);
    } catch (err) {
      console.error("Failed to load usage data:", err);
      setError("Failed to load usage metrics for this application.");
    } finally {
      setLoading(false);
    }
  }

  const totalRequests = usageData?.total_requests || 0;
  const totalErrors = usageData?.total_errors || 0;
  const errorRate = totalRequests > 0 ? ((totalErrors / totalRequests) * 100).toFixed(1) : "0.0";
  const avgLatency = usageData?.avg_latency_ms ? Math.round(usageData.avg_latency_ms) : 0;
  const totalTokens = usageData?.total_tokens || 0;
  const totalCost = usageData?.total_cost != null ? `$${usageData.total_cost.toFixed(4)}` : "$0.0000";

  return (
    <div className="space-y-6">
      {/* Disclaimer Banner */}
      <div className="p-3.5 bg-blue-500/10 border border-blue-500/20 rounded-xl flex items-center justify-between text-xs text-blue-300">
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-blue-400 shrink-0" />
          <span>
            The Public API provides controlled programmatic access to the platform. API availability, limits, and capabilities are subject to the platform&apos;s configured policies and operational state.
          </span>
        </div>
        <Link href="/app/developer/docs" className="text-blue-400 hover:underline shrink-0 ml-4 font-medium">
          View Docs
        </Link>
      </div>

      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs text-slate-400 mb-1">
            <Link href="/app/developer" className="hover:text-white transition flex items-center gap-1">
              <ArrowLeft className="w-3.5 h-3.5" />
              Developer Platform
            </Link>
            <span>/</span>
            <span className="text-slate-200">API Usage & Telemetry</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <BarChart3 className="w-6 h-6 text-indigo-400" />
            API Usage & Telemetry
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Monitor real-time consumption, latency distribution, rate-limit consumption, and error rates.
          </p>
        </div>

        {/* Filter Controls */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400 font-medium">App:</span>
            <select
              value={selectedAppId}
              onChange={(e) => setSelectedAppId(e.target.value)}
              className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
              disabled={applications.length === 0}
            >
              {applications.length === 0 && <option value="">No applications found</option>}
              {applications.map((app) => (
                <option key={app.id} value={app.id}>
                  {app.name} ({app.environment})
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400 font-medium">Window:</span>
            <select
              value={periodHours}
              onChange={(e) => setPeriodHours(e.target.value)}
              className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
            >
              <option value="1">Last 1 Hour</option>
              <option value="24">Last 24 Hours</option>
              <option value="168">Last 7 Days</option>
              <option value="720">Last 30 Days</option>
            </select>
          </div>

          <button
            onClick={loadUsage}
            disabled={loading || !selectedAppId}
            className="p-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg border border-slate-700 transition"
            title="Refresh"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin text-indigo-400" : ""}`} />
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-sm text-red-400 flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          {error}
        </div>
      )}

      {/* Metrics Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
            <span>Total Requests</span>
            <Activity className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="text-2xl font-bold text-white">
            {loading ? "..." : totalRequests.toLocaleString()}
          </div>
          <div className="text-xs text-slate-500 mt-1">in selected window</div>
        </div>

        <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
            <span>Error Rate</span>
            {totalErrors > 0 ? (
              <AlertTriangle className="w-4 h-4 text-amber-400" />
            ) : (
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            )}
          </div>
          <div className="text-2xl font-bold text-white">
            {loading ? "..." : `${errorRate}%`}
          </div>
          <div className="text-xs text-slate-500 mt-1">{totalErrors} failed requests</div>
        </div>

        <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
            <span>Avg Latency</span>
            <Clock className="w-4 h-4 text-sky-400" />
          </div>
          <div className="text-2xl font-bold text-white">
            {loading ? "..." : `${avgLatency} ms`}
          </div>
          <div className="text-xs text-slate-500 mt-1">round-trip response</div>
        </div>

        <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
            <span>Tokens Consumed</span>
            <Zap className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-bold text-white">
            {loading ? "..." : totalTokens.toLocaleString()}
          </div>
          <div className="text-xs text-slate-500 mt-1">via AI Gateway</div>
        </div>

        <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
            <span>Est. Cost</span>
            <Coins className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-white">
            {loading ? "..." : totalCost}
          </div>
          <div className="text-xs text-slate-500 mt-1">budget telemetry</div>
        </div>
      </div>

      {/* Breakdown by Endpoint */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
            <Filter className="w-4 h-4 text-indigo-400" />
            Endpoint Breakdown
          </h2>
          <span className="text-xs text-slate-500">
            {usageData?.by_endpoint?.length || 0} active routes
          </span>
        </div>

        {loading ? (
          <div className="py-12 text-center text-sm text-slate-500">Loading endpoint metrics...</div>
        ) : !usageData?.by_endpoint || usageData.by_endpoint.length === 0 ? (
          <div className="py-12 text-center text-sm text-slate-500">
            No API activity recorded for this application in the selected period.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-800/50 text-slate-400 uppercase font-mono text-[10px]">
                <tr>
                  <th className="py-2.5 px-3">Method</th>
                  <th className="py-2.5 px-3">Endpoint</th>
                  <th className="py-2.5 px-3 text-right">Requests</th>
                  <th className="py-2.5 px-3 text-right">Errors</th>
                  <th className="py-2.5 px-3 text-right">Avg Latency</th>
                  <th className="py-2.5 px-3 text-right">Tokens</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800 font-mono">
                {usageData.by_endpoint.map((row, idx) => {
                  const m = row.method || "GET";
                  const methodColor =
                    m === "GET"
                      ? "text-sky-400 bg-sky-500/10 border-sky-500/20"
                      : m === "POST"
                      ? "text-emerald-400 bg-emerald-500/10 border-emerald-500/20"
                      : m === "DELETE"
                      ? "text-red-400 bg-red-500/10 border-red-500/20"
                      : "text-amber-400 bg-amber-500/10 border-amber-500/20";

                  return (
                    <tr key={idx} className="hover:bg-slate-800/30 transition">
                      <td className="py-2 px-3">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${methodColor}`}>
                          {m}
                        </span>
                      </td>
                      <td className="py-2 px-3 text-slate-200">{row.endpoint}</td>
                      <td className="py-2 px-3 text-right text-slate-200 font-semibold">
                        {(row.requests || 0).toLocaleString()}
                      </td>
                      <td className="py-2 px-3 text-right">
                        {row.errors > 0 ? (
                          <span className="text-amber-400 font-semibold">{row.errors}</span>
                        ) : (
                          <span className="text-slate-500">0</span>
                        )}
                      </td>
                      <td className="py-2 px-3 text-right text-slate-400">
                        {row.avg_latency_ms ? `${Math.round(row.avg_latency_ms)} ms` : "—"}
                      </td>
                      <td className="py-2 px-3 text-right text-slate-400">
                        {row.tokens ? row.tokens.toLocaleString() : "—"}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Quota & Rate Limit Summary */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5">
        <h2 className="text-sm font-semibold text-slate-200 mb-2">Governance & Reliability Limits</h2>
        <p className="text-xs text-slate-400 mb-4">
          All endpoints enforce Step 32 Governance budgets and Step 35 Reliability sliding-window rate limits. Requests exceeding quota or rate ceilings return standard HTTP 429 with <code className="text-indigo-400">Retry-After</code> headers.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
          <div className="p-3 bg-slate-800/50 rounded-lg border border-slate-800">
            <div className="font-semibold text-slate-300">Requests per Minute (RPM)</div>
            <div className="text-slate-400 mt-1">Default 120 RPM sliding window per credential.</div>
          </div>
          <div className="p-3 bg-slate-800/50 rounded-lg border border-slate-800">
            <div className="font-semibold text-slate-300">Requests per Hour (RPH)</div>
            <div className="text-slate-400 mt-1">Default 2,000 RPH sliding window per application.</div>
          </div>
          <div className="p-3 bg-slate-800/50 rounded-lg border border-slate-800">
            <div className="font-semibold text-slate-300">Concurrent Executions</div>
            <div className="text-slate-400 mt-1">Bounded concurrency protection against resource exhaustion.</div>
          </div>
        </div>
      </div>
    </div>
  );
}
