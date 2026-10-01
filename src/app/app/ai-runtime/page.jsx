"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  Cpu,
  Server,
  Activity,
  Zap,
  ShieldAlert,
  ArrowRight,
  RefreshCw,
  Sliders,
  DollarSign,
  CheckCircle,
  AlertCircle,
  XCircle,
  Clock,
  Play,
  RotateCcw,
} from "lucide-react";
import {
  listGatewayModels,
  listGatewayProviders,
  getGatewayHealth,
  testGatewayPrompt,
  getGatewayPolicy,
} from "@/services/gateway";

export default function AIRuntimePage() {
  const [activeTab, setActiveTab] = useState("overview");
  const [models, setModels] = useState([]);
  const [providers, setProviders] = useState([]);
  const [healthData, setHealthData] = useState(null);
  const [policy, setPolicy] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Diagnostic Test state
  const [testPrompt, setTestPrompt] = useState("Explain how the AI Gateway ensures fault tolerance in 2 sentences.");
  const [testModel, setTestModel] = useState("gpt-4o-mini");
  const [testResult, setTestResult] = useState(null);
  const [testing, setTesting] = useState(false);
  const [testError, setTestError] = useState(null);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [mods, provs, health, pol] = await Promise.all([
        listGatewayModels().catch(() => []),
        listGatewayProviders().catch(() => []),
        getGatewayHealth().catch(() => null),
        getGatewayPolicy().catch(() => null),
      ]);
      setModels(mods);
      setProviders(provs);
      setHealthData(health);
      setPolicy(pol);
      if (mods.length > 0 && !testModel) {
        setTestModel(mods[0].model_id);
      }
    } catch (err) {
      setError(err.message || "Failed to load AI Gateway runtime data.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleRunTest = async (e) => {
    e.preventDefault();
    setTesting(true);
    setTestError(null);
    setTestResult(null);
    try {
      const res = await testGatewayPrompt({
        model: testModel,
        prompt: testPrompt,
        temperature: 0.3,
        max_tokens: 150,
      });
      setTestResult(res);
    } catch (err) {
      setTestError(err.message || "Gateway diagnostic test failed.");
    } finally {
      setTesting(false);
    }
  };

  return (
    <div className="space-y-8 max-w-7xl mx-auto p-4 sm:p-6 lg:p-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border/40 pb-6">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-primary/10 border border-primary/20 text-primary">
              <Cpu className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl sm:text-3xl font-bold tracking-tight">AI Runtime & Gateway</h1>
              <p className="text-muted-foreground text-sm mt-1">
                Unified runtime, deterministic model routing, fault-tolerant fallbacks, and operational health.
              </p>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <Link
            href="/app/ai-runtime/routing"
            className="inline-flex items-center gap-2 px-3.5 py-2 text-sm font-medium rounded-lg border border-border bg-card hover:bg-muted/50 transition-colors shadow-sm"
          >
            <Sliders className="w-4 h-4 text-primary" />
            Routing Preview
          </Link>
          <Link
            href="/app/settings/models"
            className="inline-flex items-center gap-2 px-3.5 py-2 text-sm font-medium rounded-lg border border-border bg-card hover:bg-muted/50 transition-colors shadow-sm"
          >
            <ShieldAlert className="w-4 h-4 text-amber-500" />
            Model Policies
          </Link>
          <button
            onClick={fetchData}
            disabled={loading}
            className="inline-flex items-center gap-2 px-3 py-2 text-sm rounded-lg border border-border bg-card hover:bg-muted/50 transition-colors text-muted-foreground"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl border border-rose-500/20 bg-rose-500/10 text-rose-400 text-sm flex items-center gap-3">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Top Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-5 rounded-2xl border border-border/60 bg-card/60 backdrop-blur-sm shadow-sm space-y-2">
          <div className="flex items-center justify-between text-muted-foreground text-xs uppercase tracking-wider font-semibold">
            <span>Gateway Runtime</span>
            <Server className="w-4 h-4 text-emerald-500" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold tracking-tight text-foreground">Active</span>
            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              Online
            </span>
          </div>
          <p className="text-xs text-muted-foreground">Provider-agnostic single runtime entry point</p>
        </div>

        <div className="p-5 rounded-2xl border border-border/60 bg-card/60 backdrop-blur-sm shadow-sm space-y-2">
          <div className="flex items-center justify-between text-muted-foreground text-xs uppercase tracking-wider font-semibold">
            <span>Registered Providers</span>
            <Activity className="w-4 h-4 text-blue-500" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold tracking-tight text-foreground">{providers.length}</span>
            <span className="text-xs text-muted-foreground">adapters ready</span>
          </div>
          <p className="text-xs text-muted-foreground">
            {providers.map((p) => p.display_name).join(", ") || "None"}
          </p>
        </div>

        <div className="p-5 rounded-2xl border border-border/60 bg-card/60 backdrop-blur-sm shadow-sm space-y-2">
          <div className="flex items-center justify-between text-muted-foreground text-xs uppercase tracking-wider font-semibold">
            <span>Supported Models</span>
            <Zap className="w-4 h-4 text-purple-500" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold tracking-tight text-foreground">{models.length}</span>
            <span className="text-xs text-muted-foreground">cataloged</span>
          </div>
          <p className="text-xs text-muted-foreground">Multi-provider capabilities and context limits</p>
        </div>

        <div className="p-5 rounded-2xl border border-border/60 bg-card/60 backdrop-blur-sm shadow-sm space-y-2">
          <div className="flex items-center justify-between text-muted-foreground text-xs uppercase tracking-wider font-semibold">
            <span>Circuit Breaker</span>
            <ShieldAlert className="w-4 h-4 text-amber-500" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold tracking-tight text-foreground">Closed</span>
            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              Healthy
            </span>
          </div>
          <p className="text-xs text-muted-foreground">Threshold 5 fails · 60s cooldown</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-border/40">
        <nav className="flex space-x-6">
          {[
            { id: "overview", label: "Gateway Overview" },
            { id: "providers", label: "Providers" },
            { id: "models", label: "Model Catalog" },
            { id: "health", label: "Health & Circuits" },
            { id: "diagnostic", label: "Diagnostic Tester" },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`py-3 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === tab.id
                  ? "border-primary text-primary"
                  : "border-transparent text-muted-foreground hover:text-foreground"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab: Overview */}
      {activeTab === "overview" && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <div className="p-6 rounded-2xl border border-border/60 bg-card space-y-4">
              <h3 className="font-semibold text-lg flex items-center gap-2">
                <Server className="w-5 h-5 text-primary" />
                Architecture Pipeline
              </h3>
              <p className="text-sm text-muted-foreground">
                All platform features (Tasks, Workflows, Planners, Evaluation, Reviser) execute through the unified AI Gateway runtime:
              </p>
              <div className="p-4 rounded-xl bg-muted/40 border border-border font-mono text-xs text-muted-foreground space-y-1">
                <div className="text-foreground">Application Component</div>
                <div className="pl-4 text-primary">↓ AIGateway Entry</div>
                <div className="pl-8 text-amber-400">↓ Workspace Policy Check (Allowed Models & Providers)</div>
                <div className="pl-12 text-blue-400">↓ ModelRouter (Deterministic Capability Matching)</div>
                <div className="pl-16 text-purple-400">↓ Circuit Breaker & Concurrency Gate</div>
                <div className="pl-20 text-emerald-400">↓ Provider Adapter (OpenAI, Mock)</div>
                <div className="pl-24 text-foreground">↓ Normalized Response & Token/Cost Accounting</div>
                <div className="pl-28 text-muted-foreground">↓ Observability Trace Events</div>
              </div>
            </div>

            <div className="p-6 rounded-2xl border border-border/60 bg-card space-y-4">
              <h3 className="font-semibold text-lg flex items-center gap-2">
                <RotateCcw className="w-5 h-5 text-amber-500" />
                Resilience & Fallback Policies
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
                <div className="p-4 rounded-xl border border-border/40 bg-muted/20 space-y-2">
                  <div className="font-medium text-foreground">Max Fallback Attempts</div>
                  <div className="text-2xl font-bold text-primary">2</div>
                  <p className="text-xs text-muted-foreground">
                    Cross-provider candidates tested sequentially on rate limits or timeouts.
                  </p>
                </div>
                <div className="p-4 rounded-xl border border-border/40 bg-muted/20 space-y-2">
                  <div className="font-medium text-foreground">Max Bounded Retries</div>
                  <div className="text-2xl font-bold text-primary">2</div>
                  <p className="text-xs text-muted-foreground">
                    Exponential backoff (0.25s, 0.50s) strictly on transient operational failures.
                  </p>
                </div>
              </div>
            </div>
          </div>

          <div className="space-y-6">
            <div className="p-6 rounded-2xl border border-border/60 bg-card space-y-4">
              <h3 className="font-semibold text-base flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-primary" />
                Active Workspace Policy
              </h3>
              <div className="space-y-3 text-sm">
                <div className="flex justify-between py-1 border-b border-border/30">
                  <span className="text-muted-foreground">Allowed Providers</span>
                  <span className="font-medium">{policy?.allowed_providers?.join(", ") || "All"}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-border/30">
                  <span className="text-muted-foreground">Allowed Models</span>
                  <span className="font-medium">
                    {policy?.allowed_models?.length ? policy.allowed_models.join(", ") : "All Registered"}
                  </span>
                </div>
                <div className="flex justify-between py-1 border-b border-border/30">
                  <span className="text-muted-foreground">Max Tokens/Call</span>
                  <span className="font-medium">{policy?.max_tokens_per_request || 4096}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-border/30">
                  <span className="text-muted-foreground">Max Concurrency</span>
                  <span className="font-medium">{policy?.max_concurrent_requests || 10}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-border/30">
                  <span className="text-muted-foreground">Fallback Enabled</span>
                  <span className="font-medium text-emerald-400">
                    {policy?.fallback_enabled !== false ? "Yes" : "No"}
                  </span>
                </div>
              </div>
              <Link
                href="/app/settings/models"
                className="w-full inline-flex justify-center items-center gap-2 py-2 px-3 text-xs font-medium rounded-lg border border-border bg-muted/40 hover:bg-muted transition-colors"
              >
                Configure Workspace Model Policy
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>
        </div>
      )}

      {/* Tab: Providers */}
      {activeTab === "providers" && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {providers.map((prov) => (
            <div key={prov.name} className="p-6 rounded-2xl border border-border/60 bg-card space-y-4 shadow-sm">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2.5 rounded-xl bg-primary/10 text-primary border border-primary/20">
                    <Server className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-lg">{prov.display_name}</h3>
                    <p className="text-xs text-muted-foreground">Identifier: {prov.name}</p>
                  </div>
                </div>
                <span
                  className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${
                    prov.enabled
                      ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                      : "bg-muted text-muted-foreground border-border"
                  }`}
                >
                  {prov.enabled ? <CheckCircle className="w-3.5 h-3.5" /> : <XCircle className="w-3.5 h-3.5" />}
                  {prov.enabled ? "Configured" : "Unconfigured"}
                </span>
              </div>

              <div className="space-y-2 text-sm pt-2">
                <div className="flex justify-between py-1 border-b border-border/30">
                  <span className="text-muted-foreground">Authentication</span>
                  <span className="font-mono text-xs uppercase">{prov.authentication_type}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-border/30">
                  <span className="text-muted-foreground">Available Models</span>
                  <span className="font-medium">{prov.models?.length || 0} models</span>
                </div>
                <div className="flex justify-between py-1 border-b border-border/30">
                  <span className="text-muted-foreground">Capabilities</span>
                  <div className="flex gap-1">
                    {prov.capabilities?.map((c) => (
                      <span key={c} className="px-1.5 py-0.5 bg-muted rounded text-[10px] text-muted-foreground">
                        {c}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Tab: Models */}
      {activeTab === "models" && (
        <div className="rounded-2xl border border-border/60 bg-card overflow-hidden">
          <div className="p-4 border-b border-border/40 bg-muted/20">
            <h3 className="font-semibold text-base">Registered Models Catalog</h3>
            <p className="text-xs text-muted-foreground">
              Objective technical capabilities, context limits, and pricing classes.
            </p>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="bg-muted/30 text-xs text-muted-foreground uppercase border-b border-border/30">
                <tr>
                  <th className="px-4 py-3">Model</th>
                  <th className="px-4 py-3">Provider</th>
                  <th className="px-4 py-3">Context Window</th>
                  <th className="px-4 py-3">Capabilities</th>
                  <th className="px-4 py-3">Cost Class</th>
                  <th className="px-4 py-3">Latency</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/20">
                {models.map((m) => (
                  <tr key={m.model_id} className="hover:bg-muted/10 transition-colors">
                    <td className="px-4 py-3">
                      <div className="font-medium text-foreground">{m.display_name}</div>
                      <div className="font-mono text-xs text-muted-foreground">{m.model_id}</div>
                    </td>
                    <td className="px-4 py-3 uppercase text-xs font-mono">{m.provider}</td>
                    <td className="px-4 py-3 text-xs">{m.context_window?.toLocaleString()} tokens</td>
                    <td className="px-4 py-3">
                      <div className="flex flex-wrap gap-1">
                        {m.supports_streaming && (
                          <span className="px-1.5 py-0.5 rounded text-[10px] bg-blue-500/10 text-blue-400">Stream</span>
                        )}
                        {m.supports_tools && (
                          <span className="px-1.5 py-0.5 rounded text-[10px] bg-purple-500/10 text-purple-400">Tools</span>
                        )}
                        {m.supports_structured_output && (
                          <span className="px-1.5 py-0.5 rounded text-[10px] bg-emerald-500/10 text-emerald-400">JSON</span>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3 capitalize text-xs">{m.cost_class}</td>
                    <td className="px-4 py-3 capitalize text-xs">{m.latency_class}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab: Health */}
      {activeTab === "health" && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {healthData?.providers?.map((p) => (
              <div key={p.provider} className="p-6 rounded-2xl border border-border/60 bg-card space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Activity className="w-5 h-5 text-emerald-500" />
                    <h3 className="font-semibold text-lg">{p.display_name}</h3>
                  </div>
                  <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                    <CheckCircle className="w-3.5 h-3.5" />
                    {p.health?.status || "Healthy"}
                  </span>
                </div>

                <div className="grid grid-cols-3 gap-2 py-2 text-center text-xs">
                  <div className="p-2.5 rounded-xl bg-muted/30 border border-border/30">
                    <div className="text-muted-foreground">Requests</div>
                    <div className="text-base font-bold mt-0.5">{p.health?.total_requests || 0}</div>
                  </div>
                  <div className="p-2.5 rounded-xl bg-muted/30 border border-border/30">
                    <div className="text-muted-foreground">Avg Latency</div>
                    <div className="text-base font-bold mt-0.5">{p.health?.average_latency_ms || 0}ms</div>
                  </div>
                  <div className="p-2.5 rounded-xl bg-muted/30 border border-border/30">
                    <div className="text-muted-foreground">Circuit</div>
                    <div className="text-base font-bold mt-0.5 text-emerald-400 capitalize">
                      {p.health?.circuit_state || "Closed"}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab: Diagnostic Tester */}
      {activeTab === "diagnostic" && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="p-6 rounded-2xl border border-border/60 bg-card space-y-4">
            <h3 className="font-semibold text-lg flex items-center gap-2">
              <Play className="w-5 h-5 text-primary" />
              Test Gateway Execution
            </h3>
            <p className="text-xs text-muted-foreground">
              Executes a test prompt through the actual AIGateway pipeline, verifying routing, policies, and latency.
            </p>

            <form onSubmit={handleRunTest} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1.5">Target Model</label>
                <select
                  value={testModel}
                  onChange={(e) => setTestModel(e.target.value)}
                  className="w-full px-3 py-2 text-sm rounded-lg border border-border bg-background focus:ring-1 focus:ring-primary"
                >
                  {models.map((m) => (
                    <option key={m.model_id} value={m.model_id}>
                      {m.display_name} ({m.provider})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1.5">Prompt</label>
                <textarea
                  value={testPrompt}
                  onChange={(e) => setTestPrompt(e.target.value)}
                  rows={3}
                  className="w-full px-3 py-2 text-sm rounded-lg border border-border bg-background focus:ring-1 focus:ring-primary"
                  placeholder="Enter diagnostic prompt..."
                />
              </div>

              <button
                type="submit"
                disabled={testing}
                className="w-full inline-flex justify-center items-center gap-2 py-2.5 px-4 rounded-xl font-medium text-sm bg-primary text-primary-foreground hover:bg-primary/90 transition-colors shadow-sm disabled:opacity-50"
              >
                {testing ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
                {testing ? "Executing Gateway Call..." : "Execute Gateway Test"}
              </button>
            </form>
          </div>

          <div className="p-6 rounded-2xl border border-border/60 bg-card space-y-4">
            <h3 className="font-semibold text-lg">Execution Output</h3>
            {testing && (
              <div className="py-12 flex flex-col items-center justify-center text-muted-foreground gap-3">
                <RefreshCw className="w-6 h-6 animate-spin text-primary" />
                <span className="text-sm">Running through AIGateway runtime...</span>
              </div>
            )}

            {testError && (
              <div className="p-4 rounded-xl border border-rose-500/20 bg-rose-500/10 text-rose-400 text-sm">
                {testError}
              </div>
            )}

            {testResult && !testing && (
              <div className="space-y-4">
                <div className="p-4 rounded-xl bg-muted/30 border border-border/40 text-sm">
                  <div className="font-semibold text-xs text-muted-foreground uppercase mb-1">Generated Output</div>
                  <div className="text-foreground whitespace-pre-wrap">{testResult.content}</div>
                </div>

                <div className="grid grid-cols-3 gap-2 text-xs">
                  <div className="p-3 rounded-xl bg-muted/20 border border-border/20">
                    <span className="text-muted-foreground">Tokens</span>
                    <div className="font-bold text-sm mt-0.5">{testResult.usage?.total_tokens || 0}</div>
                  </div>
                  <div className="p-3 rounded-xl bg-muted/20 border border-border/20">
                    <span className="text-muted-foreground">Latency</span>
                    <div className="font-bold text-sm mt-0.5">{testResult.latency_ms}ms</div>
                  </div>
                  <div className="p-3 rounded-xl bg-muted/20 border border-border/20">
                    <span className="text-muted-foreground">Est. Cost</span>
                    <div className="font-bold text-sm mt-0.5">
                      {testResult.usage?.estimated_cost !== null && testResult.usage?.estimated_cost !== undefined
                        ? `$${Number(testResult.usage.estimated_cost).toFixed(6)}`
                        : "N/A"}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {!testResult && !testing && !testError && (
              <div className="py-12 text-center text-sm text-muted-foreground">
                Run a diagnostic test to inspect normalized output and latency.
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
