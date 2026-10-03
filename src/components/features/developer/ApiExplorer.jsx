"use client";

import React, { useState, useEffect } from "react";
import { Terminal, Play, Copy, Check, Clock, ShieldAlert, BookOpen } from "lucide-react";
import { developerService } from "@/services/developer";

export function ApiExplorer() {
  const [openApiSpec, setOpenApiSpec] = useState(null);
  const [selectedEndpoint, setSelectedEndpoint] = useState("/api/v1/models");
  const [selectedMethod, setSelectedMethod] = useState("GET");
  const [apiKey, setApiKey] = useState("");
  const [environment, setEnvironment] = useState("development");
  const [requestBody, setRequestBody] = useState("");
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState(null);
  const [status, setStatus] = useState(null);
  const [requestId, setRequestId] = useState(null);
  const [latency, setLatency] = useState(null);
  const [copied, setCopied] = useState(false);

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

  const endpoints = openApiSpec?.paths ? Object.keys(openApiSpec.paths) : [
    "/api/v1/tasks/{task_id}/runs",
    "/api/v1/runs/{run_id}",
    "/api/v1/runs/{run_id}/result",
    "/api/v1/workflows",
    "/api/v1/artifacts",
    "/api/v1/documents",
    "/api/v1/models",
    "/api/v1/connectors",
    "/api/v1/memory",
    "/api/v1/knowledge/entities",
    "/api/v1/webhooks",
    "/api/v1/usage",
  ];

  async function handleSend() {
    setLoading(true);
    setResponse(null);
    setStatus(null);
    setRequestId(null);
    const start = performance.now();

    try {
      const headers = {};
      if (apiKey.trim()) {
        headers["Authorization"] = `Bearer ${apiKey.trim()}`;
      }

      let body = null;
      if (selectedMethod !== "GET" && requestBody.trim()) {
        try {
          body = JSON.parse(requestBody);
        } catch {
          body = requestBody;
        }
      }

      const res = await developerService.executePublicSandbox(
        selectedMethod,
        selectedEndpoint,
        headers,
        body
      );

      const elapsed = Math.round(performance.now() - start);
      setLatency(elapsed);
      setStatus(200);
      setResponse(res);
      setRequestId(res?.request_id || "req_" + Math.random().toString(36).substring(7));
    } catch (err) {
      const elapsed = Math.round(performance.now() - start);
      setLatency(elapsed);
      setStatus(err?.statusCode || 400);
      setResponse(err?.details || { message: err?.message || "Request failed" });
      setRequestId(err?.requestId || null);
    } finally {
      setLoading(false);
    }
  }

  function handleCopyResponse() {
    if (response) {
      navigator.clipboard.writeText(JSON.stringify(response, null, 2));
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  }

  return (
    <div className="space-y-4">
      <div className="rounded-xl border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 p-4 shadow-sm">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
          <div>
            <label className="block text-xs font-medium text-neutral-700 dark:text-neutral-300 mb-1">
              Method & Endpoint
            </label>
            <div className="flex gap-2">
              <select
                value={selectedMethod}
                onChange={(e) => setSelectedMethod(e.target.value)}
                className="w-24 text-xs font-semibold px-2.5 py-1.5 rounded-lg border border-neutral-200 dark:border-neutral-700 bg-neutral-50 dark:bg-neutral-800 text-neutral-900 dark:text-neutral-100 focus:outline-none"
              >
                <option value="GET">GET</option>
                <option value="POST">POST</option>
                <option value="DELETE">DELETE</option>
              </select>
              <select
                value={selectedEndpoint}
                onChange={(e) => setSelectedEndpoint(e.target.value)}
                className="flex-1 text-xs font-mono px-2.5 py-1.5 rounded-lg border border-neutral-200 dark:border-neutral-700 bg-neutral-50 dark:bg-neutral-800 text-neutral-900 dark:text-neutral-100 focus:outline-none"
              >
                {endpoints.map((ep) => (
                  <option key={ep} value={ep}>
                    {ep}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-neutral-700 dark:text-neutral-300 mb-1">
              Environment
            </label>
            <select
              value={environment}
              onChange={(e) => setEnvironment(e.target.value)}
              className="w-full text-xs px-2.5 py-1.5 rounded-lg border border-neutral-200 dark:border-neutral-700 bg-neutral-50 dark:bg-neutral-800 text-neutral-900 dark:text-neutral-100 focus:outline-none"
            >
              <option value="development">Development</option>
              <option value="staging">Staging</option>
              <option value="production">Production</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-neutral-700 dark:text-neutral-300 mb-1">
              API Key (Masked)
            </label>
            <input
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="awl_dev_... (session auth used if empty)"
              className="w-full text-xs font-mono px-3 py-1.5 rounded-lg border border-neutral-200 dark:border-neutral-700 bg-neutral-50 dark:bg-neutral-800 text-neutral-900 dark:text-neutral-100 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>

          <div className="flex items-end">
            <button
              onClick={handleSend}
              disabled={loading}
              className="w-full flex items-center justify-center gap-1.5 text-xs font-medium px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white transition-colors disabled:opacity-50"
            >
              <Play className="w-3.5 h-3.5 fill-current" />
              {loading ? "Sending..." : "Send Request"}
            </button>
          </div>
        </div>

        {selectedMethod !== "GET" && (
          <div className="mt-3">
            <label className="block text-xs font-medium text-neutral-700 dark:text-neutral-300 mb-1">
              Request Payload (JSON)
            </label>
            <textarea
              rows={4}
              value={requestBody}
              onChange={(e) => setRequestBody(e.target.value)}
              placeholder='{ "input": "Analyze recent tasks" }'
              className="w-full font-mono text-xs px-3 py-2 rounded-lg border border-neutral-200 dark:border-neutral-700 bg-neutral-50 dark:bg-neutral-800 text-neutral-900 dark:text-neutral-100 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>
        )}
      </div>

      {/* Response Box */}
      <div className="rounded-xl border border-neutral-200 dark:border-neutral-800 bg-neutral-950 text-neutral-100 p-4 shadow-sm font-mono text-xs">
        <div className="flex items-center justify-between border-b border-neutral-800 pb-2 mb-2">
          <div className="flex items-center gap-2">
            <Terminal className="w-4 h-4 text-neutral-400" />
            <span className="font-semibold text-neutral-300">Live API Response</span>
            {status && (
              <span
                className={`text-[10px] px-2 py-0.5 rounded-full font-bold ${
                  status >= 200 && status < 300
                    ? "bg-emerald-900/60 text-emerald-300 border border-emerald-800"
                    : "bg-rose-900/60 text-rose-300 border border-rose-800"
                }`}
              >
                HTTP {status}
              </span>
            )}
          </div>

          <div className="flex items-center gap-3 text-neutral-400 text-[11px]">
            {latency !== null && (
              <span className="flex items-center gap-1">
                <Clock className="w-3 h-3" />
                {latency}ms
              </span>
            )}
            {response && (
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
            Request ID: <span className="text-neutral-300 select-all">{requestId}</span>
          </div>
        )}

        <div className="overflow-auto max-h-[400px] rounded bg-neutral-900/60 p-3 text-neutral-200 leading-relaxed">
          {loading ? (
            <div className="text-neutral-500">Dispatching request to {selectedEndpoint}...</div>
          ) : response ? (
            <pre className="whitespace-pre-wrap">{JSON.stringify(response, null, 2)}</pre>
          ) : (
            <div className="text-neutral-600 italic">Send a request above to inspect response data.</div>
          )}
        </div>
      </div>
    </div>
  );
}
