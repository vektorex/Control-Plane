"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  Plug,
  CheckCircle2,
  AlertCircle,
  ShieldCheck,
  Search,
  ExternalLink,
  Lock,
  RefreshCw,
  GitBranch,
  FileCode2,
  FolderGit2,
  MessageSquareCode,
  Layers,
  Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { useWorkspace } from "@/lib/workspaceContext";
import { connectorService } from "@/services/connectors";

export default function ConnectorsPage() {
  const { activeWorkspace } = useWorkspace();
  const [connectors, setConnectors] = useState([]);
  const [statuses, setStatuses] = useState({});
  const [searchQuery, setSearchQuery] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("ALL");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchConnectorsAndStatuses = async () => {
    try {
      setIsLoading(true);
      setError(null);

      const connList = await connectorService.listConnectors();
      setConnectors(connList || []);

      // Fetch status for each connector
      const statusMap = {};
      for (const conn of connList || []) {
        try {
          const st = await connectorService.getStatus(conn.name);
          statusMap[conn.name] = st;
        } catch {
          statusMap[conn.name] = { status: "disconnected" };
        }
      }
      setStatuses(statusMap);
    } catch (err) {
      console.error("[ConnectorsPage] Error fetching connectors:", err);
      setError(err.message || "Failed to load connectors");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchConnectorsAndStatuses();
  }, [activeWorkspace?.id]);

  const filteredConnectors = connectors.filter((conn) => {
    const matchesSearch =
      conn.display_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      conn.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      conn.name.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory =
      categoryFilter === "ALL" ||
      (categoryFilter === "CONNECTED" && statuses[conn.name]?.status === "connected") ||
      conn.category === categoryFilter;
    return matchesSearch && matchesCategory;
  });

  const connectedCount = Object.values(statuses).filter((s) => s?.status === "connected").length;

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-12">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
              <Plug className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-slate-100 tracking-tight">External Connectors</h1>
              <p className="text-xs text-slate-400">
                Securely connect repositories, data sources, and external tools to the LLM Work Layer.
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <Badge
            variant="outline"
            className="border-slate-800 bg-slate-900/80 text-slate-300 font-mono text-xs px-3 py-1 flex items-center gap-1.5"
          >
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            <span>AES-256-GCM Encrypted</span>
          </Badge>
          <Button
            variant="outline"
            size="sm"
            onClick={fetchConnectorsAndStatuses}
            disabled={isLoading}
            className="border-slate-800 text-slate-300 hover:bg-slate-850 gap-1.5 text-xs"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? "animate-spin" : ""}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Security Banner */}
      <div className="rounded-xl border border-indigo-500/20 bg-gradient-to-r from-indigo-950/40 via-slate-900/60 to-purple-950/30 p-4.5 text-xs text-slate-300 space-y-2">
        <div className="flex items-center justify-between font-semibold text-indigo-200">
          <div className="flex items-center gap-2">
            <Lock className="w-4 h-4 text-indigo-400" />
            <span>Zero-Trust Connector Security Policy</span>
          </div>
          <span className="text-[11px] font-mono text-indigo-400 bg-indigo-950/80 px-2 py-0.5 rounded border border-indigo-800/40">
            trust_level: external_untrusted
          </span>
        </div>
        <p className="text-slate-400 leading-relaxed text-[11px]">
          All external connector payloads are treated as untrusted data. Instructions returned from external repositories
          cannot override system policies, workflow step validations, or prompt boundaries. Credentials are never returned
          in API responses and are encrypted at rest.
        </p>
      </div>

      {/* Filters and Search */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="flex items-center gap-1.5 bg-slate-900/90 border border-slate-800 p-1 rounded-lg w-full sm:w-auto overflow-x-auto">
          {["ALL", "CONNECTED", "code", "productivity", "databases"].map((cat) => (
            <button
              key={cat}
              onClick={() => setCategoryFilter(cat)}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all capitalize ${
                categoryFilter === cat
                  ? "bg-indigo-600 text-white shadow-sm"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
              }`}
            >
              {cat === "ALL" ? "All Connectors" : cat === "CONNECTED" ? `Connected (${connectedCount})` : cat}
            </button>
          ))}
        </div>

        <div className="relative w-full sm:w-64">
          <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
          <input
            type="text"
            placeholder="Search connectors..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-slate-900/90 border border-slate-800 rounded-lg pl-8 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
          />
        </div>
      </div>

      {/* Error state */}
      {error && (
        <div className="rounded-lg border border-red-500/30 bg-red-950/20 p-4 text-xs text-red-300 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Connector Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {filteredConnectors.map((conn) => {
          const status = statuses[conn.name] || { status: "disconnected" };
          const isConnected = status.status === "connected";

          return (
            <div
              key={conn.name}
              className="rounded-xl border border-slate-800/80 bg-slate-900/60 backdrop-blur-sm p-5 flex flex-col justify-between hover:border-slate-700/90 transition-all group"
            >
              <div className="space-y-4">
                {/* Card Header */}
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-slate-800/90 border border-slate-700/60 flex items-center justify-center text-slate-200 group-hover:scale-105 transition-transform">
                      {conn.name === "github" ? (
                        <FolderGit2 className="w-5 h-5 text-indigo-400" />
                      ) : (
                        <Layers className="w-5 h-5 text-indigo-400" />
                      )}
                    </div>
                    <div>
                      <h3 className="font-semibold text-sm text-slate-100">{conn.display_name}</h3>
                      <span className="text-[10px] font-mono text-indigo-400 capitalize">{conn.category}</span>
                    </div>
                  </div>

                  {isConnected ? (
                    <span className="inline-flex items-center gap-1.5 text-[11px] font-medium text-emerald-400 bg-emerald-950/60 border border-emerald-800/40 px-2 py-0.5 rounded-full">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                      Connected
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 text-[11px] text-slate-400 bg-slate-800/60 px-2 py-0.5 rounded-full">
                      Disconnected
                    </span>
                  )}
                </div>

                {/* Description */}
                <p className="text-xs text-slate-400 leading-relaxed min-h-[36px]">
                  {conn.name === "github"
                    ? "Repository and development data. Search code, inspect pull requests, read issues, and retrieve file contents securely."
                    : conn.description}
                </p>

                {/* Account Details if connected */}
                {isConnected && status.account && (
                  <div className="rounded-lg bg-slate-950/60 border border-slate-800/60 px-3 py-2 text-[11px] text-slate-300 flex items-center justify-between">
                    <span className="text-slate-400">Account</span>
                    <span className="font-mono text-indigo-300 font-semibold">@{status.account.login}</span>
                  </div>
                )}

                {/* Capabilities list */}
                <div className="space-y-1.5">
                  <div className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">
                    Capabilities ({conn.supported_operations?.length || 0} operations)
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {conn.name === "github" ? (
                      <>
                        <span className="text-[10px] font-mono bg-indigo-950/40 border border-indigo-800/30 text-indigo-300 px-2 py-0.5 rounded">
                          repositories
                        </span>
                        <span className="text-[10px] font-mono bg-indigo-950/40 border border-indigo-800/30 text-indigo-300 px-2 py-0.5 rounded">
                          issues
                        </span>
                        <span className="text-[10px] font-mono bg-indigo-950/40 border border-indigo-800/30 text-indigo-300 px-2 py-0.5 rounded">
                          pull requests
                        </span>
                        <span className="text-[10px] font-mono bg-indigo-950/40 border border-indigo-800/30 text-indigo-300 px-2 py-0.5 rounded">
                          files
                        </span>
                        <span className="text-[10px] font-mono bg-indigo-950/40 border border-indigo-800/30 text-indigo-300 px-2 py-0.5 rounded">
                          code search
                        </span>
                      </>
                    ) : (
                      (conn.capabilities || []).map((cap) => (
                        <span
                          key={cap}
                          className="text-[10px] font-mono bg-slate-800 text-slate-300 px-2 py-0.5 rounded"
                        >
                          {cap}
                        </span>
                      ))
                    )}
                  </div>
                </div>
              </div>

              {/* Card Footer */}
              <div className="pt-5 mt-4 border-t border-slate-800/60 flex items-center justify-between">
                <span className="text-[10px] text-slate-400 font-mono">v{conn.version || "1.0.0"}</span>
                <Link href={`/app/connectors/${conn.name}`}>
                  <Button
                    size="sm"
                    className={`text-xs gap-1.5 ${
                      isConnected
                        ? "bg-slate-800 hover:bg-slate-750 text-slate-200 border border-slate-700/60"
                        : "bg-indigo-600 hover:bg-indigo-500 text-white shadow-md shadow-indigo-900/30"
                    }`}
                  >
                    {isConnected ? "Manage Connection" : "Configure & Connect"}
                    <ExternalLink className="w-3 h-3" />
                  </Button>
                </Link>
              </div>
            </div>
          );
        })}

        {/* Coming Soon Preview Cards */}
        <div className="rounded-xl border border-dashed border-slate-800 bg-slate-950/30 p-5 flex flex-col justify-between opacity-60 hover:opacity-80 transition-opacity">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-slate-850 border border-slate-800 flex items-center justify-center text-slate-400">
                  <MessageSquareCode className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-semibold text-sm text-slate-300">Slack / Discord</h3>
                  <span className="text-[10px] font-mono text-slate-400">Communication</span>
                </div>
              </div>
              <span className="text-[10px] bg-slate-800 text-slate-400 px-2 py-0.5 rounded font-mono">Coming Soon</span>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              Thread search, channel history indexing, and message context provider for automated team summaries.
            </p>
          </div>
          <div className="pt-4 border-t border-slate-850 text-[11px] text-slate-400">
            Extensible via <code className="text-indigo-400">BaseConnector</code> interface
          </div>
        </div>

        <div className="rounded-xl border border-dashed border-slate-800 bg-slate-950/30 p-5 flex flex-col justify-between opacity-60 hover:opacity-80 transition-opacity">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-slate-850 border border-slate-800 flex items-center justify-center text-slate-400">
                  <GitBranch className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-semibold text-sm text-slate-300">Jira / Linear</h3>
                  <span className="text-[10px] font-mono text-slate-400">Project Management</span>
                </div>
              </div>
              <span className="text-[10px] bg-slate-800 text-slate-400 px-2 py-0.5 rounded font-mono">Coming Soon</span>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              Ticket retrieval, sprint tracking, and automated task context synchronization for developer workflows.
            </p>
          </div>
          <div className="pt-4 border-t border-slate-850 text-[11px] text-slate-400">
            Zero changes required in core orchestration engine
          </div>
        </div>
      </div>
    </div>
  );
}
