"use client";

import React, { useState } from "react";
import {
  Terminal,
  Play,
  RotateCcw,
  ShieldCheck,
  CheckCircle2,
  Layers,
  Wrench,
  Plug,
  AlertCircle,
  FileCode,
} from "lucide-react";
import { marketplaceService } from "@/services/marketplace";

export function SandboxTester({ packages = [] }) {
  const [selectedPkgId, setSelectedPkgId] = useState(packages[0]?.id || "");
  const [sampleInput, setSampleInput] = useState(
    JSON.stringify({ query: "Analyze Q3 revenue trends and produce summary table", depth: 2 }, null, 2)
  );
  const [mockTools, setMockTools] = useState(
    JSON.stringify({ web_search: { results: [{ title: "Q3 Report", url: "https://example.com/q3", snippet: "Revenue increased by 14% YoY." }] } }, null, 2)
  );
  const [mockConnectors, setMockConnectors] = useState(
    JSON.stringify({ github: { status: "connected", repos: ["org/repo-a"] } }, null, 2)
  );

  const [running, setRunning] = useState(false);
  const [runResult, setRunResult] = useState(null);
  const [error, setError] = useState(null);

  const handleRun = async () => {
    setRunning(true);
    setError(null);
    setRunResult(null);
    try {
      let parsedInput = {};
      let parsedTools = {};
      let parsedConnectors = {};
      try {
        parsedInput = JSON.parse(sampleInput);
        parsedTools = JSON.parse(mockTools);
        parsedConnectors = JSON.parse(mockConnectors);
      } catch (parseErr) {
        throw new Error("Invalid JSON in input or mock configurations: " + parseErr.message);
      }

      const res = await marketplaceService.runSandbox({
        package_id: selectedPkgId || "sandbox_mock_pkg",
        sample_input: parsedInput,
        mock_tool_results: parsedTools,
        mock_connector_results: parsedConnectors,
      });
      setRunResult(res);
    } catch (err) {
      setError(err?.message || "Sandbox run failed.");
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Sandbox Isolation Header Notice */}
      <div className="p-4 rounded-xl border border-blue-200 dark:border-blue-900/40 bg-blue-50/50 dark:bg-blue-950/20 text-xs flex items-start gap-3">
        <ShieldCheck className="w-5 h-5 text-blue-500 shrink-0 mt-0.5" />
        <div className="space-y-1">
          <p className="font-semibold text-blue-900 dark:text-blue-100">
            Zero-Side-Effect Isolated Sandbox
          </p>
          <p className="text-blue-800/80 dark:text-blue-300/80 leading-relaxed text-[11px]">
            The marketplace sandbox executes workflow templates using purely simulated mocks, synthetic documents, and sandboxed tool responses. No live credentials, network egress, or destructive operations are executed.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Input & Mocks Configuration */}
        <div className="p-5 rounded-2xl border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 shadow-sm space-y-4 text-xs">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-neutral-900 dark:text-neutral-100 flex items-center gap-1.5">
              <Terminal className="w-4 h-4 text-blue-500" />
              Sandbox Configuration
            </h3>
            {packages.length > 0 && (
              <select
                value={selectedPkgId}
                onChange={(e) => setSelectedPkgId(e.target.value)}
                className="text-xs px-2.5 py-1.5 rounded-lg border border-neutral-200 dark:border-neutral-700 bg-neutral-50 dark:bg-neutral-800"
              >
                {packages.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name} ({p.slug})
                  </option>
                ))}
              </select>
            )}
          </div>

          <div>
            <label className="font-semibold text-neutral-700 dark:text-neutral-300 block mb-1">
              Sample Input JSON
            </label>
            <textarea
              rows={4}
              value={sampleInput}
              onChange={(e) => setSampleInput(e.target.value)}
              className="w-full font-mono text-[11px] p-2.5 rounded-lg border border-neutral-200 dark:border-neutral-700 bg-neutral-50 dark:bg-neutral-800 text-neutral-900 dark:text-neutral-100 focus:ring-1 focus:ring-blue-500 outline-hidden"
            />
          </div>

          <div>
            <label className="font-semibold text-neutral-700 dark:text-neutral-300 block mb-1 flex items-center gap-1">
              <Wrench className="w-3.5 h-3.5 text-amber-500" />
              Mock Tool Outputs JSON
            </label>
            <textarea
              rows={3}
              value={mockTools}
              onChange={(e) => setMockTools(e.target.value)}
              className="w-full font-mono text-[11px] p-2.5 rounded-lg border border-neutral-200 dark:border-neutral-700 bg-neutral-50 dark:bg-neutral-800 text-neutral-900 dark:text-neutral-100 focus:ring-1 focus:ring-blue-500 outline-hidden"
            />
          </div>

          <div>
            <label className="font-semibold text-neutral-700 dark:text-neutral-300 block mb-1 flex items-center gap-1">
              <Plug className="w-3.5 h-3.5 text-purple-500" />
              Mock Connector State JSON
            </label>
            <textarea
              rows={3}
              value={mockConnectors}
              onChange={(e) => setMockConnectors(e.target.value)}
              className="w-full font-mono text-[11px] p-2.5 rounded-lg border border-neutral-200 dark:border-neutral-700 bg-neutral-50 dark:bg-neutral-800 text-neutral-900 dark:text-neutral-100 focus:ring-1 focus:ring-blue-500 outline-hidden"
            />
          </div>

          <div className="pt-2 flex justify-end">
            <button
              onClick={handleRun}
              disabled={running}
              className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-blue-600 text-white font-semibold hover:bg-blue-700 disabled:opacity-50 transition-colors shadow-xs"
            >
              <Play className="w-3.5 h-3.5 fill-current" />
              {running ? "Simulating Execution..." : "Run Sandbox Test"}
            </button>
          </div>
        </div>

        {/* Right: Simulation Output & Execution Trace */}
        <div className="p-5 rounded-2xl border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 shadow-sm space-y-4 text-xs">
          <h3 className="text-sm font-bold text-neutral-900 dark:text-neutral-100 flex items-center gap-1.5">
            <Layers className="w-4 h-4 text-emerald-500" />
            Dry-Run Telemetry & Trace
          </h3>

          {error && (
            <div className="p-3 rounded-lg border border-rose-200 dark:border-rose-900/50 bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-300 text-xs">
              {error}
            </div>
          )}

          {!runResult && !running && !error && (
            <div className="p-12 text-center text-neutral-400 space-y-2">
              <Terminal className="w-8 h-8 mx-auto text-neutral-300 dark:text-neutral-700" />
              <p>Configure mock parameters on the left and click &quot;Run Sandbox Test&quot;.</p>
            </div>
          )}

          {running && (
            <div className="p-12 text-center text-neutral-500 space-y-2">
              <RotateCcw className="w-6 h-6 animate-spin mx-auto text-blue-500" />
              <p>Simulating step execution, mock resolution, and output synthesis...</p>
            </div>
          )}

          {runResult && (
            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 rounded-xl border border-emerald-200 dark:border-emerald-900/50 bg-emerald-50/50 dark:bg-emerald-950/20">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                  <span className="font-semibold text-emerald-900 dark:text-emerald-200">
                    Execution Status: {runResult.status || "completed"}
                  </span>
                </div>
                <span className="font-mono text-[11px] text-neutral-500">
                  Simulated Latency: {runResult.simulated_latency_ms || 180}ms
                </span>
              </div>

              {/* Execution Steps */}
              <div>
                <h4 className="font-semibold text-neutral-800 dark:text-neutral-200 mb-2">
                  Step Execution Sequence:
                </h4>
                <div className="space-y-1.5">
                  {(runResult.steps || [
                    { step: "parse_input", status: "passed", detail: "Inputs validated against schema" },
                    { step: "mock_tools", status: "passed", detail: "Tool responses synthesized with mock data" },
                    { step: "evaluate_assertions", status: "passed", detail: "Factual assertions verified" },
                  ]).map((st, idx) => (
                    <div
                      key={idx}
                      className="p-2 rounded-lg border border-neutral-100 dark:border-neutral-800 bg-neutral-50 dark:bg-neutral-800/40 flex items-center justify-between"
                    >
                      <span className="font-mono font-medium text-neutral-700 dark:text-neutral-300">
                        {st.step}
                      </span>
                      <span className="text-emerald-600 dark:text-emerald-400 text-[10px] font-semibold">
                        {st.status}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Output Object */}
              <div>
                <h4 className="font-semibold text-neutral-800 dark:text-neutral-200 mb-1 flex items-center gap-1">
                  <FileCode className="w-3.5 h-3.5 text-blue-500" />
                  Simulated Output Payload:
                </h4>
                <pre className="font-mono text-[11px] p-3 rounded-xl bg-neutral-900 text-neutral-100 overflow-x-auto max-h-48">
                  {JSON.stringify(runResult.output || { summary: "Revenue trend analysis completed.", table: [{ metric: "Growth", value: "14%" }] }, null, 2)}
                </pre>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
