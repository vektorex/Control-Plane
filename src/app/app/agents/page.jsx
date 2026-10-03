"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Input } from "@/components/ui/Input";
import { StatCard } from "@/components/ui/StatCard";
import { agentService } from "@/services/agents";
import { useWorkspace } from "@/lib/workspaceContext";
import { AgentIdentityBadge } from "@/components/agents/AgentIdentityBadge";
import {
  Bot,
  Plus,
  Play,
  Search,
  RefreshCw,
  Clock,
  ShieldCheck,
  AlertCircle,
  ArrowRight,
  Boxes,
  Zap,
} from "lucide-react";

export default function AgentsPage() {
  const router = useRouter();
  const { activeWorkspace } = useWorkspace();

  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [error, setError] = useState(null);

  const fetchAgents = async () => {
    try {
      setLoading(true);
      setError(null);
      const params = statusFilter !== "ALL" ? { status: statusFilter.toLowerCase() } : {};
      const data = await agentService.listAgents(params);
      setAgents(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error("[AgentsPage] Error fetching agents:", err);
      setError(err.message || "Failed to load agents");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAgents();
  }, [activeWorkspace, statusFilter]);

  const filteredAgents = agents.filter((ag) => {
    const q = searchQuery.toLowerCase();
    return (
      ag.name.toLowerCase().includes(q) ||
      ag.slug.toLowerCase().includes(q) ||
      ag.purpose.toLowerCase().includes(q)
    );
  });

  const totalAgents = agents.length;
  const activeCount = agents.filter((a) => a.status === "active").length;
  const draftCount = agents.filter((a) => a.status === "draft").length;
  const pausedCount = agents.filter((a) => a.status === "paused").length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Bot className="w-7 h-7 text-purple-400" />
            <h1 className="text-2xl font-bold tracking-tight text-zinc-100">AI Agents</h1>
          </div>
          <p className="text-sm text-zinc-400 mt-1">
            Governed autonomous agents with bounded policies, capability constraints, and human oversight.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Link href="/app/agent-teams">
            <Button variant="outline" size="sm" className="gap-2 border-zinc-800">
              <Boxes className="w-4 h-4 text-purple-400" />
              <span>Agent Teams</span>
            </Button>
          </Link>
          <Link href="/app/agents/new">
            <Button size="sm" className="gap-2 bg-purple-600 hover:bg-purple-500 text-white">
              <Plus className="w-4 h-4" />
              <span>Create Agent</span>
            </Button>
          </Link>
        </div>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard title="Total Agents" value={totalAgents} icon={Bot} />
        <StatCard title="Active Principals" value={activeCount} icon={ShieldCheck} />
        <StatCard title="Drafts" value={draftCount} icon={Clock} />
        <StatCard title="Paused" value={pausedCount} icon={Zap} />
      </div>

      {/* Filter / Search Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 bg-zinc-900/40 p-3 rounded-xl border border-zinc-800/80">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 text-zinc-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <Input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search agents by name or purpose..."
            className="pl-9 bg-zinc-950/60 border-zinc-800 text-xs"
          />
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto overflow-x-auto">
          {["ALL", "ACTIVE", "DRAFT", "PAUSED", "DISABLED"].map((st) => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                statusFilter === st
                  ? "bg-purple-600/20 text-purple-300 border border-purple-500/40"
                  : "bg-zinc-900/60 text-zinc-400 hover:text-zinc-200 border border-transparent"
              }`}
            >
              {st}
            </button>
          ))}
          <Button variant="ghost" size="icon" onClick={fetchAgents} disabled={loading}>
            <RefreshCw className={`w-4 h-4 text-zinc-400 ${loading ? "animate-spin" : ""}`} />
          </Button>
        </div>
      </div>

      {/* Error state */}
      {error && (
        <div className="p-4 rounded-xl border border-rose-500/30 bg-rose-500/10 text-rose-300 text-sm flex items-center gap-2">
          <AlertCircle className="w-5 h-5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Agents Grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-44 rounded-xl border border-zinc-800/80 bg-zinc-900/30 animate-pulse" />
          ))}
        </div>
      ) : filteredAgents.length === 0 ? (
        <div className="p-12 text-center rounded-2xl border border-zinc-800 bg-zinc-950/40 space-y-3">
          <Bot className="w-10 h-10 text-zinc-600 mx-auto" />
          <h3 className="text-base font-semibold text-zinc-200">No agents found</h3>
          <p className="text-xs text-zinc-400 max-w-sm mx-auto">
            Get started by creating your first governed AI Agent with custom purpose, model policy, and explicit capabilities.
          </p>
          <Link href="/app/agents/new">
            <Button size="sm" className="mt-2 bg-purple-600 hover:bg-purple-500 text-white gap-2">
              <Plus className="w-4 h-4" />
              <span>Create Agent</span>
            </Button>
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredAgents.map((ag) => (
            <Card
              key={ag.id}
              className="p-5 border-zinc-800/80 bg-zinc-950/70 hover:border-purple-500/40 hover:bg-zinc-900/30 transition-all flex flex-col justify-between group"
            >
              <div className="space-y-3">
                <div className="flex items-start justify-between gap-2">
                  <div className="space-y-1">
                    <h3 className="text-sm font-bold text-zinc-100 group-hover:text-purple-300 transition-colors">
                      {ag.name}
                    </h3>
                    <span className="text-[11px] font-mono text-zinc-500 block">
                      slug: {ag.slug}
                    </span>
                  </div>
                  <Badge
                    variant={
                      ag.status === "active"
                        ? "success"
                        : ag.status === "paused"
                        ? "warning"
                        : "default"
                    }
                    className="capitalize text-[10px]"
                  >
                    {ag.status}
                  </Badge>
                </div>

                <p className="text-xs text-zinc-400 line-clamp-2 leading-relaxed">
                  {ag.purpose}
                </p>

                <div className="pt-2">
                  <AgentIdentityBadge type="ai_agent" />
                </div>
              </div>

              <div className="pt-4 border-t border-zinc-900 mt-4 flex items-center justify-between">
                <span className="text-[10px] text-zinc-500 font-mono">
                  Updated: {new Date(ag.updated_at).toLocaleDateString()}
                </span>
                <Link
                  href={`/app/agents/${ag.id}`}
                  className="text-xs font-semibold text-purple-400 hover:text-purple-300 flex items-center gap-1 group-hover:translate-x-0.5 transition-transform"
                >
                  <span>Configure</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
