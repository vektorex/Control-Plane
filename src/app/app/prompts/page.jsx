"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import {
  FileCode2,
  Plus,
  Search,
  Sparkles,
  GitBranch,
  ShieldCheck,
  FlaskConical,
  RefreshCw,
  ExternalLink,
  Layers,
  Copy,
  Check,
} from "lucide-react";
import { promptService } from "@/services/prompts";
import { StatCard } from "@/components/ui/StatCard";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";

const PROMPT_TYPES = [
  "all",
  "task",
  "planner",
  "evaluator",
  "workflow",
  "system",
  "instruction",
  "transform",
];

export default function PromptsPage() {
  const [prompts, setPrompts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedType, setSelectedType] = useState("all");
  const [selectedStatus, setSelectedStatus] = useState("active");
  const [seeding, setSeeding] = useState(false);
  const [copiedKey, setCopiedKey] = useState(null);

  const fetchPrompts = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await promptService.listPrompts({
        status: selectedStatus,
        ...(selectedType !== "all" ? { prompt_type: selectedType } : {}),
      });
      setPrompts(res || []);
    } catch (err) {
      console.error("Failed to fetch prompts:", err);
      setError(err.message || "Failed to load prompts");
    } finally {
      setLoading(false);
    }
  }, [selectedStatus, selectedType]);

  useEffect(() => {
    fetchPrompts();
  }, [fetchPrompts]);

  const handleSeed = async () => {
    try {
      setSeeding(true);
      // Retrieve active workspace ID from localStorage if available
      const storedWorkspace = localStorage.getItem("active_workspace_id");
      await promptService.seedPrompts(storedWorkspace || "00000000-0000-0000-0000-000000000001");
      await fetchPrompts();
    } catch (err) {
      alert(`Seeding failed: ${err.message}`);
    } finally {
      setSeeding(false);
    }
  };

  const handleCopyKey = (key, e) => {
    e.preventDefault();
    e.stopPropagation();
    navigator.clipboard.writeText(key);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  // Filtered prompts
  const filteredPrompts = prompts.filter((p) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      p.name?.toLowerCase().includes(q) ||
      p.key?.toLowerCase().includes(q) ||
      p.description?.toLowerCase().includes(q)
    );
  });

  // Calculate metrics
  const totalCount = prompts.length;
  const prodReleases = prompts.filter((p) => p.production_version).length;
  const stagingReleases = prompts.filter((p) => p.staging_version).length;
  const hasDrafts = prompts.filter((p) => p.latest_version?.status === "draft").length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
              <FileCode2 className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white flex items-center gap-2">
                Prompt Registry
                <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 border border-slate-700 font-normal">
                  STEP 28
                </span>
              </h1>
              <p className="text-xs text-slate-400">
                Governed, versioned, reusable AI prompt assets with immutable environments and safe rendering.
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            variant="outline"
            size="sm"
            onClick={handleSeed}
            disabled={seeding}
            className="flex items-center gap-1.5 text-xs text-slate-300 hover:text-white border-slate-700 bg-slate-900/50"
          >
            <Sparkles className={`w-3.5 h-3.5 text-amber-400 ${seeding ? "animate-spin" : ""}`} />
            {seeding ? "Seeding..." : "Seed Built-in Prompts"}
          </Button>

          <Link href="/app/prompts/new">
            <Button size="sm" className="flex items-center gap-1.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs">
              <Plus className="w-3.5 h-3.5" />
              New Prompt
            </Button>
          </Link>
        </div>
      </div>

      {/* Metrics Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Registered Prompts"
          value={totalCount}
          icon={FileCode2}
          subtext="Total governed assets"
        />
        <StatCard
          label="Production Releases"
          value={prodReleases}
          icon={ShieldCheck}
          subtext="Live production versions"
        />
        <StatCard
          label="Staging Releases"
          value={stagingReleases}
          icon={GitBranch}
          subtext="Active pre-production"
        />
        <StatCard
          label="Draft Iterations"
          value={hasDrafts}
          icon={Layers}
          subtext="Unpublished revisions"
        />
      </div>

      {/* Filters & Search */}
      <div className="flex flex-col md:flex-row gap-3 items-center justify-between bg-slate-900/40 p-3 rounded-xl border border-slate-800">
        <div className="flex flex-1 items-center gap-2 w-full md:w-auto">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-2.5 w-4 h-4 text-slate-500" />
            <input
              type="text"
              placeholder="Search prompts by key, name, or description..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-4 py-1.5 text-xs bg-slate-950 border border-slate-800 rounded-lg text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
            />
          </div>

          <button
            onClick={fetchPrompts}
            disabled={loading}
            className="p-1.5 rounded-lg border border-slate-800 bg-slate-950 text-slate-400 hover:text-white"
            title="Refresh"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          </button>
        </div>

        <div className="flex items-center gap-2 w-full md:w-auto overflow-x-auto">
          <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-lg border border-slate-800">
            {PROMPT_TYPES.map((type) => (
              <button
                key={type}
                onClick={() => setSelectedType(type)}
                className={`px-2.5 py-1 text-[11px] font-medium rounded capitalize transition-all ${
                  selectedType === type
                    ? "bg-indigo-600 text-white"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                {type}
              </button>
            ))}
          </div>

          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className="text-xs bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-slate-300 focus:outline-none"
          >
            <option value="active">Active</option>
            <option value="archived">Archived</option>
          </select>
        </div>
      </div>

      {/* Prompts Table */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/30 overflow-hidden">
        {loading ? (
          <div className="py-16 text-center text-slate-500 text-xs flex items-center justify-center gap-2">
            <RefreshCw className="w-4 h-4 animate-spin text-indigo-400" />
            Loading prompt registry...
          </div>
        ) : error ? (
          <div className="py-12 text-center text-rose-400 text-xs">
            {error}
          </div>
        ) : filteredPrompts.length === 0 ? (
          <div className="py-16 text-center space-y-3">
            <FileCode2 className="w-10 h-10 text-slate-600 mx-auto" />
            <h3 className="text-sm font-semibold text-slate-300">No prompts found</h3>
            <p className="text-xs text-slate-500 max-w-sm mx-auto">
              Get started by seeding the standard system prompts or creating your own governed prompt template.
            </p>
            <div className="pt-2 flex justify-center gap-2">
              <Button size="sm" variant="outline" onClick={handleSeed}>
                Seed Standard Prompts
              </Button>
              <Link href="/app/prompts/new">
                <Button size="sm">Create Prompt</Button>
              </Link>
            </div>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-400">
              <thead className="bg-slate-900/60 border-b border-slate-800 text-slate-400 uppercase text-[10px] tracking-wider font-semibold">
                <tr>
                  <th className="py-3 px-4">Prompt & Key</th>
                  <th className="py-3 px-4">Type</th>
                  <th className="py-3 px-4">Production</th>
                  <th className="py-3 px-4">Staging</th>
                  <th className="py-3 px-4">Latest Version</th>
                  <th className="py-3 px-4">Updated</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {filteredPrompts.map((p) => {
                  const isCopied = copiedKey === p.key;
                  return (
                    <tr
                      key={p.id}
                      className="hover:bg-slate-850/40 transition-colors group cursor-pointer"
                    >
                      <td className="py-3 px-4">
                        <Link href={`/app/prompts/${p.id}`} className="block">
                          <div className="font-semibold text-slate-200 group-hover:text-indigo-400 transition-colors">
                            {p.name}
                          </div>
                          <div className="flex items-center gap-1.5 mt-0.5">
                            <code className="text-[11px] font-mono text-slate-400 bg-slate-950 px-1.5 py-0.5 rounded border border-slate-800">
                              {p.key}
                            </code>
                            <button
                              onClick={(e) => handleCopyKey(p.key, e)}
                              className="text-slate-500 hover:text-slate-300 p-0.5"
                              title="Copy key"
                            >
                              {isCopied ? (
                                <Check className="w-3 h-3 text-emerald-400" />
                              ) : (
                                <Copy className="w-3 h-3" />
                              )}
                            </button>
                          </div>
                          {p.description && (
                            <p className="text-[11px] text-slate-500 line-clamp-1 mt-1">
                              {p.description}
                            </p>
                          )}
                        </Link>
                      </td>

                      <td className="py-3 px-4">
                        <span className="capitalize px-2 py-0.5 rounded text-[10px] font-medium bg-slate-800 text-slate-300 border border-slate-700">
                          {p.prompt_type}
                        </span>
                      </td>

                      <td className="py-3 px-4">
                        {p.production_version ? (
                          <div className="flex items-center gap-1.5">
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                            <span className="font-mono text-emerald-400 font-medium">
                              v{p.production_version.version_number}
                            </span>
                          </div>
                        ) : (
                          <span className="text-slate-600 font-mono">—</span>
                        )}
                      </td>

                      <td className="py-3 px-4">
                        {p.staging_version ? (
                          <div className="flex items-center gap-1.5">
                            <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
                            <span className="font-mono text-amber-400 font-medium">
                              v{p.staging_version.version_number}
                            </span>
                          </div>
                        ) : (
                          <span className="text-slate-600 font-mono">—</span>
                        )}
                      </td>

                      <td className="py-3 px-4">
                        {p.latest_version ? (
                          <div className="flex items-center gap-2">
                            <span className="font-mono text-slate-300">
                              v{p.latest_version.version_number}
                            </span>
                            <span
                              className={`text-[9px] px-1.5 py-0.2 rounded font-semibold uppercase ${
                                p.latest_version.status === "published"
                                  ? "bg-indigo-950 text-indigo-300 border border-indigo-800"
                                  : p.latest_version.status === "draft"
                                  ? "bg-slate-800 text-slate-400 border border-slate-700"
                                  : "bg-rose-950 text-rose-300 border border-rose-800"
                              }`}
                            >
                              {p.latest_version.status}
                            </span>
                          </div>
                        ) : (
                          <span className="text-slate-600 font-mono">No versions</span>
                        )}
                      </td>

                      <td className="py-3 px-4 text-slate-400">
                        {new Date(p.updated_at).toLocaleDateString()}
                      </td>

                      <td className="py-3 px-4 text-right">
                        <Link href={`/app/prompts/${p.id}`}>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="text-xs text-indigo-400 hover:text-indigo-300 hover:bg-indigo-950/30"
                          >
                            Open Hub
                          </Button>
                        </Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
