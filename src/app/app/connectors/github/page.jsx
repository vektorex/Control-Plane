"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  FolderGit2,
  CheckCircle2,
  XCircle,
  AlertCircle,
  ShieldCheck,
  Lock,
  Key,
  Trash2,
  RefreshCw,
  Play,
  ArrowLeft,
  Search,
  ExternalLink,
  Code2,
  Sliders,
  Check,
  X,
  Info,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { useWorkspace } from "@/lib/workspaceContext";
import { connectorService } from "@/services/connectors";

export default function GitHubConnectorPage() {
  const { activeWorkspace } = useWorkspace();
  const [status, setStatus] = useState(null);
  const [operations, setOperations] = useState([]);
  const [permissions, setPermissions] = useState([]);
  const [tokenInput, setTokenInput] = useState("");
  const [accountLabel, setAccountLabel] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isConnecting, setIsConnecting] = useState(false);
  const [isTesting, setIsTesting] = useState(false);
  const [isDisconnecting, setIsDisconnecting] = useState(false);
  const [testResult, setTestResult] = useState(null);
  const [actionSuccess, setActionSuccess] = useState(null);
  const [error, setError] = useState(null);

  // Quick execution tester state
  const [selectedOp, setSelectedOp] = useState("search_repositories");
  const [execArgs, setExecArgs] = useState(JSON.stringify({ query: "fastapi" }, null, 2));
  const [isExecuting, setIsExecuting] = useState(false);
  const [execResult, setExecResult] = useState(null);

  const loadConnectorDetails = async () => {
    try {
      setIsLoading(true);
      setError(null);

      // Load status
      const statusRes = await connectorService.getStatus("github");
      setStatus(statusRes);

      // Load operations
      const opsRes = await connectorService.getOperations("github");
      setOperations(opsRes || []);

      // Load permissions
      const permsRes = await connectorService.getPermissions("github");
      setPermissions(permsRes || []);
    } catch (err) {
      console.error("[GitHubConnectorPage] Error loading details:", err);
      setError(err.message || "Failed to load GitHub connector details");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadConnectorDetails();
  }, [activeWorkspace?.id]);

  const handleConnect = async (e) => {
    e.preventDefault();
    if (!tokenInput.trim()) return;

    try {
      setIsConnecting(true);
      setError(null);
      setActionSuccess(null);

      const res = await connectorService.connect("github", {
        credential: tokenInput.trim(),
        credentialType: "pat",
        metadata: { label: accountLabel || "Personal Access Token" },
      });

      // Clear the sensitive input immediately
      setTokenInput("");
      setAccountLabel("");
      setStatus(res);
      setActionSuccess("GitHub Personal Access Token successfully validated and encrypted.");
      await loadConnectorDetails();
    } catch (err) {
      console.error("[GitHubConnectorPage] Connect error:", err);
      setError(err.message || "Failed to authenticate GitHub token.");
    } finally {
      setIsConnecting(false);
    }
  };

  const handleTestConnection = async () => {
    try {
      setIsTesting(true);
      setError(null);
      setTestResult(null);

      const res = await connectorService.testConnection("github");
      setTestResult(res);
      if (res.success) {
        setActionSuccess("Connection verified! Authenticated with GitHub API successfully.");
      } else {
        setError(res.error_message || "Connection verification failed.");
      }
    } catch (err) {
      console.error("[GitHubConnectorPage] Test connection error:", err);
      setError(err.message || "Error testing connection.");
    } finally {
      setIsTesting(false);
    }
  };

  const handleDisconnect = async () => {
    if (!confirm("Are you sure you want to disconnect GitHub? All encrypted tokens for this workspace will be deleted.")) {
      return;
    }

    try {
      setIsDisconnecting(true);
      setError(null);
      setTestResult(null);

      await connectorService.disconnect("github");
      setStatus({ connector: "github", status: "disconnected", has_credentials: false });
      setActionSuccess("GitHub connector disconnected.");
    } catch (err) {
      console.error("[GitHubConnectorPage] Disconnect error:", err);
      setError(err.message || "Failed to disconnect.");
    } finally {
      setIsDisconnecting(false);
    }
  };

  const handleTogglePermission = async (opName, currentEnabled) => {
    try {
      setError(null);
      const updated = await connectorService.updatePermission("github", {
        operation: opName,
        enabled: !currentEnabled,
        permissionLevel: "read",
      });

      setPermissions((prev) =>
        prev.map((p) => (p.operation === opName ? { ...p, enabled: updated.enabled } : p))
      );
    } catch (err) {
      console.error("[GitHubConnectorPage] Permission update error:", err);
      setError(err.message || "Failed to update operation permission.");
    }
  };

  const handleExecuteOperation = async () => {
    try {
      setIsExecuting(true);
      setError(null);
      setExecResult(null);

      let parsedArgs = {};
      try {
        parsedArgs = JSON.parse(execArgs);
      } catch {
        throw new Error("Invalid JSON arguments");
      }

      const res = await connectorService.executeOperation("github", selectedOp, parsedArgs);
      setExecResult(res);
    } catch (err) {
      console.error("[GitHubConnectorPage] Execute error:", err);
      setError(err.message || "Operation execution failed.");
    } finally {
      setIsExecuting(false);
    }
  };

  const isConnected = status?.status === "connected";

  return (
    <div className="space-y-8 max-w-6xl mx-auto pb-16">
      {/* Back link & Header */}
      <div>
        <Link
          href="/app/connectors"
          className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 transition-colors mb-4"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          Back to Connectors
        </Link>

        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
          <div className="flex items-center gap-3.5">
            <div className="w-12 h-12 rounded-2xl bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400 shadow-lg shadow-indigo-950/50">
              <FolderGit2 className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2.5">
                <h1 className="text-2xl font-bold text-slate-100 tracking-tight">GitHub Connector</h1>
                <Badge
                  variant="outline"
                  className="border-indigo-500/30 bg-indigo-950/40 text-indigo-300 text-[10px] font-mono"
                >
                  read-only
                </Badge>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Inspect public and private repositories, search issues, fetch code, and triage pull requests.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {isConnected ? (
              <span className="inline-flex items-center gap-1.5 text-xs font-medium text-emerald-400 bg-emerald-950/60 border border-emerald-800/40 px-3 py-1 rounded-full">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                Connected
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 text-xs text-slate-400 bg-slate-850 px-3 py-1 rounded-full">
                Disconnected
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Alerts */}
      {actionSuccess && (
        <div className="rounded-xl border border-emerald-500/30 bg-emerald-950/20 p-4 text-xs text-emerald-300 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>{actionSuccess}</span>
          </div>
          <button onClick={() => setActionSuccess(null)} className="text-emerald-400 hover:text-emerald-200">
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {error && (
        <div className="rounded-xl border border-red-500/30 bg-red-950/20 p-4 text-xs text-red-300 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
            <span>{error}</span>
          </div>
          <button onClick={() => setError(null)} className="text-red-400 hover:text-red-200">
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* Main Grid: Connection Manager + Account Details */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Connection Form / Status */}
        <div className="lg:col-span-2 space-y-6">
          <div className="rounded-xl border border-slate-800/90 bg-slate-900/60 backdrop-blur-sm p-6 space-y-5">
            <div className="flex items-center justify-between">
              <h2 className="font-semibold text-sm text-slate-100 flex items-center gap-2">
                <Key className="w-4 h-4 text-indigo-400" />
                <span>Authentication & Credentials</span>
              </h2>
              <span className="text-[10px] font-mono text-slate-400">AES-256-GCM Vault</span>
            </div>

            {isConnected ? (
              <div className="space-y-4">
                <div className="rounded-lg bg-slate-950/80 border border-slate-800 p-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      {status.account?.avatar_url ? (
                        <img
                          src={status.account.avatar_url}
                          alt="Avatar"
                          className="w-10 h-10 rounded-full border border-slate-700"
                        />
                      ) : (
                        <div className="w-10 h-10 rounded-full bg-indigo-600/30 flex items-center justify-center text-indigo-300 font-bold">
                          {status.account?.login ? status.account.login[0].toUpperCase() : "GH"}
                        </div>
                      )}
                      <div>
                        <div className="font-semibold text-sm text-slate-200">
                          {status.account?.name || status.account?.login || "Authenticated User"}
                        </div>
                        <div className="text-xs text-indigo-400 font-mono">@{status.account?.login}</div>
                      </div>
                    </div>

                    <Badge variant="outline" className="border-emerald-800/40 text-emerald-400 bg-emerald-950/50 text-xs">
                      Active
                    </Badge>
                  </div>

                  <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-850 text-xs text-slate-400">
                    <div>
                      Public Repos: <span className="text-slate-200 font-mono">{status.account?.public_repos ?? "N/A"}</span>
                    </div>
                    <div>
                      Credential Type: <span className="text-slate-200 font-mono uppercase">PAT</span>
                    </div>
                  </div>
                </div>

                <div className="flex flex-wrap items-center gap-3 pt-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={handleTestConnection}
                    disabled={isTesting}
                    className="border-slate-700 text-slate-300 hover:bg-slate-800 gap-1.5 text-xs"
                  >
                    <RefreshCw className={`w-3.5 h-3.5 ${isTesting ? "animate-spin" : ""}`} />
                    Test Connection
                  </Button>

                  <Button
                    size="sm"
                    variant="destructive"
                    onClick={handleDisconnect}
                    disabled={isDisconnecting}
                    className="bg-red-950/50 hover:bg-red-900/60 text-red-300 border border-red-800/40 gap-1.5 text-xs"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                    Disconnect & Purge Secrets
                  </Button>
                </div>
              </div>
            ) : (
              <form onSubmit={handleConnect} className="space-y-4">
                <p className="text-xs text-slate-400 leading-relaxed">
                  Provide a GitHub Personal Access Token (PAT) with <code className="text-indigo-300">repo</code> (or public repo) read scope.
                  Tokens are encrypted with AES-256-GCM before being stored in the database and are never logged or returned in responses.
                </p>

                <div className="space-y-3">
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">
                      GitHub Personal Access Token (PAT)
                    </label>
                    <input
                      type="password"
                      placeholder="ghp_xxxxxxxxxxxxxxxxxxxx or github_pat_xxxxxxxxxxxx"
                      value={tokenInput}
                      onChange={(e) => setTokenInput(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-100 placeholder-slate-600 focus:outline-none focus:border-indigo-500 font-mono"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">
                      Label / Description (Optional)
                    </label>
                    <input
                      type="text"
                      placeholder="e.g. Work GitHub Account"
                      value={accountLabel}
                      onChange={(e) => setAccountLabel(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-100 placeholder-slate-600 focus:outline-none focus:border-indigo-500"
                    />
                  </div>
                </div>

                <div className="pt-2">
                  <Button
                    type="submit"
                    disabled={isConnecting || !tokenInput.trim()}
                    className="bg-indigo-600 hover:bg-indigo-500 text-white gap-1.5 text-xs w-full sm:w-auto"
                  >
                    <ShieldCheck className="w-3.5 h-3.5" />
                    {isConnecting ? "Validating & Encrypting..." : "Connect GitHub"}
                  </Button>
                </div>
              </form>
            )}
          </div>

          {/* Granular Operation Permissions Table */}
          <div className="rounded-xl border border-slate-800/90 bg-slate-900/60 backdrop-blur-sm p-6 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="font-semibold text-sm text-slate-100 flex items-center gap-2">
                  <Sliders className="w-4 h-4 text-indigo-400" />
                  <span>Operation Permissions & Scopes</span>
                </h2>
                <p className="text-xs text-slate-400 mt-0.5">
                  Enable or disable individual connector operations for this workspace.
                </p>
              </div>
              <Badge variant="outline" className="border-slate-800 text-slate-400 text-[10px] font-mono">
                {operations.length} operations
              </Badge>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400 font-mono text-[10px] uppercase">
                    <th className="py-2.5 px-3">Operation</th>
                    <th className="py-2.5 px-3">Description</th>
                    <th className="py-2.5 px-3">Level</th>
                    <th className="py-2.5 px-3 text-right">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-850">
                  {operations.map((op) => {
                    const perm = permissions.find((p) => p.operation === op.name);
                    const isEnabled = perm ? perm.enabled : true;

                    return (
                      <tr key={op.name} className="hover:bg-slate-850/40 transition-colors">
                        <td className="py-2.5 px-3">
                          <span className="font-mono text-indigo-300 font-medium">{op.name}</span>
                        </td>
                        <td className="py-2.5 px-3 text-slate-400 max-w-xs truncate">{op.description}</td>
                        <td className="py-2.5 px-3">
                          <span className="inline-block text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 uppercase">
                            {op.permission_level}
                          </span>
                        </td>
                        <td className="py-2.5 px-3 text-right">
                          <button
                            onClick={() => handleTogglePermission(op.name, isEnabled)}
                            className={`px-2.5 py-1 rounded-md text-[11px] font-medium transition-colors ${
                              isEnabled
                                ? "bg-emerald-950/60 text-emerald-300 border border-emerald-800/40 hover:bg-emerald-900/50"
                                : "bg-slate-800 text-slate-400 border border-slate-700 hover:bg-slate-750"
                            }`}
                          >
                            {isEnabled ? "Enabled" : "Disabled"}
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Right Column: Security Boundary & Quick Tester */}
        <div className="space-y-6">
          {/* Security Boundary Card */}
          <div className="rounded-xl border border-indigo-500/20 bg-gradient-to-b from-indigo-950/30 to-slate-900/60 p-5 space-y-3.5 text-xs text-slate-300">
            <div className="flex items-center gap-2 font-semibold text-indigo-200">
              <ShieldCheck className="w-4 h-4 text-indigo-400" />
              <span>Prompt Injection Isolation</span>
            </div>
            <p className="text-slate-400 leading-relaxed text-[11px]">
              Every response fetched through the GitHub Connector is wrapped with:
            </p>
            <div className="p-2.5 rounded bg-slate-950/90 border border-indigo-900/40 font-mono text-[10px] text-indigo-300 space-y-1">
              <div>trust_level: &quot;external_untrusted&quot;</div>
              <div>source_type: &quot;connector&quot;</div>
              <div>source_name: &quot;github&quot;</div>
            </div>
            <p className="text-slate-400 text-[11px] leading-relaxed">
              External issue comments, README files, and PR bodies are never treated as trusted prompt instructions.
            </p>
          </div>

          {/* Live Operation Tester */}
          <div className="rounded-xl border border-slate-800/90 bg-slate-900/60 backdrop-blur-sm p-5 space-y-4">
            <h3 className="font-semibold text-xs text-slate-200 flex items-center gap-2">
              <Code2 className="w-4 h-4 text-indigo-400" />
              <span>Connector Live Tester</span>
            </h3>

            <div className="space-y-3">
              <div>
                <label className="block text-[11px] font-medium text-slate-400 mb-1">Select Operation</label>
                <select
                  value={selectedOp}
                  onChange={(e) => setSelectedOp(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500 font-mono"
                >
                  {operations.map((op) => (
                    <option key={op.name} value={op.name}>
                      {op.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-[11px] font-medium text-slate-400 mb-1">Arguments (JSON)</label>
                <textarea
                  rows={4}
                  value={execArgs}
                  onChange={(e) => setExecArgs(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-xs text-slate-200 font-mono focus:outline-none focus:border-indigo-500"
                />
              </div>

              <Button
                size="sm"
                onClick={handleExecuteOperation}
                disabled={isExecuting || !isConnected}
                className="w-full bg-indigo-600 hover:bg-indigo-500 text-white gap-1.5 text-xs"
              >
                <Play className="w-3.5 h-3.5" />
                {isExecuting ? "Executing..." : "Execute Read Operation"}
              </Button>

              {!isConnected && (
                <p className="text-[11px] text-amber-400/80 text-center">
                  Connect GitHub above to run live queries.
                </p>
              )}

              {execResult && (
                <div className="mt-3 space-y-2">
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="text-slate-400">Result:</span>
                    <span
                      className={`font-mono ${
                        execResult.success ? "text-emerald-400" : "text-red-400"
                      }`}
                    >
                      {execResult.success ? "200 OK" : execResult.error_code}
                    </span>
                  </div>
                  <pre className="p-2.5 rounded bg-slate-950 border border-slate-800 text-[10px] font-mono text-slate-300 max-h-48 overflow-y-auto">
                    {JSON.stringify(execResult, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
