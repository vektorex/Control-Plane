"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Badge } from "@/components/ui/Badge";
import { SimulationBanner } from "@/components/simulation/SimulationBanner";
import { simulationService } from "@/services/simulation";
import {
  Layers,
  ArrowLeft,
  Check,
  ShieldAlert,
  AlertTriangle,
  Zap,
  ShieldCheck,
  Plus,
} from "lucide-react";

export default function VisualScenarioBuilderPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Form states
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [scenarioType, setScenarioType] = useState("normal");
  const [inputPrompt, setInputPrompt] = useState("");
  const [contextInput, setContextInput] = useState("{}");
  const [faultType, setFaultType] = useState("none");
  const [faultProb, setFaultProb] = useState("1.0");

  // Selected Assertions
  const [assertions, setAssertions] = useState([
    { type: "must_complete", value: true, severity: "error" },
    { type: "no_external_side_effect", value: true, severity: "error" },
  ]);

  const toggleAssertion = (type) => {
    if (assertions.some((a) => a.type === type)) {
      setAssertions(assertions.filter((a) => a.type !== type));
    } else {
      setAssertions([...assertions, { type, value: true, severity: "error" }]);
    }
  };

  const validateBeforeSave = () => {
    if (!name.trim()) return "Scenario name is required.";
    if (!inputPrompt.trim()) return "Task input prompt is required.";
    try {
      if (contextInput.trim()) JSON.parse(contextInput);
    } catch {
      return "Context payload must be valid JSON.";
    }
    return null;
  };

  const handleSave = async (e) => {
    e.preventDefault();
    const valErr = validateBeforeSave();
    if (valErr) {
      setError(valErr);
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const faultConfig = {};
      if (faultType !== "none") {
        faultConfig[faultType] = {
          enabled: true,
          mode: "fixed",
          probability: parseFloat(faultProb) || 1.0,
        };
      }

      const payload = {
        name: name.trim(),
        description: description.trim() || undefined,
        scenario_type: scenarioType,
        input: { prompt: inputPrompt.trim() },
        context: contextInput.trim() ? JSON.parse(contextInput) : {},
        fault_configuration: faultConfig,
        assertions,
      };

      await simulationService.createScenario(payload);
      router.push("/app/simulations/scenarios");
    } catch (err) {
      console.error(err);
      setError(err.message || "Failed to create scenario.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <Link
        href="/app/simulations/scenarios"
        className="text-xs text-zinc-400 hover:text-zinc-200 flex items-center gap-1 transition"
      >
        <ArrowLeft className="w-3.5 h-3.5" /> Back to Scenarios
      </Link>

      <SimulationBanner mode="ISOLATED" seed={42} />

      <div>
        <h1 className="text-xl font-bold tracking-tight text-zinc-100 flex items-center gap-2">
          <Layers className="w-5 h-5 text-amber-400" />
          Visual Scenario Builder
        </h1>
        <p className="text-xs text-zinc-400 mt-1">
          Compose reproducible scenarios with injected faults, variable templates, and deterministic assertions.
        </p>
      </div>

      {error && (
        <div className="p-3.5 rounded-lg bg-red-950/40 border border-red-800 text-red-200 text-xs">
          {error}
        </div>
      )}

      <form onSubmit={handleSave} className="space-y-6">
        {/* Scenario Metadata */}
        <Card className="p-5 border-zinc-800 bg-zinc-900/80 space-y-4">
          <h2 className="text-sm font-semibold text-zinc-200">1. Scenario Definition</h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="text-xs font-medium text-zinc-400 block mb-1">Scenario Name *</label>
              <Input
                placeholder="e.g. Prompt Injection Bypass Test"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="bg-zinc-950 border-zinc-800 text-sm"
                required
              />
            </div>

            <div>
              <label className="text-xs font-medium text-zinc-400 block mb-1">Scenario Type *</label>
              <select
                value={scenarioType}
                onChange={(e) => setScenarioType(e.target.value)}
                className="w-full bg-zinc-950 border border-zinc-800 text-zinc-200 rounded-md px-3 py-2 text-sm focus:outline-none"
              >
                <option value="normal">Normal Baseline</option>
                <option value="edge_case">Edge Case</option>
                <option value="failure">Failure / Timeout</option>
                <option value="security">Security Policy Check</option>
                <option value="adversarial">Adversarial Attack</option>
                <option value="performance">Performance & Budget</option>
              </select>
            </div>
          </div>

          <div>
            <label className="text-xs font-medium text-zinc-400 block mb-1">Description</label>
            <Input
              placeholder="Tests agent defense when user instructs system prompt disclosure."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="bg-zinc-950 border-zinc-800 text-sm"
            />
          </div>
        </Card>

        {/* Input & Context */}
        <Card className="p-5 border-zinc-800 bg-zinc-900/80 space-y-4">
          <h2 className="text-sm font-semibold text-zinc-200">2. Input Prompt & Context Payload</h2>

          <div>
            <label className="text-xs font-medium text-zinc-400 block mb-1">
              Task Input Prompt * (supports safe variables like {"{{agent.id}}"})
            </label>
            <textarea
              rows={3}
              value={inputPrompt}
              onChange={(e) => setInputPrompt(e.target.value)}
              placeholder="e.g. Please analyze this repository and create a GitHub issue with the findings."
              className="w-full bg-zinc-950 border border-zinc-800 text-zinc-200 rounded-md p-3 text-sm font-mono focus:outline-none"
              required
            />
          </div>

          <div>
            <label className="text-xs font-medium text-zinc-400 block mb-1">
              Context JSON (optional synthetic metadata)
            </label>
            <textarea
              rows={2}
              value={contextInput}
              onChange={(e) => setContextInput(e.target.value)}
              className="w-full bg-zinc-950 border border-zinc-800 text-zinc-200 rounded-md p-3 text-xs font-mono focus:outline-none"
            />
          </div>
        </Card>

        {/* Fault Injection */}
        <Card className="p-5 border-zinc-800 bg-zinc-900/80 space-y-4">
          <h2 className="text-sm font-semibold text-zinc-200">3. Injected Fault (Section 16)</h2>
          <p className="text-xs text-zinc-400">
            Inject deterministic bounded failure conditions to evaluate resilience.
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="text-xs font-medium text-zinc-400 block mb-1">Injected Fault</label>
              <select
                value={faultType}
                onChange={(e) => setFaultType(e.target.value)}
                className="w-full bg-zinc-950 border border-zinc-800 text-zinc-200 rounded-md px-3 py-2 text-sm focus:outline-none"
              >
                <option value="none">None (Standard execution)</option>
                <option value="model_timeout">Model Timeout</option>
                <option value="model_unavailable">Model Unavailable</option>
                <option value="connector_timeout">Connector Timeout</option>
                <option value="connector_failure">Connector Failure</option>
                <option value="tool_timeout">Tool Timeout</option>
                <option value="retrieval_empty">Retrieval Empty</option>
                <option value="budget_exhausted">Budget Exhausted</option>
              </select>
            </div>
            {faultType !== "none" && (
              <div>
                <label className="text-xs font-medium text-zinc-400 block mb-1">Trigger Probability (0.0 to 1.0)</label>
                <Input
                  type="number"
                  step="0.1"
                  min="0"
                  max="1"
                  value={faultProb}
                  onChange={(e) => setFaultProb(e.target.value)}
                  className="bg-zinc-950 border-zinc-800 text-sm font-mono"
                />
              </div>
            )}
          </div>
        </Card>

        {/* Assertions & Security Assertions */}
        <Card className="p-5 border-zinc-800 bg-zinc-900/80 space-y-4">
          <h2 className="text-sm font-semibold text-zinc-200">4. Assertions & Security Checks</h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
            {[
              { id: "must_complete", label: "Must Complete Run" },
              { id: "no_external_side_effect", label: "No External Side Effects (Sandbox Intercept)" },
              { id: "no_secret_exposure", label: "No Secret Exposure (Tokens, Keys)" },
              { id: "no_privilege_escalation", label: "No Privilege Escalation" },
              { id: "no_cross_tenant_access", label: "No Cross-Tenant Access" },
              { id: "required_approval", label: "Must Require Virtual Approval" },
              { id: "max_cost", label: "Cost Must Be Under $0.05" },
            ].map((item) => {
              const active = assertions.some((a) => a.type === item.id);
              return (
                <div
                  key={item.id}
                  onClick={() => toggleAssertion(item.id)}
                  className={`p-2.5 rounded-md border text-xs cursor-pointer flex items-center justify-between transition ${
                    active
                      ? "border-amber-500/50 bg-amber-950/30 text-amber-200 font-medium"
                      : "border-zinc-800 bg-zinc-950/40 text-zinc-400 hover:border-zinc-700"
                  }`}
                >
                  <span>{item.label}</span>
                  {active && <Check className="w-4 h-4 text-amber-400" />}
                </div>
              );
            })}
          </div>
        </Card>

        <div className="flex justify-end gap-3 pt-2">
          <Link href="/app/simulations/scenarios">
            <Button variant="outline" className="border-zinc-700 text-zinc-300">
              Cancel
            </Button>
          </Link>
          <Button
            type="submit"
            disabled={loading}
            className="bg-amber-600 hover:bg-amber-500 text-white font-medium px-6 shadow-md"
          >
            {loading ? "Saving..." : "Save Scenario"}
          </Button>
        </div>
      </form>
    </div>
  );
}
