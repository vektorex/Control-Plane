"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { agentService } from "@/services/agents";
import { useWorkspace } from "@/lib/workspaceContext";
import {
  Bot,
  ArrowLeft,
  ShieldCheck,
  ShieldAlert,
  Zap,
  CheckCircle2,
  AlertCircle,
  Cpu,
  Brain,
  Layers,
  Sparkles,
} from "lucide-react";

const AVAILABLE_CAPABILITIES = [
  { id: "task_execute", label: "task_execute", desc: "Execute bounded tasks through AI Gateway" },
  { id: "workflow_run", label: "workflow_run", desc: "Invoke published workflow pipelines" },
  { id: "retrieve", label: "retrieve", desc: "Perform RAG retrieval over context sources" },
  { id: "memory_read", label: "memory_read", desc: "Read persistent memory facts" },
  { id: "memory_write", label: "memory_write", desc: "Propose new memory facts (requires verification)", privileged: true },
  { id: "knowledge_read", label: "knowledge_read", desc: "Query relational knowledge graph entities" },
  { id: "document_read", label: "document_read", desc: "Read chunked document text" },
  { id: "artifact_read", label: "artifact_read", desc: "Access multimodal artifacts" },
  { id: "artifact_create", label: "artifact_create", desc: "Generate multimodal artifacts" },
  { id: "tool_use", label: "tool_use", desc: "Invoke registered tools" },
  { id: "connector_read", label: "connector_read", desc: "Query authorized connector integrations" },
  { id: "prompt_use", label: "prompt_use", desc: "Render versioned prompts from registry" },
  { id: "collaboration_comment", label: "collaboration_comment", desc: "Post comment entries in shared sessions" },
  { id: "agent_delegate", label: "agent_delegate", desc: "Delegate sub-tasks to permitted child agents", privileged: true },
];

export default function NewAgentPage() {
  const router = useRouter();
  const { activeWorkspace } = useWorkspace();

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Form State
  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [purpose, setPurpose] = useState("");
  const [instructions, setInstructions] = useState(
    "You are a bounded, governed AI agent assisting with structured tasks. Never extrapolate beyond provided facts."
  );
  const [preferredModel, setPreferredModel] = useState("gpt-4o-mini");
  const [temperature, setTemperature] = useState(0.2);
  const [maxOutputTokens, setMaxOutputTokens] = useState(2048);
  const [selectedCaps, setSelectedCaps] = useState(["task_execute", "retrieve", "memory_read", "document_read"]);
  const [maxSteps, setMaxSteps] = useState(15);
  const [maxCost, setMaxCost] = useState(2.0);
  const [reqExternalApproval, setReqExternalApproval] = useState(true);
  const [reqDelegationApproval, setReqDelegationApproval] = useState(false);

  const toggleCapability = (capId) => {
    setSelectedCaps((prev) =>
      prev.includes(capId) ? prev.filter((c) => c !== capId) : [...prev, capId]
    );
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!name.trim() || !purpose.trim()) {
      setError("Name and purpose are required.");
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const payload = {
        name: name.trim(),
        slug: slug.trim() || undefined,
        purpose: purpose.trim(),
        instructions: instructions.trim(),
        capability_policy: selectedCaps,
        model_policy: {
          preferred_model: preferredModel,
          temperature: Number(temperature),
          max_output_tokens: Number(maxOutputTokens),
        },
        execution_policy: {
          max_steps: Number(maxSteps),
          max_cost: Number(maxCost),
        },
        approval_policy: {
          requires_approval_for_external_actions: reqExternalApproval,
          requires_approval_for_delegation: reqDelegationApproval,
        },
        budget_policy: {
          max_budget_per_run: Number(maxCost),
        },
      };

      const agent = await agentService.createAgent(payload);
      router.push(`/app/agents/${agent.id}`);
    } catch (err) {
      console.error("[NewAgentPage] Error creating agent:", err);
      setError(err.message || "Failed to create agent");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-12">
      {/* Top Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link
            href="/app/agents"
            className="p-2 rounded-lg bg-zinc-900 hover:bg-zinc-800 text-zinc-400 hover:text-zinc-200 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <h1 className="text-xl font-bold text-zinc-100 flex items-center gap-2">
              <Bot className="w-6 h-6 text-purple-400" />
              <span>Agent Builder</span>
            </h1>
            <p className="text-xs text-zinc-400">
              Declare identity, purpose, model constraints, and explicit capabilities.
            </p>
          </div>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl border border-rose-500/30 bg-rose-500/10 text-rose-300 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Columns: Configuration Form */}
        <div className="lg:col-span-2 space-y-6">
          {/* Identity & Purpose */}
          <Card className="p-5 border-zinc-800 bg-zinc-950/70 space-y-4">
            <h3 className="text-sm font-semibold text-zinc-200 flex items-center gap-2">
              <Bot className="w-4 h-4 text-purple-400" />
              <span>Identity & Purpose</span>
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-zinc-300">Agent Name *</label>
                <Input
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Research Analyst Agent"
                  className="bg-zinc-900 border-zinc-700 text-xs"
                  required
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-medium text-zinc-300">Slug (Optional)</label>
                <Input
                  value={slug}
                  onChange={(e) => setSlug(e.target.value)}
                  placeholder="e.g. research-analyst"
                  className="bg-zinc-900 border-zinc-700 text-xs"
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-medium text-zinc-300">Explicit Purpose *</label>
              <textarea
                value={purpose}
                onChange={(e) => setPurpose(e.target.value)}
                placeholder="Declare the specific bounded work this agent is authorized to perform..."
                rows={2}
                className="w-full text-xs p-2.5 rounded-lg bg-zinc-900 border border-zinc-700 text-zinc-200 focus:outline-none focus:border-purple-500"
                required
              />
            </div>
          </Card>

          {/* System Instructions */}
          <Card className="p-5 border-zinc-800 bg-zinc-950/70 space-y-3">
            <h3 className="text-sm font-semibold text-zinc-200 flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-purple-400" />
              <span>System Instructions</span>
            </h3>
            <textarea
              value={instructions}
              onChange={(e) => setInstructions(e.target.value)}
              rows={4}
              className="w-full text-xs p-3 rounded-lg bg-zinc-900 border border-zinc-700 text-zinc-200 font-mono focus:outline-none focus:border-purple-500"
              required
            />
          </Card>

          {/* Model Policy */}
          <Card className="p-5 border-zinc-800 bg-zinc-950/70 space-y-4">
            <h3 className="text-sm font-semibold text-zinc-200 flex items-center gap-2">
              <Cpu className="w-4 h-4 text-purple-400" />
              <span>Model Policy</span>
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-zinc-300">Preferred Model</label>
                <select
                  value={preferredModel}
                  onChange={(e) => setPreferredModel(e.target.value)}
                  className="w-full text-xs p-2 rounded-lg bg-zinc-900 border border-zinc-700 text-zinc-200"
                >
                  <option value="gpt-4o-mini">gpt-4o-mini</option>
                  <option value="gpt-4o">gpt-4o</option>
                  <option value="claude-3-5-sonnet">claude-3-5-sonnet</option>
                  <option value="mock-model">mock-model (Testing)</option>
                </select>
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-medium text-zinc-300">Temperature</label>
                <Input
                  type="number"
                  step="0.05"
                  min="0"
                  max="1"
                  value={temperature}
                  onChange={(e) => setTemperature(e.target.value)}
                  className="bg-zinc-900 border-zinc-700 text-xs"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-medium text-zinc-300">Max Tokens</label>
                <Input
                  type="number"
                  step="256"
                  min="256"
                  max="8192"
                  value={maxOutputTokens}
                  onChange={(e) => setMaxOutputTokens(e.target.value)}
                  className="bg-zinc-900 border-zinc-700 text-xs"
                />
              </div>
            </div>
          </Card>

          {/* Declarative Capabilities */}
          <Card className="p-5 border-zinc-800 bg-zinc-950/70 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold text-zinc-200 flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-purple-400" />
                <span>Declarative Capabilities</span>
              </h3>
              <span className="text-[11px] text-zinc-400 font-mono">
                {selectedCaps.length} selected
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
              {AVAILABLE_CAPABILITIES.map((cap) => {
                const isSelected = selectedCaps.includes(cap.id);
                return (
                  <button
                    type="button"
                    key={cap.id}
                    onClick={() => toggleCapability(cap.id)}
                    className={`p-3 rounded-lg border text-left transition-all flex items-start gap-2.5 ${
                      isSelected
                        ? "bg-purple-600/10 border-purple-500/40 text-purple-200"
                        : "bg-zinc-900/40 border-zinc-800/80 text-zinc-400 hover:border-zinc-700"
                    }`}
                  >
                    <div
                      className={`w-4 h-4 rounded border mt-0.5 flex items-center justify-center text-[10px] ${
                        isSelected
                          ? "bg-purple-600 border-purple-400 text-white"
                          : "border-zinc-700 bg-zinc-800"
                      }`}
                    >
                      {isSelected && <CheckCircle2 className="w-3.5 h-3.5" />}
                    </div>
                    <div>
                      <div className="text-xs font-semibold font-mono flex items-center gap-1.5">
                        <span>{cap.label}</span>
                        {cap.privileged && (
                          <span className="text-[9px] px-1 rounded bg-amber-500/20 text-amber-300 font-sans">
                            Privileged
                          </span>
                        )}
                      </div>
                      <p className="text-[11px] text-zinc-500 leading-tight mt-0.5">
                        {cap.desc}
                      </p>
                    </div>
                  </button>
                );
              })}
            </div>
          </Card>

          {/* Limits & HITL Approvals */}
          <Card className="p-5 border-zinc-800 bg-zinc-950/70 space-y-4">
            <h3 className="text-sm font-semibold text-zinc-200 flex items-center gap-2">
              <Zap className="w-4 h-4 text-purple-400" />
              <span>Limits & Human Oversight</span>
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-zinc-300">Max Steps Per Run</label>
                <Input
                  type="number"
                  min="1"
                  max="50"
                  value={maxSteps}
                  onChange={(e) => setMaxSteps(e.target.value)}
                  className="bg-zinc-900 border-zinc-700 text-xs"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-medium text-zinc-300">Max Budget Per Run ($)</label>
                <Input
                  type="number"
                  step="0.25"
                  min="0.1"
                  max="50"
                  value={maxCost}
                  onChange={(e) => setMaxCost(e.target.value)}
                  className="bg-zinc-900 border-zinc-700 text-xs"
                />
              </div>
            </div>

            <div className="space-y-2 pt-2 border-t border-zinc-800">
              <label className="flex items-center gap-2 text-xs text-zinc-300 cursor-pointer">
                <input
                  type="checkbox"
                  checked={reqExternalApproval}
                  onChange={(e) => setReqExternalApproval(e.target.checked)}
                  className="rounded border-zinc-700 bg-zinc-900 text-purple-600 focus:ring-0"
                />
                <span>Require Human-in-the-Loop approval for external actions</span>
              </label>

              <label className="flex items-center gap-2 text-xs text-zinc-300 cursor-pointer">
                <input
                  type="checkbox"
                  checked={reqDelegationApproval}
                  onChange={(e) => setReqDelegationApproval(e.target.checked)}
                  className="rounded border-zinc-700 bg-zinc-900 text-purple-600 focus:ring-0"
                />
                <span>Require Human approval before delegating work to child agents</span>
              </label>
            </div>
          </Card>

          <Button
            type="submit"
            disabled={loading}
            className="w-full bg-purple-600 hover:bg-purple-500 text-white font-semibold py-2.5"
          >
            {loading ? "Creating Agent..." : "Create Governed Agent"}
          </Button>
        </div>

        {/* Right Column: Real-Time Effective Policy Preview */}
        <div className="space-y-4">
          <Card className="p-5 border-zinc-800 bg-zinc-950/80 sticky top-6 space-y-4">
            <div className="flex items-center gap-2 border-b border-zinc-800 pb-3">
              <ShieldAlert className="w-4 h-4 text-purple-400" />
              <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-200">
                Effective Policy Preview
              </h3>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <span className="text-zinc-500 block font-mono text-[10px] uppercase">
                  Allowed Capabilities ({selectedCaps.length})
                </span>
                <div className="flex flex-wrap gap-1 mt-1">
                  {selectedCaps.map((c) => (
                    <span
                      key={c}
                      className="px-2 py-0.5 rounded bg-purple-500/10 text-purple-300 border border-purple-500/20 font-mono text-[10px]"
                    >
                      {c}
                    </span>
                  ))}
                </div>
              </div>

              <div>
                <span className="text-zinc-500 block font-mono text-[10px] uppercase">
                  Denied Capabilities ({AVAILABLE_CAPABILITIES.length - selectedCaps.length})
                </span>
                <p className="text-[11px] text-zinc-400 mt-1">
                  Actions not explicitly granted above are strictly denied by the runtime.
                </p>
              </div>

              <div className="pt-2 border-t border-zinc-900">
                <span className="text-zinc-500 block font-mono text-[10px] uppercase">
                  Runtime Bounds
                </span>
                <ul className="space-y-1 mt-1 font-mono text-[11px] text-zinc-300">
                  <li>• Max Steps: {maxSteps}</li>
                  <li>• Max Cost: ${Number(maxCost).toFixed(2)}</li>
                  <li>• Delegation Depth Limit: 2 (Hard Invariant)</li>
                  <li>• Cross-Tenant Access: Strictly Denied</li>
                </ul>
              </div>

              <div className="pt-2 border-t border-zinc-900">
                <span className="text-zinc-500 block font-mono text-[10px] uppercase">
                  Safety Invariant
                </span>
                <p className="text-[11px] text-zinc-400 mt-1 leading-relaxed">
                  Agents execute under strict principal isolation. They can never approve their own actions, modify their own policy, or impersonate human operators.
                </p>
              </div>
            </div>
          </Card>
        </div>
      </form>
    </div>
  );
}
