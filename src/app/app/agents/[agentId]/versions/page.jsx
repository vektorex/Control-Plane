"use client";

import React, { useState, useEffect, use } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { agentService } from "@/services/agents";
import { useWorkspace } from "@/lib/workspaceContext";
import {
  ArrowLeft,
  Bot,
  History,
  ShieldCheck,
  Cpu,
  Sparkles,
  Lock,
  Clock,
  Layers,
  CheckCircle2,
} from "lucide-react";

export default function AgentVersionsPage({ params }) {
  const unwrappedParams = use(params);
  const { agentId } = unwrappedParams;
  const { activeWorkspace } = useWorkspace();

  const [agent, setAgent] = useState(null);
  const [versions, setVersions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        const [ag, vers] = await Promise.all([
          agentService.getAgent(agentId),
          agentService.listAgentVersions(agentId),
        ]);
        setAgent(ag);
        setVersions(Array.isArray(vers) ? vers : []);
      } catch (err) {
        console.error("Failed to load agent versions:", err);
        setError(err.message || "Failed to load agent versions");
      } finally {
        setLoading(false);
      }
    };
    if (agentId) {
      loadData();
    }
  }, [agentId, activeWorkspace]);

  if (loading) {
    return (
      <div className="space-y-4 animate-pulse">
        <div className="h-16 rounded-xl bg-zinc-900 border border-zinc-800" />
        <div className="h-64 rounded-xl bg-zinc-900 border border-zinc-800" />
      </div>
    );
  }

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div className="flex items-center gap-3 border-b border-zinc-800/80 pb-5">
        <Link
          href={`/app/agents/${agentId}`}
          className="p-2 rounded-lg bg-zinc-900 hover:bg-zinc-800 text-zinc-400 hover:text-zinc-200 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
        </Link>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-zinc-100">{agent?.name} — Version History</h1>
            <Badge variant="outline" className="text-[10px] text-purple-400 border-purple-500/30">
              Immutable Records
            </Badge>
          </div>
          <p className="text-xs text-zinc-400 mt-0.5">
            Published versions are immutable. Once published, instructions, model parameters, and capability policies cannot be modified.
          </p>
        </div>
      </div>

      {versions.length === 0 ? (
        <div className="p-12 text-center rounded-2xl border border-zinc-800 bg-zinc-950/40 text-zinc-500 text-xs">
          No published version snapshots recorded yet.
        </div>
      ) : (
        <div className="space-y-4">
          {versions.map((ver) => {
            const isCurrent = agent?.current_version_id === ver.id;
            return (
              <Card
                key={ver.id}
                className={`p-6 border-zinc-800 bg-zinc-950/70 space-y-4 transition-all ${
                  isCurrent ? "border-purple-500/40 shadow-lg shadow-purple-900/10" : ""
                }`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-center gap-2.5">
                    <div className="p-2 rounded-lg bg-purple-500/10 border border-purple-500/20 text-purple-400">
                      <Lock className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-semibold text-zinc-200">
                          Version {ver.version}
                        </span>
                        {isCurrent && (
                          <Badge variant="success" className="text-[10px]">
                            Current Active
                          </Badge>
                        )}
                        {ver.published_at && (
                          <Badge variant="outline" className="text-[10px] text-zinc-400 border-zinc-800">
                            Published
                          </Badge>
                        )}
                      </div>
                      <span className="text-[10px] text-zinc-500 font-mono">ID: {ver.id}</span>
                    </div>
                  </div>

                  <span className="text-xs text-zinc-500 font-mono">
                    Created: {new Date(ver.created_at).toLocaleDateString()}
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                  {/* Capabilities */}
                  <div className="p-3.5 rounded-lg bg-zinc-900/60 border border-zinc-800/80 space-y-2">
                    <span className="font-semibold text-zinc-400 uppercase tracking-wider block text-[10px] flex items-center gap-1.5">
                      <ShieldCheck className="w-3.5 h-3.5 text-purple-400" />
                      Granted Capabilities ({ver.capability_policy?.length || 0})
                    </span>
                    <div className="flex flex-wrap gap-1">
                      {(ver.capability_policy || []).map((c) => (
                        <span
                          key={c}
                          className="px-2 py-0.5 rounded bg-purple-500/10 text-purple-300 font-mono text-[10px] border border-purple-500/20"
                        >
                          {c}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Model Policy */}
                  <div className="p-3.5 rounded-lg bg-zinc-900/60 border border-zinc-800/80 space-y-1.5 font-mono text-zinc-300">
                    <span className="font-semibold text-zinc-400 uppercase tracking-wider block text-[10px] flex items-center gap-1.5 font-sans">
                      <Cpu className="w-3.5 h-3.5 text-purple-400" />
                      Model Configuration
                    </span>
                    <div>Preferred: {ver.model_policy?.preferred_model || "gpt-4o-mini"}</div>
                    <div>Temp: {ver.model_policy?.temperature ?? 0.2}</div>
                    <div>Max Tokens: {ver.model_policy?.max_output_tokens || 2048}</div>
                  </div>
                </div>

                {/* Instructions snippet */}
                <div className="space-y-1.5">
                  <span className="text-[11px] font-semibold text-zinc-400 uppercase tracking-wider block">
                    System Instructions
                  </span>
                  <pre className="p-3 rounded-lg bg-zinc-900/90 border border-zinc-800 text-xs font-mono text-zinc-300 whitespace-pre-wrap max-h-36 overflow-y-auto">
                    {ver.instructions}
                  </pre>
                </div>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
