"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  ShieldAlert,
  Save,
  RefreshCw,
  CheckCircle,
  AlertCircle,
  Cpu,
  Layers,
} from "lucide-react";
import {
  getGatewayPolicy,
  updateGatewayPolicy,
  listGatewayProviders,
  listGatewayModels,
} from "@/services/gateway";

export default function WorkspaceModelSettingsPage() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  const [providers, setProviders] = useState([]);
  const [models, setModels] = useState([]);

  // Policy Form State
  const [allowedProviders, setAllowedProviders] = useState(["openai", "mock"]);
  const [allowedModels, setAllowedModels] = useState([]);
  const [defaultModel, setDefaultModel] = useState("");
  const [maxTokens, setMaxTokens] = useState(4096);
  const [maxRequestsPerRun, setMaxRequestsPerRun] = useState(50);
  const [maxConcurrent, setMaxConcurrent] = useState(10);
  const [fallbackEnabled, setFallbackEnabled] = useState(true);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [pol, provs, mods] = await Promise.all([
        getGatewayPolicy(),
        listGatewayProviders().catch(() => []),
        listGatewayModels().catch(() => []),
      ]);
      setProviders(provs);
      setModels(mods);

      if (pol) {
        setAllowedProviders(pol.allowed_providers || ["openai", "mock"]);
        setAllowedModels(pol.allowed_models || []);
        setDefaultModel(pol.default_model || "");
        setMaxTokens(pol.max_tokens_per_request || 4096);
        setMaxRequestsPerRun(pol.max_requests_per_run || 50);
        setMaxConcurrent(pol.max_concurrent_requests || 10);
        setFallbackEnabled(pol.fallback_enabled !== false);
      }
    } catch (err) {
      setError(err.message || "Failed to load workspace model settings.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleProviderToggle = (pName) => {
    if (allowedProviders.includes(pName)) {
      if (allowedProviders.length === 1) {
        setError("At least one provider must remain allowed.");
        return;
      }
      setAllowedProviders(allowedProviders.filter((p) => p !== pName));
    } else {
      setAllowedProviders([...allowedProviders, pName]);
    }
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    setSuccess(null);
    try {
      await updateGatewayPolicy({
        allowed_providers: allowedProviders,
        allowed_models: allowedModels,
        default_model: defaultModel || null,
        max_tokens_per_request: parseInt(maxTokens, 10),
        max_requests_per_run: parseInt(maxRequestsPerRun, 10),
        max_concurrent_requests: parseInt(maxConcurrent, 10),
        fallback_enabled: fallbackEnabled,
      });
      setSuccess("Workspace model policy updated successfully.");
    } catch (err) {
      setError(err.message || "Failed to update workspace model policy.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-8 max-w-4xl mx-auto p-4 sm:p-6 lg:p-8">
      {/* Header */}
      <div className="border-b border-border/40 pb-6">
        <Link
          href="/app/ai-runtime"
          className="inline-flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground mb-2 transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          Back to AI Runtime
        </Link>
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-500">
            <ShieldAlert className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight">Workspace Model Settings</h1>
            <p className="text-muted-foreground text-sm mt-1">
              Configure allowed providers, model whitelists, token limits, and concurrency boundaries.
            </p>
          </div>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl border border-rose-500/20 bg-rose-500/10 text-rose-400 text-sm flex items-center gap-3">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {success && (
        <div className="p-4 rounded-xl border border-emerald-500/20 bg-emerald-500/10 text-emerald-400 text-sm flex items-center gap-3">
          <CheckCircle className="w-5 h-5 flex-shrink-0" />
          <span>{success}</span>
        </div>
      )}

      {loading ? (
        <div className="py-12 flex items-center justify-center text-muted-foreground gap-3">
          <RefreshCw className="w-6 h-6 animate-spin text-primary" />
          <span>Loading workspace model policy...</span>
        </div>
      ) : (
        <form onSubmit={handleSave} className="space-y-8">
          {/* Section 1: Allowed Providers */}
          <div className="p-6 rounded-2xl border border-border/60 bg-card space-y-4 shadow-sm">
            <h2 className="font-semibold text-base flex items-center gap-2">
              <Layers className="w-4 h-4 text-primary" />
              Allowed Providers
            </h2>
            <p className="text-xs text-muted-foreground">
              Select which model providers can be invoked by workflows and tasks in this workspace.
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
              {providers.map((p) => {
                const checked = allowedProviders.includes(p.name);
                return (
                  <label
                    key={p.name}
                    className={`flex items-center justify-between p-3.5 rounded-xl border cursor-pointer transition-colors ${
                      checked
                        ? "border-primary/50 bg-primary/5"
                        : "border-border/60 bg-muted/20 hover:bg-muted/30"
                    }`}
                  >
                    <div>
                      <div className="font-medium text-sm text-foreground">{p.display_name}</div>
                      <div className="text-xs text-muted-foreground font-mono">{p.name}</div>
                    </div>
                    <input
                      type="checkbox"
                      checked={checked}
                      onChange={() => handleProviderToggle(p.name)}
                      className="rounded border-border text-primary focus:ring-primary h-4 w-4"
                    />
                  </label>
                );
              })}
            </div>
          </div>

          {/* Section 2: Token and Concurrency Boundaries */}
          <div className="p-6 rounded-2xl border border-border/60 bg-card space-y-4 shadow-sm">
            <h2 className="font-semibold text-base flex items-center gap-2">
              <Cpu className="w-4 h-4 text-primary" />
              Execution & Concurrency Boundaries
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2">
              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                  Max Tokens per Call
                </label>
                <input
                  type="number"
                  min="256"
                  max="32768"
                  value={maxTokens}
                  onChange={(e) => setMaxTokens(e.target.value)}
                  className="w-full px-3 py-2 text-sm rounded-lg border border-border bg-background focus:ring-1 focus:ring-primary"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                  Max Calls per Run
                </label>
                <input
                  type="number"
                  min="5"
                  max="200"
                  value={maxRequestsPerRun}
                  onChange={(e) => setMaxRequestsPerRun(e.target.value)}
                  className="w-full px-3 py-2 text-sm rounded-lg border border-border bg-background focus:ring-1 focus:ring-primary"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                  Max Concurrent Calls
                </label>
                <input
                  type="number"
                  min="1"
                  max="50"
                  value={maxConcurrent}
                  onChange={(e) => setMaxConcurrent(e.target.value)}
                  className="w-full px-3 py-2 text-sm rounded-lg border border-border bg-background focus:ring-1 focus:ring-primary"
                />
              </div>
            </div>

            <div className="pt-4 border-t border-border/40">
              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={fallbackEnabled}
                  onChange={(e) => setFallbackEnabled(e.target.checked)}
                  className="rounded border-border text-primary focus:ring-primary h-4 w-4"
                />
                <div>
                  <div className="font-medium text-sm text-foreground">Enable Model Fallbacks</div>
                  <p className="text-xs text-muted-foreground">
                    Automatically try compatible alternative models if the primary model hits a transient rate limit or timeout.
                  </p>
                </div>
              </label>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex justify-end gap-3 pt-4">
            <button
              type="submit"
              disabled={saving}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl font-medium text-sm bg-primary text-primary-foreground hover:bg-primary/90 transition-colors shadow-sm disabled:opacity-50"
            >
              {saving ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
              {saving ? "Saving Policy..." : "Save Model Policy"}
            </button>
          </div>
        </form>
      )}
    </div>
  );
}
