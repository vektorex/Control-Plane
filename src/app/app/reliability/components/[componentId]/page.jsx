"use client";

import React, { useState, useEffect, useCallback, use } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  Server,
  Activity,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  HelpCircle,
  Clock,
  Zap,
  RotateCcw,
  ShieldAlert,
  GitBranch,
  RefreshCw,
} from "lucide-react";
import { reliabilityService } from "@/services/reliability";

export default function ComponentDetailPage({ params }) {
  const unwrappedParams = use(params);
  const componentId = unwrappedParams.componentId;

  const [component, setComponent] = useState(null);
  const [dependencies, setDependencies] = useState([]);
  const [circuit, setCircuit] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState("");

  const fetchData = useCallback(async () => {
    try {
      setIsLoading(true);
      setErrorMsg("");

      const [compRes, depRes, cctRes] = await Promise.allSettled([
        reliabilityService.getComponent(componentId),
        reliabilityService.listDependencies({ componentId }),
        reliabilityService.getCircuits(),
      ]);

      if (compRes.status === "fulfilled") {
        setComponent(compRes.value);
        if (cctRes.status === "fulfilled" && cctRes.value) {
          const compName = compRes.value.component_name;
          const found = cctRes.value[compName] || cctRes.value[componentId];
          setCircuit(found || null);
        }
      } else {
        throw new Error("Failed to load component details.");
      }

      if (depRes.status === "fulfilled") {
        setDependencies(depRes.value || []);
      }
    } catch (err) {
      setErrorMsg(err.message || "Failed to load component.");
    } finally {
      setIsLoading(false);
    }
  }, [componentId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  if (isLoading && !component) {
    return (
      <div className="p-8 text-center text-slate-400 text-sm">
        <RefreshCw className="w-5 h-5 animate-spin mx-auto mb-2 text-indigo-400" />
        Loading component reliability metrics...
      </div>
    );
  }

  if (errorMsg || !component) {
    return (
      <div className="p-6 max-w-4xl mx-auto space-y-4">
        <Link
          href="/app/reliability/components"
          className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200"
        >
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Components
        </Link>
        <div className="p-4 bg-red-950/40 border border-red-800 rounded-xl text-red-200 text-sm">
          {errorMsg || "Component not found."}
        </div>
      </div>
    );
  }

  const successRate =
    component.success_count + component.failure_count > 0
      ? (
          (component.success_count /
            (component.success_count + component.failure_count)) *
          100
        ).toFixed(2)
      : "100.00";

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      {/* Back button */}
      <div>
        <Link
          href="/app/reliability/components"
          className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 transition mb-2"
        >
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Component Registry
        </Link>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-slate-900 border border-slate-800 rounded-xl">
              <Server className="w-6 h-6 text-indigo-400" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl font-bold text-white tracking-tight">
                  {component.component_name}
                </h1>
                <span className="font-mono text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                  {component.component_type}
                </span>
              </div>
              <p className="text-xs font-mono text-slate-500 mt-0.5">
                ID: {component.id} • Version: {component.version || "1.0.0"}
              </p>
            </div>
          </div>

          <button
            onClick={fetchData}
            disabled={isLoading}
            className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
            title="Refresh component metrics"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl">
          <span className="text-xs text-slate-400 uppercase font-semibold">Health Status</span>
          <div className="mt-2 flex items-center gap-2">
            {component.health_status === "healthy" ? (
              <span className="inline-flex items-center gap-1.5 text-sm font-bold text-emerald-400">
                <CheckCircle2 className="w-4 h-4" /> Healthy
              </span>
            ) : component.health_status === "warning" ? (
              <span className="inline-flex items-center gap-1.5 text-sm font-bold text-amber-400">
                <AlertTriangle className="w-4 h-4" /> Warning
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 text-sm font-bold text-red-400">
                <XCircle className="w-4 h-4" /> Critical
              </span>
            )}
          </div>
          <span className="text-[11px] text-slate-500 mt-1 block">
            Operational status: {component.status}
          </span>
        </div>

        <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl">
          <span className="text-xs text-slate-400 uppercase font-semibold">Success Rate</span>
          <div className="mt-2 text-2xl font-bold font-mono text-white">
            {successRate}%
          </div>
          <span className="text-[11px] text-slate-500 font-mono mt-1 block">
            {component.success_count} success / {component.failure_count} failure
          </span>
        </div>

        <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl">
          <span className="text-xs text-slate-400 uppercase font-semibold">Circuit Protection</span>
          <div className="mt-2">
            {circuit ? (
              <span
                className={`inline-flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded border ${
                  circuit.state === "open"
                    ? "bg-red-950 text-red-400 border-red-800"
                    : circuit.state === "half_open"
                    ? "bg-amber-950 text-amber-400 border-amber-800"
                    : "bg-emerald-950 text-emerald-400 border-emerald-800"
                }`}
              >
                <Zap className="w-3 h-3" /> {circuit.state.toUpperCase()}
              </span>
            ) : (
              <span className="text-xs text-slate-400">Standard / Pass-through</span>
            )}
          </div>
          <span className="text-[11px] text-slate-500 mt-1 block">
            {circuit ? `Threshold: ${circuit.failure_threshold} failures` : "No circuit breaker assigned"}
          </span>
        </div>

        <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl">
          <span className="text-xs text-slate-400 uppercase font-semibold">Last Heartbeat</span>
          <div className="mt-2 text-xs font-mono text-slate-300 flex items-center gap-1.5">
            <Clock className="w-3.5 h-3.5 text-slate-500" />
            {component.last_heartbeat_at
              ? new Date(component.last_heartbeat_at).toLocaleString()
              : "Never"}
          </div>
          <span className="text-[11px] text-slate-500 mt-1 block">
            Last failure:{" "}
            {component.last_failure_at
              ? new Date(component.last_failure_at).toLocaleTimeString()
              : "None"}
          </span>
        </div>
      </div>

      {/* Downstream Dependencies List */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <GitBranch className="w-4 h-4 text-indigo-400" />
            <h3 className="text-sm font-semibold text-white">Downstream Health & Probe Checks</h3>
          </div>
          <span className="text-xs text-slate-500">
            {dependencies.length} health checks recorded
          </span>
        </div>

        {dependencies.length === 0 ? (
          <div className="p-8 text-center text-slate-500 text-xs font-mono">
            No active probe checks registered for this component.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="bg-slate-950/60 text-xs uppercase text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="py-2.5 px-4 font-semibold">Check Type</th>
                  <th className="py-2.5 px-4 font-semibold">Status</th>
                  <th className="py-2.5 px-4 font-semibold">Latency</th>
                  <th className="py-2.5 px-4 font-semibold">Error Type</th>
                  <th className="py-2.5 px-4 font-semibold">Checked At</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono text-xs">
                {dependencies.map((dep) => (
                  <tr key={dep.id} className="hover:bg-slate-800/40 transition">
                    <td className="py-2.5 px-4 font-semibold text-slate-200">
                      {dep.check_type}
                    </td>
                    <td className="py-2.5 px-4">
                      {dep.status === "healthy" ? (
                        <span className="text-emerald-400">healthy</span>
                      ) : (
                        <span className="text-red-400 font-bold">{dep.status}</span>
                      )}
                    </td>
                    <td className="py-2.5 px-4 text-slate-300">
                      {dep.latency_ms != null ? `${dep.latency_ms}ms` : "-"}
                    </td>
                    <td className="py-2.5 px-4 text-slate-400">
                      {dep.error_type || "None"}
                    </td>
                    <td className="py-2.5 px-4 text-slate-500">
                      {new Date(dep.checked_at).toLocaleTimeString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Security Incident Bridge Info */}
      <div className="p-4 bg-slate-950/50 border border-slate-800 rounded-xl flex items-center justify-between text-xs">
        <div className="flex items-center gap-2 text-slate-300">
          <ShieldAlert className="w-4 h-4 text-indigo-400" />
          <span>
            Reliability failures correlated with security attacks or containment triggers are logged in Security Operations.
          </span>
        </div>
        <Link
          href="/app/security"
          className="text-indigo-400 hover:text-indigo-300 font-medium"
        >
          View Security Operations →
        </Link>
      </div>
    </div>
  );
}
