"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Input } from "@/components/ui/Input";
import { agentService } from "@/services/agents";
import { useWorkspace } from "@/lib/workspaceContext";
import {
  Boxes,
  ArrowLeft,
  Plus,
  Trash2,
  Users2,
  ShieldCheck,
  AlertTriangle,
  Sparkles,
  Bot,
  Sliders,
  CheckCircle2,
} from "lucide-react";

const TEAM_ROLES = [
  { value: "lead", label: "Lead (Coordinator)", desc: "Plans execution and directs specialist handoffs" },
  { value: "researcher", label: "Researcher", desc: "Retrieves evidence from knowledge & documents" },
  { value: "analyst", label: "Analyst", desc: "Evaluates findings and correlates structured data" },
  { value: "builder", label: "Builder", desc: "Constructs drafts and workflows" },
  { value: "reviewer", label: "Reviewer", desc: "Validates policy compliance and peer checks outputs" },
  { value: "specialist", label: "Specialist", desc: "Domain-specific execution and tool usage" },
  { value: "executor", label: "Executor", desc: "Performs bounded actions and state changes" },
];

export default function NewAgentTeamPage() {
  const router = useRouter();
  const { activeWorkspace } = useWorkspace();

  const [availableAgents, setAvailableAgents] = useState([]);
  const [loadingAgents, setLoadingAgents] = useState(true);

  // Form State
  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [description, setDescription] = useState("");
  const [objective, setObjective] = useState(
    "Coordinate research, policy review, and factual synthesis across team members with mandatory verification."
  );

  const [members, setMembers] = useState([
    {
      agent_id: "",
      role: "lead",
      responsibilities: "Coordinate team plan, assign steps, and summarize findings.",
      limits: { max_steps: 10, max_cost: 0.5 },
    },
    {
      agent_id: "",
      role: "reviewer",
      responsibilities: "Verify evidence, detect contradictions, and audit compliance.",
      limits: { max_steps: 5, max_cost: 0.25 },
    },
  ]);

  const [coordinationMode, setCoordinationMode] = useState("hierarchical");
  const [maxParallelAgents, setMaxParallelAgents] = useState(3);
  const [allowCrossMessaging, setAllowCrossMessaging] = useState(true);
  const [requireHumanApproval, setRequireHumanApproval] = useState(false);

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadAgents = async () => {
      try {
        setLoadingAgents(true);
        const data = await agentService.listAgents({ status: "active" });
        const list = Array.isArray(data) ? data : [];
        setAvailableAgents(list);

        // Pre-select first two agents if available
        if (list.length >= 2) {
          setMembers((prev) => [
            { ...prev[0], agent_id: list[0].id },
            { ...prev[1], agent_id: list[1].id },
          ]);
        } else if (list.length === 1) {
          setMembers((prev) => [
            { ...prev[0], agent_id: list[0].id },
            { ...prev[1], agent_id: "" },
          ]);
        }
      } catch (err) {
        console.error("Failed to load active agents:", err);
      } finally {
        setLoadingAgents(false);
      }
    };
    loadAgents();
  }, [activeWorkspace]);

  const handleNameChange = (val) => {
    setName(val);
    if (!slug || slug === name.toLowerCase().replace(/[^a-z0-9]+/g, "-")) {
      setSlug(val.toLowerCase().replace(/[^a-z0-9]+/g, "-"));
    }
  };

  const handleAddMember = () => {
    const unpicked = availableAgents.find(
      (a) => !members.some((m) => m.agent_id === a.id)
    );
    setMembers([
      ...members,
      {
        agent_id: unpicked ? unpicked.id : "",
        role: "specialist",
        responsibilities: "Perform domain-specific analysis.",
        limits: { max_steps: 5, max_cost: 0.25 },
      },
    ]);
  };

  const handleRemoveMember = (idx) => {
    if (members.length <= 1) return;
    setMembers(members.filter((_, i) => i !== idx));
  };

  const handleUpdateMember = (idx, field, val) => {
    const updated = [...members];
    updated[idx] = { ...updated[idx], [field]: val };
    setMembers(updated);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!name.trim()) {
      setError("Team name is required.");
      return;
    }
    if (!objective.trim()) {
      setError("Team objective is required.");
      return;
    }

    // Validation
    const emptyAgents = members.some((m) => !m.agent_id);
    if (emptyAgents) {
      setError("Please select an agent for all team member slots.");
      return;
    }

    const agentIds = members.map((m) => m.agent_id);
    if (new Set(agentIds).size !== agentIds.length) {
      setError("Duplicate agents are not allowed in the same team. Each role must be an independent agent.");
      return;
    }

    try {
      setSubmitting(true);
      setError(null);

      const payload = {
        name: name.trim(),
        slug: slug.trim() || name.toLowerCase().replace(/[^a-z0-9]+/g, "-"),
        description: description.trim() || undefined,
        objective: objective.trim(),
        members: members.map((m) => {
          const matchedAgent = availableAgents.find((a) => a.id === m.agent_id);
          return {
            agent_id: m.agent_id,
            agent_version_id: matchedAgent?.current_version_id,
            role: m.role,
            capabilities: matchedAgent?.current_version?.capability_policy || [],
            responsibilities: m.responsibilities,
            limits: m.limits,
          };
        }),
        coordination_policy: {
          mode: coordinationMode,
          max_parallel_agents: maxParallelAgents,
          allow_cross_messaging: allowCrossMessaging,
        },
        shared_context_policy: {
          share_artifacts: true,
          share_evidence: true,
        },
        approval_policy: {
          require_human_approval_for_synthesis: requireHumanApproval,
        },
      };

      const team = await agentService.createTeam(payload);
      router.push(`/app/agent-teams/${team.id}`);
    } catch (err) {
      console.error("[NewAgentTeam] Creation failed:", err);
      setError(err.message || "Failed to create agent team");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6 pb-12">
      {/* Header */}
      <div className="flex items-center gap-3 border-b border-zinc-800/80 pb-5">
        <Link
          href="/app/agent-teams"
          className="p-2 rounded-lg bg-zinc-900 hover:bg-zinc-800 text-zinc-400 hover:text-zinc-200 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
        </Link>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-zinc-100">Team Builder</h1>
            <Badge variant="outline" className="text-[10px] text-purple-400 border-purple-500/30">
              Multi-Agent
            </Badge>
          </div>
          <p className="text-xs text-zinc-400 mt-0.5">
            Configure collaborative agent teams with bounded roles, cross-agent message policies, and shared context.
          </p>
        </div>
      </div>

      {error && (
        <div className="p-3.5 rounded-xl border border-red-500/20 bg-red-500/10 text-red-300 text-xs flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-red-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {availableAgents.length === 0 && !loadingAgents && (
        <div className="p-4 rounded-xl border border-amber-500/20 bg-amber-500/10 text-amber-300 text-xs flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
            <span>No active agents available. You must create and activate at least one agent before assembling a team.</span>
          </div>
          <Link href="/app/agents/new">
            <Button size="sm" variant="outline" className="text-amber-300 border-amber-500/30 hover:bg-amber-500/20 text-xs">
              Create Agent
            </Button>
          </Link>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Section 1: Team Identity & Objective */}
        <Card className="p-6 border-zinc-800 bg-zinc-950/70 space-y-4">
          <h2 className="text-sm font-semibold text-zinc-200 flex items-center gap-2">
            <Boxes className="w-4 h-4 text-purple-400" />
            <span>1. Team Identity & Core Objective</span>
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-zinc-300">Team Name *</label>
              <Input
                value={name}
                onChange={(e) => handleNameChange(e.target.value)}
                placeholder="e.g. Research & Verification Squad"
                className="text-xs bg-zinc-900 border-zinc-800 text-zinc-200"
                required
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-medium text-zinc-300">Slug</label>
              <Input
                value={slug}
                onChange={(e) => setSlug(e.target.value)}
                placeholder="e.g. research-verification-squad"
                className="text-xs bg-zinc-900 border-zinc-800 text-zinc-200 font-mono"
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-medium text-zinc-300">Description</label>
            <Input
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Brief description of the team's specialization..."
              className="text-xs bg-zinc-900 border-zinc-800 text-zinc-200"
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-medium text-zinc-300">Primary Objective *</label>
            <textarea
              value={objective}
              onChange={(e) => setObjective(e.target.value)}
              rows={3}
              placeholder="State the bounded objective and deliverables the team is responsible for..."
              className="w-full text-xs bg-zinc-900 border border-zinc-800 rounded-lg p-3 text-zinc-200 focus:outline-none focus:border-purple-500"
              required
            />
          </div>
        </Card>

        {/* Section 2: Team Members & Roles */}
        <Card className="p-6 border-zinc-800 bg-zinc-950/70 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-zinc-200 flex items-center gap-2">
              <Users2 className="w-4 h-4 text-purple-400" />
              <span>2. Member Agents & Assigned Roles</span>
            </h2>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={handleAddMember}
              className="border-zinc-800 text-zinc-300 hover:text-zinc-100 gap-1.5 text-xs"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Add Member</span>
            </Button>
          </div>

          <p className="text-xs text-zinc-400">
            Roles dictate coordination behavior, not privilege. Actual authority is strictly bounded by each agent's immutable policy.
          </p>

          <div className="space-y-4">
            {members.map((member, idx) => (
              <div
                key={idx}
                className="p-4 rounded-xl border border-zinc-800/80 bg-zinc-900/40 space-y-3 relative group"
              >
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
                  <div className="flex items-center gap-2 w-full sm:w-auto">
                    <span className="w-5 h-5 rounded-full bg-purple-500/20 text-purple-400 font-mono text-[10px] flex items-center justify-center font-bold">
                      {idx + 1}
                    </span>
                    <span className="text-xs font-medium text-zinc-300">Member Role:</span>
                    <select
                      value={member.role}
                      onChange={(e) => handleUpdateMember(idx, "role", e.target.value)}
                      className="text-xs bg-zinc-900 border border-zinc-800 rounded px-2.5 py-1 text-zinc-200 focus:outline-none focus:border-purple-500 font-medium capitalize"
                    >
                      {TEAM_ROLES.map((r) => (
                        <option key={r.value} value={r.value}>
                          {r.label}
                        </option>
                      ))}
                    </select>
                  </div>

                  {members.length > 1 && (
                    <button
                      type="button"
                      onClick={() => handleRemoveMember(idx)}
                      className="text-zinc-500 hover:text-red-400 transition-colors p-1"
                      title="Remove member"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <label className="text-[11px] font-medium text-zinc-400">Select Active Agent</label>
                    <select
                      value={member.agent_id}
                      onChange={(e) => handleUpdateMember(idx, "agent_id", e.target.value)}
                      className="w-full text-xs bg-zinc-900 border border-zinc-800 rounded-lg p-2 text-zinc-200 focus:outline-none focus:border-purple-500"
                      required
                    >
                      <option value="">-- Choose an agent --</option>
                      {availableAgents.map((ag) => (
                        <option key={ag.id} value={ag.id}>
                          {ag.name} ({ag.status}) - v{ag.current_version?.version || 1}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="space-y-1">
                    <label className="text-[11px] font-medium text-zinc-400">Responsibilities</label>
                    <Input
                      value={member.responsibilities}
                      onChange={(e) => handleUpdateMember(idx, "responsibilities", e.target.value)}
                      placeholder="e.g. Conduct literature review and summarize findings..."
                      className="text-xs bg-zinc-900 border-zinc-800 text-zinc-200"
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* Section 3: Coordination & Governance Policies */}
        <Card className="p-6 border-zinc-800 bg-zinc-950/70 space-y-4">
          <h2 className="text-sm font-semibold text-zinc-200 flex items-center gap-2">
            <Sliders className="w-4 h-4 text-purple-400" />
            <span>3. Coordination & Governance Policies</span>
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-zinc-300">Coordination Mode</label>
              <select
                value={coordinationMode}
                onChange={(e) => setCoordinationMode(e.target.value)}
                className="w-full text-xs bg-zinc-900 border border-zinc-800 rounded-lg p-2 text-zinc-200 focus:outline-none focus:border-purple-500"
              >
                <option value="hierarchical">Hierarchical (Lead coordinates specialized stages)</option>
                <option value="sequential">Sequential Pipeline (A → B → C handoffs)</option>
                <option value="parallel_synthesis">Parallel Investigation with Final Synthesis</option>
              </select>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-medium text-zinc-300">Max Concurrent Parallel Agents</label>
              <Input
                type="number"
                min={1}
                max={5}
                value={maxParallelAgents}
                onChange={(e) => setMaxParallelAgents(parseInt(e.target.value) || 1)}
                className="text-xs bg-zinc-900 border-zinc-800 text-zinc-200 font-mono"
              />
            </div>
          </div>

          <div className="pt-2 space-y-2.5">
            <label className="flex items-center gap-2 cursor-pointer text-xs text-zinc-300">
              <input
                type="checkbox"
                checked={allowCrossMessaging}
                onChange={(e) => setAllowCrossMessaging(e.target.checked)}
                className="rounded border-zinc-700 bg-zinc-900 text-purple-600 focus:ring-purple-500"
              />
              <span>Enable peer-to-peer data context sharing (AgentMessage log)</span>
            </label>

            <label className="flex items-center gap-2 cursor-pointer text-xs text-zinc-300">
              <input
                type="checkbox"
                checked={requireHumanApproval}
                onChange={(e) => setRequireHumanApproval(e.target.checked)}
                className="rounded border-zinc-700 bg-zinc-900 text-purple-600 focus:ring-purple-500"
              />
              <span>Require Human-in-the-Loop (HITL) approval before finalizing team synthesis</span>
            </label>
          </div>
        </Card>

        {/* Submit */}
        <div className="flex items-center justify-end gap-3 pt-3">
          <Link href="/app/agent-teams">
            <Button variant="outline" type="button" className="border-zinc-800 text-zinc-400">
              Cancel
            </Button>
          </Link>
          <Button
            type="submit"
            disabled={submitting || availableAgents.length === 0}
            className="bg-purple-600 hover:bg-purple-500 text-white gap-1.5"
          >
            <CheckCircle2 className="w-4 h-4" />
            <span>{submitting ? "Assembling Team..." : "Create & Activate Team"}</span>
          </Button>
        </div>
      </form>
    </div>
  );
}
