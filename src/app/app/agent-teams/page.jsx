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
import {
  Boxes,
  Plus,
  Play,
  Search,
  RefreshCw,
  Clock,
  ShieldCheck,
  AlertCircle,
  ArrowRight,
  Bot,
  Users2,
  Sparkles,
} from "lucide-react";

export default function AgentTeamsPage() {
  const router = useRouter();
  const { activeWorkspace } = useWorkspace();

  const [teams, setTeams] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [error, setError] = useState(null);

  const fetchTeams = async () => {
    try {
      setLoading(true);
      setError(null);
      const params = statusFilter !== "ALL" ? { status: statusFilter.toLowerCase() } : {};
      const data = await agentService.listTeams(params);
      setTeams(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error("[AgentTeamsPage] Error fetching teams:", err);
      setError(err.message || "Failed to load multi-agent teams");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTeams();
  }, [activeWorkspace, statusFilter]);

  const filteredTeams = teams.filter((t) => {
    const q = searchQuery.toLowerCase();
    return (
      t.name.toLowerCase().includes(q) ||
      (t.description && t.description.toLowerCase().includes(q)) ||
      (t.slug && t.slug.toLowerCase().includes(q))
    );
  });

  const activeCount = teams.filter((t) => t.status === "active").length;
  const draftCount = teams.filter((t) => t.status === "draft").length;
  const pausedCount = teams.filter((t) => t.status === "paused").length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-zinc-800/80 pb-5">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-purple-500/10 border border-purple-500/20 text-purple-400">
              <Boxes className="w-5 h-5" />
            </div>
            <h1 className="text-xl font-bold text-zinc-100 tracking-tight">
              Multi-Agent Teams
            </h1>
            <Badge variant="outline" className="text-[10px] text-zinc-400 border-zinc-800">
              STEP 40
            </Badge>
          </div>
          <p className="text-xs text-zinc-400 mt-1">
            Governed co-execution of specialized agent roles (lead, researcher, analyst, reviewer, executor) with bounded delegation, shared context, and conflict arbitration.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={fetchTeams}
            disabled={loading}
            className="border-zinc-800 text-zinc-400 hover:text-zinc-200"
          >
            <RefreshCw className={`w-3.5 h-3.5 mr-1.5 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </Button>
          <Link href="/app/agent-teams/new">
            <Button size="sm" className="bg-purple-600 hover:bg-purple-500 text-white gap-1.5">
              <Plus className="w-3.5 h-3.5" />
              <span>Create Team</span>
            </Button>
          </Link>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Teams"
          value={teams.length}
          icon={<Boxes className="w-4 h-4 text-purple-400" />}
          description="Tenant-bounded teams"
        />
        <StatCard
          title="Active Teams"
          value={activeCount}
          icon={<Sparkles className="w-4 h-4 text-emerald-400" />}
          description="Ready for coordinated runs"
        />
        <StatCard
          title="Draft Teams"
          value={draftCount}
          icon={<Clock className="w-4 h-4 text-amber-400" />}
          description="In policy configuration"
        />
        <StatCard
          title="Paused / Inactive"
          value={pausedCount}
          icon={<AlertCircle className="w-4 h-4 text-zinc-400" />}
          description="Suspended execution"
        />
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 p-3 rounded-xl border border-zinc-800 bg-zinc-950/70">
        <div className="relative w-full sm:w-80">
          <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" />
          <Input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search teams by name or description..."
            className="pl-9 h-8 text-xs bg-zinc-900 border-zinc-800 text-zinc-200 placeholder:text-zinc-500"
          />
        </div>

        <div className="flex items-center gap-1.5 w-full sm:w-auto overflow-x-auto">
          {["ALL", "ACTIVE", "DRAFT", "PAUSED", "DISABLED"].map((status) => (
            <button
              key={status}
              onClick={() => setStatusFilter(status)}
              className={`px-2.5 py-1 text-xs rounded-lg transition-colors capitalize ${
                statusFilter === status
                  ? "bg-purple-600/20 text-purple-300 border border-purple-500/30"
                  : "text-zinc-400 hover:text-zinc-200 border border-transparent"
              }`}
            >
              {status.toLowerCase()}
            </button>
          ))}
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="p-3 rounded-xl border border-red-500/20 bg-red-500/10 text-red-300 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Teams Grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="h-44 rounded-xl border border-zinc-800 bg-zinc-950/40 animate-pulse"
            />
          ))}
        </div>
      ) : filteredTeams.length === 0 ? (
        <div className="text-center py-16 px-4 rounded-2xl border border-zinc-800/80 bg-zinc-950/40">
          <div className="w-12 h-12 rounded-2xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center mx-auto text-purple-400 mb-3">
            <Boxes className="w-6 h-6" />
          </div>
          <h3 className="text-sm font-semibold text-zinc-200">No multi-agent teams found</h3>
          <p className="text-xs text-zinc-500 mt-1 max-w-sm mx-auto">
            {searchQuery
              ? "No teams match your search criteria. Try a different filter."
              : "Assemble specialized agents into coordinated teams with bounded responsibilities and peer review."}
          </p>
          <div className="mt-5">
            <Link href="/app/agent-teams/new">
              <Button size="sm" className="bg-purple-600 hover:bg-purple-500 text-white gap-1.5">
                <Plus className="w-3.5 h-3.5" />
                <span>Create First Team</span>
              </Button>
            </Link>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredTeams.map((team) => (
            <Card
              key={team.id}
              className="p-5 border-zinc-800 bg-zinc-950/80 hover:border-zinc-700/80 transition-all flex flex-col justify-between group"
            >
              <div>
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-center gap-2.5">
                    <div className="w-9 h-9 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400 shrink-0">
                      <Users2 className="w-4 h-4" />
                    </div>
                    <div>
                      <h3 className="text-sm font-semibold text-zinc-200 group-hover:text-purple-300 transition-colors">
                        {team.name}
                      </h3>
                      <span className="text-[10px] text-zinc-500 font-mono">
                        slug: {team.slug}
                      </span>
                    </div>
                  </div>
                  <Badge
                    variant={
                      team.status === "active"
                        ? "success"
                        : team.status === "paused"
                        ? "warning"
                        : "default"
                    }
                    className="capitalize text-[10px]"
                  >
                    {team.status}
                  </Badge>
                </div>

                <p className="text-xs text-zinc-400 mt-3 line-clamp-2">
                  {team.description || "No description provided."}
                </p>

                {/* Team metadata pill */}
                <div className="mt-4 pt-3 border-t border-zinc-900 flex items-center justify-between text-[11px] text-zinc-500 font-mono">
                  <span>Members: {team.members?.length || 0}</span>
                  <span>Version: v{team.current_version?.version || 1}</span>
                </div>
              </div>

              <div className="mt-4 pt-3 border-t border-zinc-800/80 flex items-center justify-between">
                <span className="text-[10px] text-zinc-500 font-mono">
                  {new Date(team.created_at).toLocaleDateString()}
                </span>
                <Link
                  href={`/app/agent-teams/${team.id}`}
                  className="inline-flex items-center gap-1 text-xs text-purple-400 hover:text-purple-300 font-medium transition-colors"
                >
                  <span>Manage Team</span>
                  <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
                </Link>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
