"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  BookOpen,
  ArrowLeft,
  Key,
  Shield,
  Layers,
  Webhook,
  Zap,
  Terminal,
  Code2,
  Copy,
  Check,
  Download,
  AlertCircle,
  ExternalLink,
  ShieldCheck,
} from "lucide-react";
import { developerService } from "@/services/developer";

const DOC_SECTIONS = [
  { id: "overview", label: "Overview & Architecture", icon: Layers },
  { id: "auth", label: "Authentication & Keys", icon: Key },
  { id: "scopes", label: "Scopes & Hierarchy", icon: Shield },
  { id: "endpoints", label: "Endpoints (/api/v1)", icon: Terminal },
  { id: "streaming", label: "Streaming (SSE)", icon: Zap },
  { id: "idempotency", label: "Idempotency", icon: Layers },
  { id: "webhooks", label: "Webhooks & Signatures", icon: Webhook },
  { id: "sdks", label: "Official SDKs", icon: Code2 },
  { id: "openapi", label: "OpenAPI Specification", icon: Download },
];

export default function DeveloperDocsPage() {
  const [activeSection, setActiveSection] = useState("overview");
  const [openApiSpec, setOpenApiSpec] = useState(null);
  const [copiedKey, setCopiedKey] = useState(null);

  useEffect(() => {
    async function loadSpec() {
      try {
        const spec = await developerService.getPublicOpenApiSpec();
        setOpenApiSpec(spec);
      } catch (err) {
        console.error("Failed to load OpenAPI spec", err);
      }
    }
    loadSpec();
  }, []);

  function handleCopy(text, key) {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  }

  function downloadOpenApiJson() {
    if (!openApiSpec) return;
    const blob = new Blob([JSON.stringify(openApiSpec, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "public-openapi.json";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

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
        <Link href="/app/developer/api-explorer" className="text-blue-400 hover:underline shrink-0 ml-4 font-medium flex items-center gap-1">
          <Terminal className="w-3.5 h-3.5" />
          API Explorer
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
            <span className="text-slate-200">Documentation</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <BookOpen className="w-6 h-6 text-indigo-400" />
            Developer Platform & Public API Reference
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Complete technical guide to authenticating, running tasks, executing workflows, verifying webhooks, and integrating with official SDKs.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={downloadOpenApiJson}
            disabled={!openApiSpec}
            className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-slate-200 rounded-lg text-xs font-medium border border-slate-700 flex items-center gap-1.5 transition"
          >
            <Download className="w-3.5 h-3.5 text-indigo-400" />
            Download OpenAPI JSON
          </button>
        </div>
      </div>

      {/* Content Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Navigation Sidebar */}
        <div className="lg:col-span-1 space-y-1">
          <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider px-3 mb-2">
            Table of Contents
          </div>
          {DOC_SECTIONS.map((sec) => {
            const Icon = sec.icon;
            const isActive = activeSection === sec.id;
            return (
              <button
                key={sec.id}
                onClick={() => setActiveSection(sec.id)}
                className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium transition text-left ${
                  isActive
                    ? "bg-indigo-600 text-white font-semibold shadow-sm shadow-indigo-600/30"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
                }`}
              >
                <Icon className={`w-4 h-4 shrink-0 ${isActive ? "text-white" : "text-slate-400"}`} />
                {sec.label}
              </button>
            );
          })}
        </div>

        {/* Section Content */}
        <div className="lg:col-span-3 bg-slate-900/60 border border-slate-800 rounded-xl p-6 text-sm text-slate-300 space-y-6">
          {activeSection === "overview" && (
            <div className="space-y-4">
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <Layers className="w-5 h-5 text-indigo-400" />
                Architecture & Security Boundaries
              </h2>
              <p>
                The Public API acts as a secure, authenticated, and governed adapter over the AI Work Layer platform. It allows external applications to consume AI capabilities programmatically while preserving strict enterprise boundaries:
              </p>
              <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 font-mono text-xs text-slate-300 overflow-x-auto leading-relaxed">
{`External Application
       ↓ (HTTPS + Scoped Bearer Key)
Public API Gateway (/api/v1)
       ↓
API Authentication (SHA-256 Key Lookup)
       ↓
API Authorization (Centralized Step 27 RBAC)
       ↓
Governance Engine (Step 32 Policy Evaluation)
       ↓
Rate & Quota Control (Step 35 Sliding Window)
       ↓
Existing Platform Services (Tasks, Workflows, Tools, Connectors)
       ↓
Events / SSE Streams / Signed Webhook Delivery`}
              </div>

              <h3 className="text-base font-semibold text-white pt-2">Core Guarantees</h3>
              <ul className="list-disc pl-5 space-y-1.5 text-xs text-slate-400">
                <li><strong className="text-slate-200">No Internal API Exposure:</strong> Untrusted clients only have access to versioned <code className="text-indigo-400">/api/v1/</code> routes.</li>
                <li><strong className="text-slate-200">Zero Secret Leakage:</strong> Provider API keys, database credentials, connector secrets, and internal policy rules are strictly masked.</li>
                <li><strong className="text-slate-200">Governance First:</strong> All operations pass through Step 32 Governance prior to execution.</li>
                <li><strong className="text-slate-200">End-to-End Correlation:</strong> Every request receives an <code className="text-indigo-400">X-Request-ID</code> header that propagates through all downstream subsystems.</li>
              </ul>
            </div>
          )}

          {activeSection === "auth" && (
            <div className="space-y-4">
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <Key className="w-5 h-5 text-indigo-400" />
                Authentication & API Keys
              </h2>
              <p>
                All Public API requests must supply a valid API key in the <code className="text-indigo-400">Authorization</code> HTTP header:
              </p>
              <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 font-mono text-xs text-indigo-300 flex items-center justify-between">
                <span>Authorization: Bearer awl_prod_abc123...</span>
                <button
                  onClick={() => handleCopy("Authorization: Bearer awl_prod_abc123...", "bearer_header")}
                  className="p-1 hover:bg-slate-800 rounded text-slate-400 hover:text-slate-200"
                >
                  {copiedKey === "bearer_header" ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                </button>
              </div>

              <h3 className="text-base font-semibold text-white pt-2">Environment Prefixes</h3>
              <p className="text-xs text-slate-400">
                Keys use cryptographically secure random bytes with explicit environment identifiers to prevent accidental cross-environment execution:
              </p>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
                <div className="p-3 bg-slate-950 rounded-lg border border-slate-800">
                  <div className="font-mono font-bold text-emerald-400">awl_dev_...</div>
                  <div className="text-slate-400 text-[11px] mt-1">Development only. Never runs against production assets.</div>
                </div>
                <div className="p-3 bg-slate-950 rounded-lg border border-slate-800">
                  <div className="font-mono font-bold text-amber-400">awl_stg_...</div>
                  <div className="text-slate-400 text-[11px] mt-1">Staging only. Pre-production testing environment.</div>
                </div>
                <div className="p-3 bg-slate-950 rounded-lg border border-slate-800">
                  <div className="font-mono font-bold text-sky-400">awl_prod_...</div>
                  <div className="text-slate-400 text-[11px] mt-1">Production only. Requires approval for sensitive scopes.</div>
                </div>
              </div>

              <h3 className="text-base font-semibold text-white pt-2">Zero-Downtime Rotation</h3>
              <p className="text-xs text-slate-400">
                You can rotate keys seamlessly without interrupting production traffic. When rotating a credential, both the old and new keys remain active concurrently during a grace period until you explicitly revoke the old key.
              </p>
            </div>
          )}

          {activeSection === "scopes" && (
            <div className="space-y-4">
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <Shield className="w-5 h-5 text-indigo-400" />
                Scopes & Resource Hierarchy
              </h2>
              <p>
                Every API credential has an immutable set of granted scopes and a strict resource boundary. Scopes follow the principle of least privilege and cannot exceed the creator&apos;s organizational permissions.
              </p>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                <div className="p-3 bg-slate-950 rounded-lg border border-slate-800">
                  <div className="font-semibold text-slate-200 mb-1">Execution Scopes</div>
                  <ul className="space-y-1 font-mono text-[11px] text-indigo-300">
                    <li>tasks:read, tasks:run</li>
                    <li>workflows:read, workflows:run</li>
                    <li>runs:read</li>
                  </ul>
                </div>
                <div className="p-3 bg-slate-950 rounded-lg border border-slate-800">
                  <div className="font-semibold text-slate-200 mb-1">Resource & Artifact Scopes</div>
                  <ul className="space-y-1 font-mono text-[11px] text-indigo-300">
                    <li>artifacts:read, artifacts:create</li>
                    <li>documents:read</li>
                    <li>memory:read, memory:write</li>
                    <li>knowledge:read</li>
                  </ul>
                </div>
                <div className="p-3 bg-slate-950 rounded-lg border border-slate-800">
                  <div className="font-semibold text-slate-200 mb-1">Discovery & Observability</div>
                  <ul className="space-y-1 font-mono text-[11px] text-indigo-300">
                    <li>models:read</li>
                    <li>connectors:read</li>
                    <li>events:read</li>
                    <li>usage:read</li>
                  </ul>
                </div>
                <div className="p-3 bg-slate-950 rounded-lg border border-slate-800">
                  <div className="font-semibold text-slate-200 mb-1">Management Scopes</div>
                  <ul className="space-y-1 font-mono text-[11px] text-indigo-300">
                    <li>webhooks:manage</li>
                    <li>applications:manage</li>
                  </ul>
                </div>
              </div>

              <h3 className="text-base font-semibold text-white pt-2">Resource Bounds</h3>
              <p className="text-xs text-slate-400">
                A key scoped to <code className="text-indigo-400">workspace = ws_123</code> can never read or trigger executions in any other workspace, even if the granted scope includes <code className="text-indigo-400">tasks:run</code>.
              </p>
            </div>
          )}

          {activeSection === "endpoints" && (
            <div className="space-y-4">
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <Terminal className="w-5 h-5 text-indigo-400" />
                Public Endpoints Reference
              </h2>
              <p>
                All Public API endpoints are versioned under <code className="text-indigo-400">/api/v1/</code>:
              </p>

              <div className="space-y-2 text-xs font-mono">
                <div className="p-2.5 bg-slate-950 rounded-lg border border-slate-800 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 text-[10px] font-bold border border-emerald-500/20">POST</span>
                    <span className="text-slate-200">/api/v1/tasks/&#123;task_id&#125;/runs</span>
                  </div>
                  <span className="text-slate-500 text-[11px]">Execute task</span>
                </div>

                <div className="p-2.5 bg-slate-950 rounded-lg border border-slate-800 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="px-1.5 py-0.5 rounded bg-sky-500/10 text-sky-400 text-[10px] font-bold border border-sky-500/20">GET</span>
                    <span className="text-slate-200">/api/v1/runs/&#123;run_id&#125;</span>
                  </div>
                  <span className="text-slate-500 text-[11px]">Get execution status</span>
                </div>

                <div className="p-2.5 bg-slate-950 rounded-lg border border-slate-800 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="px-1.5 py-0.5 rounded bg-sky-500/10 text-sky-400 text-[10px] font-bold border border-sky-500/20">GET</span>
                    <span className="text-slate-200">/api/v1/runs/&#123;run_id&#125;/result</span>
                  </div>
                  <span className="text-slate-500 text-[11px]">Get task output result</span>
                </div>

                <div className="p-2.5 bg-slate-950 rounded-lg border border-slate-800 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="px-1.5 py-0.5 rounded bg-sky-500/10 text-sky-400 text-[10px] font-bold border border-sky-500/20">GET</span>
                    <span className="text-slate-200">/api/v1/runs/&#123;run_id&#125;/stream</span>
                  </div>
                  <span className="text-slate-500 text-[11px]">Server-Sent Events (SSE) stream</span>
                </div>

                <div className="p-2.5 bg-slate-950 rounded-lg border border-slate-800 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 text-[10px] font-bold border border-emerald-500/20">POST</span>
                    <span className="text-slate-200">/api/v1/workflows/&#123;workflow_id&#125;/runs</span>
                  </div>
                  <span className="text-slate-500 text-[11px]">Execute published workflow</span>
                </div>

                <div className="p-2.5 bg-slate-950 rounded-lg border border-slate-800 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="px-1.5 py-0.5 rounded bg-sky-500/10 text-sky-400 text-[10px] font-bold border border-sky-500/20">GET</span>
                    <span className="text-slate-200">/api/v1/models</span>
                  </div>
                  <span className="text-slate-500 text-[11px]">List approved models</span>
                </div>

                <div className="p-2.5 bg-slate-950 rounded-lg border border-slate-800 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="px-1.5 py-0.5 rounded bg-sky-500/10 text-sky-400 text-[10px] font-bold border border-sky-500/20">GET</span>
                    <span className="text-slate-200">/api/v1/usage</span>
                  </div>
                  <span className="text-slate-500 text-[11px]">Usage telemetry & metrics</span>
                </div>
              </div>
            </div>
          )}

          {activeSection === "streaming" && (
            <div className="space-y-4">
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <Zap className="w-5 h-5 text-indigo-400" />
                Streaming Execution Events (SSE)
              </h2>
              <p>
                Receive real-time progress updates for task runs via standard Server-Sent Events (SSE). Reconnection is supported via <code className="text-indigo-400">Last-Event-ID</code>:
              </p>
              <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 font-mono text-xs text-slate-300 leading-relaxed overflow-x-auto">
{`GET /api/v1/runs/run_abc123/stream HTTP/1.1
Host: api.aiworklayer.com
Authorization: Bearer awl_prod_...
Accept: text/event-stream

event: run.started
data: {"run_id": "run_abc123", "status": "running"}

event: run.step.started
data: {"step": "planning", "step_index": 0}

event: run.progress
data: {"progress_pct": 50, "message": "Synthesizing research notes"}

event: run.completed
data: {"run_id": "run_abc123", "status": "completed"}`}
              </div>
              <p className="text-xs text-slate-400">
                Internal chain-of-thought tokens and sensitive prompt templates are automatically sanitized and never broadcast to public streams.
              </p>
            </div>
          )}

          {activeSection === "idempotency" && (
            <div className="space-y-4">
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <Layers className="w-5 h-5 text-indigo-400" />
                Idempotency & Concurrency
              </h2>
              <p>
                All mutating endpoints (<code className="text-indigo-400">POST</code>) support safe network retries via the <code className="text-indigo-400">Idempotency-Key</code> header:
              </p>
              <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 font-mono text-xs text-indigo-300 flex items-center justify-between">
                <span>Idempotency-Key: 9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d</span>
                <button
                  onClick={() => handleCopy("Idempotency-Key: 9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d", "idem_header")}
                  className="p-1 hover:bg-slate-800 rounded text-slate-400 hover:text-slate-200"
                >
                  {copiedKey === "idem_header" ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                </button>
              </div>
              <p className="text-xs text-slate-400">
                If a network timeout occurs and your client resends the exact request, the server returns the original execution result without triggering a duplicate task run. If the same key is supplied with a different request payload, the server returns <code className="text-amber-400">409 Conflict</code>.
              </p>
            </div>
          )}

          {activeSection === "webhooks" && (
            <div className="space-y-4">
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <Webhook className="w-5 h-5 text-indigo-400" />
                Webhooks & Signature Verification
              </h2>
              <p>
                When events occur, the platform dispatches signed HTTP POST requests to your subscribed endpoint. Each request contains an HMAC-SHA256 signature in the <code className="text-indigo-400">X-AWL-Signature</code> header:
              </p>
              <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 font-mono text-xs text-indigo-300">
                X-AWL-Signature: t=1728000000,v1=5d41402abc4b2a76b9719d911017c592...
              </div>

              <h3 className="text-base font-semibold text-white pt-2">Verification (Node.js Example)</h3>
              <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 font-mono text-xs text-slate-300 overflow-x-auto leading-relaxed">
{`import { verifyWebhookSignature } from "@ai-work-layer/sdk";

app.post("/webhook", (req, res) => {
  const signature = req.headers["x-awl-signature"];
  const secret = process.env.AWL_WEBHOOK_SECRET;

  const isValid = verifyWebhookSignature(req.rawBody, signature, secret, {
    toleranceSeconds: 300,
  });

  if (!isValid) return res.status(401).send("Invalid signature");
  res.status(200).send("OK");
});`}
              </div>
              <p className="text-xs text-slate-400">
                The platform enforces strict SSRF protection: loopback (<code className="text-indigo-400">127.0.0.1</code>), private subnets, and cloud metadata IPs (<code className="text-indigo-400">169.254.169.254</code>) are blocked.
              </p>
            </div>
          )}

          {activeSection === "sdks" && (
            <div className="space-y-4">
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <Code2 className="w-5 h-5 text-indigo-400" />
                Official SDKs
              </h2>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* JavaScript SDK */}
                <div className="p-4 bg-slate-950 rounded-xl border border-slate-800 space-y-3">
                  <div className="font-semibold text-white flex items-center justify-between">
                    <span>JavaScript / Node.js SDK</span>
                    <span className="text-[10px] font-mono text-indigo-400">@ai-work-layer/sdk</span>
                  </div>
                  <div className="p-2 bg-slate-900 rounded font-mono text-xs text-indigo-300">
                    npm install @ai-work-layer/sdk
                  </div>
                  <div className="font-mono text-[11px] text-slate-300 leading-relaxed overflow-x-auto">
{`import { AIWorkLayerClient } from "@ai-work-layer/sdk";

const client = new AIWorkLayerClient({
  apiKey: process.env.AWL_API_KEY,
  environment: "production",
});

const run = await client.tasks.run("task-id", {
  input: "Generate report",
});
console.log(run.run_id);`}
                  </div>
                </div>

                {/* Python SDK */}
                <div className="p-4 bg-slate-950 rounded-xl border border-slate-800 space-y-3">
                  <div className="font-semibold text-white flex items-center justify-between">
                    <span>Python SDK</span>
                    <span className="text-[10px] font-mono text-indigo-400">ai-work-layer</span>
                  </div>
                  <div className="p-2 bg-slate-900 rounded font-mono text-xs text-indigo-300">
                    pip install ai-work-layer
                  </div>
                  <div className="font-mono text-[11px] text-slate-300 leading-relaxed overflow-x-auto">
{`from ai_work_layer import Client

client = Client(
    api_key="awl_prod_...",
    environment="production"
)

run = client.tasks.run("task-id", {
    "input": "Generate report"
})
print(run["run_id"])`}
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeSection === "openapi" && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-bold text-white flex items-center gap-2">
                  <Download className="w-5 h-5 text-indigo-400" />
                  Public OpenAPI 3.0 Specification
                </h2>
                <button
                  onClick={downloadOpenApiJson}
                  disabled={!openApiSpec}
                  className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded-lg text-xs font-semibold shadow-sm transition flex items-center gap-1.5"
                >
                  <Download className="w-3.5 h-3.5" />
                  Download JSON
                </button>
              </div>
              <p className="text-xs text-slate-400">
                The OpenAPI specification contains only authorized Public API endpoints under <code className="text-indigo-400">/api/v1/</code>. Internal administration routes and private service schemas are strictly excluded.
              </p>

              <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 font-mono text-xs text-slate-300 max-h-96 overflow-y-auto">
                <pre>{openApiSpec ? JSON.stringify(openApiSpec, null, 2) : "Loading OpenAPI specification..."}</pre>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
