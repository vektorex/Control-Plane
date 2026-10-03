"use client";

import React, { useState } from "react";
import { Play, CheckCircle2, AlertCircle, Copy, Check, Terminal, Clock, ShieldCheck } from "lucide-react";
import { developerService } from "@/services/developer";

const SANDBOX_OPERATIONS = [
  {
    id: "list_models",
    label: "GET /api/v1/models",
    method: "GET",
    path: "/api/v1/models",
    description: "Inspect available LLM models and verified capabilities",
    defaultBody: "",
  },
  {
    id: "list_workflows",
    label: "GET /api/v1/workflows",
    method: "GET",
    path: "/api/v1/workflows",
    description: "List published workflows eligible for execution",
    defaultBody: "",
  },
  {
    id: "run_task",
    label: "POST /api/v1/tasks/{id}/runs",
    method: "POST",
    path: "/api/v1/tasks/00000000-0000-0000-0000-000000000000/runs",
    description: "Execute a task in the development sandbox environment",
    defaultBody: JSON.stringify(
      {
        input: "Analyze test development metrics and report summary.",
        stream: false,
      },
      null,
      2
    ),
  },
  {
    id: "list_memory",
    label: "GET /api/v1/memory",
    method: "GET",
    path: "/api/v1/memory",
    description: "List persistent structured memory items",
    defaultBody: "",
  },
  {
    id: "get_usage",
    label: "GET /api/v1/usage",
    method: "GET",
    path: "/api/v1/usage?period_hours=24",
    description: "Fetch aggregated telemetry for recent invocations",
    defaultBody: "",
  },
];

export function SandboxRunner() {
  const [selectedOp, setSelectedOp] = useState(SANDBOX_OPERATIONS[0]);
  const [requestPath, setRequestPath] = useState(SANDBOX_OPERATIONS[0].path);
  const [requestBody, setRequestBody] = useState(SANDBOX_OPERATIONS[0].defaultBody);
  const [apiKey, setApiKey] = useState("");
  const [executing, setExecuting] = useState(false);
  const [responseStatus, setResponseStatus] = useState(null);
  const [responseData, setResponseData] = useState(null);
  const [requestId, setRequestId] = useState(null);
  const [durationMs, setDurationMs] = useState(null);
  const [copied, setCopied] = useState(false);

  function handleSelectOp(op) {
    setSelectedOp(op);
    setRequestPath(op.path);
    setRequestBody(op.defaultBody);
    setResponseStatus(null);
    setResponseData(null);
    setRequestId(null);
  }

  async function handleExecute() {
    setExecuting(true);
    setResponseStatus(null);
    setResponseData(null);
    setRequestId(null);
    const start = performance.now();

    try {
      const headers = {};
      if (apiKey.trim()) {
        headers["Authorization"] = `Bearer ${apiKey.trim()}`;
      }

      let parsedBody = null;
      if (selectedOp.method !== "GET" && requestBody.trim()) {
        try {
          parsedBody = JSON.parse(requestBody);
        } catch {
          parsedBody = requestBody;
        }
      }

      const res = await developerService.executePublicSandbox(
        selectedOp.method,
        requestPath,
        headers,
        parsedBody
      );

      const elapsed = Math.round(performance.now() - start);
      setDurationMs(elapsed);
      setResponseStatus(200);
      setResponseData(res);
      setRequestId(res?.request_id || "req_sbx_" + Math.random().toString(36).substring(7));
    } catch (err) {
      const elapsed = Math.round(performance.now() - start);
      setDurationMs(elapsed);
      setResponseStatus(err?.statusCode || 400);
      setResponseData(err?.details || { message: err?.message || "Execution failed" });
      setRequestId(err?.requestId || null);
    } finally {
      setExecuting(false);
    }
  }

  function handleCopyResponse() {
    if (responseData) {
      navigator.clipboard.writeText(JSON.stringify(responseData, null, 2));
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  }

  return (
    <div className="space-y-4">
      {/* Top Banner */}
      <div className="p-4 rounded-xl border border-blue-200 dark:border-blue-900 bg-blue-50 dark:bg-blue-950/30 flex items-start gap-3">
        <ShieldCheck className="w-5 h-5 text-blue-600 dark:text-blue-400 shrink-0 mt-0.5" />
        <div className="text-xs text-blue-900 dark:text-blue-200">
          <div className="font-semibold text-sm mb-0.5">Development Sandbox Testbed</div>
          Safe playground strictly isolated from production environments. Invocations execute against development-tier policies with automated request correlation and mock safeguards.
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* Left Column: Operation & Configuration */}
        <div className="lg:col-span-5 space-y-4">
          <div className="rounded-xl border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 p-4 shadow-sm space-y-4">
            <div>
              <label className="block text-xs font-semibold text-neutral-700 dark:text-neutral-300 mb-2">
                Select API Operation
              </label>
              <div className="space-y-1.5">
                {SANDBOX_OPERATIONS.map((op) => (
                  <button
                    key={op.id}
                    onClick={() => handleSelectOp(op)}
                    className={`w-full text-left p-2.5 rounded-lg border text-xs transition-all ${
                      selectedOp.id === op.id
                        ? "border-blue-500 bg-blue-50/50 dark:bg-blue-950/20 text-blue-900 dark:text-blue-200"
                        : "border-neutral-200 dark:border-neutral-800 hover:bg-neutral-50 dark:hover:bg-neutral-800/50 text-neutral-700 dark:text-neutral-300"
                    }`}
                  >
                    <div className="flex items-center gap-2 font-mono font-medium">
                      <span
                        className={`text-[10px] px-1.5 py-0.5 rounded font-bold ${
                          op.method === "GET"
                            ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300"
                            : "bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300"
                        }`}
                      >
                        {op.method}
                      </span>
                      <span>{op.path.split("?")[0]}</span>
                    </div>
                    <div className="text-[11px] text-neutral-500 dark:text-neutral-400 mt-1">
                      {op.description}
                    </div>
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-neutral-700 dark:text-neutral-300 mb-1">
                API Key (Optional for Sandbox)
              </label>
              <input
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="awl_dev_... (uses active session if empty)"
                className="w-full text-xs font-mono px-3 py-2 rounded-lg border border-neutral-200 dark:border-neutral-700 bg-neutral-50 dark:bg-neutral-800 text-neutral-900 dark:text-neutral-100 focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
            </div>

            {selectedOp.method !== "GET" && (
              <div>
                <label className="block text-xs font-medium text-neutral-700 dark:text-neutral-300 mb-1">
                  JSON Request Body
                </label>
                <textarea
                  rows={6}
                  value={requestBody}
                  onChange={(e) => setRequestBody(e.target.value)}
                  className="w-full font-mono text-xs px-3 py-2 rounded-lg border border-neutral-200 dark:border-neutral-700 bg-neutral-50 dark:bg-neutral-800 text-neutral-900 dark:text-neutral-100 focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
              </div>
            )}

            <button
              onClick={handleExecute}
              disabled={executing}
              className="w-full flex items-center justify-center gap-2 text-xs font-medium py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white transition-colors disabled:opacity-50"
            >
              <Play className="w-3.5 h-3.5 fill-current" />
              {executing ? "Dispatching Call..." : "Execute in Sandbox"}
            </button>
          </div>
        </div>

        {/* Right Column: Execution Output */}
        <div className="lg:col-span-7">
          <div className="h-full rounded-xl border border-neutral-200 dark:border-neutral-800 bg-neutral-950 text-neutral-100 p-4 shadow-sm flex flex-col font-mono text-xs">
            <div className="flex items-center justify-between border-b border-neutral-800 pb-3 mb-3">
              <div className="flex items-center gap-2">
                <Terminal className="w-4 h-4 text-neutral-400" />
                <span className="font-semibold text-neutral-300">Response Inspector</span>
                {responseStatus && (
                  <span
                    className={`text-[10px] px-2 py-0.5 rounded-full font-bold ${
                      responseStatus >= 200 && responseStatus < 300
                        ? "bg-emerald-900/60 text-emerald-300 border border-emerald-800"
                        : "bg-rose-900/60 text-rose-300 border border-rose-800"
                    }`}
                  >
                    HTTP {responseStatus}
                  </span>
                )}
              </div>

              <div className="flex items-center gap-3 text-neutral-400 text-[11px]">
                {durationMs !== null && (
                  <span className="flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {durationMs}ms
                  </span>
                )}
                {responseData && (
                  <button
                    onClick={handleCopyResponse}
                    className="flex items-center gap-1 hover:text-white transition-colors"
                  >
                    {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                    {copied ? "Copied" : "Copy"}
                  </button>
                )}
              </div>
            </div>

            {requestId && (
              <div className="mb-2 text-[11px] text-neutral-500">
                X-Request-ID: <span className="text-neutral-300 select-all">{requestId}</span>
              </div>
            )}

            <div className="flex-1 overflow-auto rounded bg-neutral-900/60 p-3 text-neutral-200 leading-relaxed min-h-[300px]">
              {executing ? (
                <div className="text-neutral-500 flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-blue-500 animate-ping" />
                  Routing request through Public API Gateway...
                </div>
              ) : responseData ? (
                <pre className="whitespace-pre-wrap">{JSON.stringify(responseData, null, 2)}</pre>
              ) : (
                <div className="text-neutral-600 italic">
                  Select an endpoint and click "Execute in Sandbox" to preview the response.
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
