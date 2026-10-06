"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Input } from "@/components/ui/Input";
import { StatCard } from "@/components/ui/StatCard";
import { planningService } from "@/services/planning";
import {
  Users2,
  Plus,
  Search,
  RefreshCw,
  Cpu,
  Layers,
  ArrowRight,
  ShieldCheck,
  AlertTriangle,
} from "lucide-react";

export default function ResourcesPage() {
  const [resources, setResources] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [typeFilter, setTypeFilter] = useState("ALL");
  const [error, setError] = useState(null);

  // New Resource modal state
  const [showCreate, setShowCreate] = useState(false);
  const [createForm, setCreateForm] = useState({
    name: "",
    resource_type: "agent",
    resource_ref: "",
    description: "",
    capabilities: "python, analysis",
  });
  const [actionLoading, setActionLoading] = useState(false);

  const fetchResources = async () => {
    try {
      setLoading(true);
      setError(null);
      const params = {};
      if (typeFilter !== "ALL") params.resourceType = typeFilter.toLowerCase();
      const data = await planningService.listResources(params);
      setResources(Array.isArray(data) ? data : []);
    } catch (err) {
      setError(err.message || "Failed to load resources");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchResources();
  }, [typeFilter]);

  const handleCreateResource = async (e) => {
    e.preventDefault();
    try {
      setActionLoading(true);
      const caps = createForm.capabilities
        ? createForm.capabilities.split(",").map((s) => s.trim()).filter(Boolean)
        : [];
      await planningService.createResource({
        name: createForm.name,
        resource_type: createForm.resource_type,
        resource_ref: createForm.resource_ref || `ref-${Date.now()}`,
        description: createForm.description || null,
        capabilities: caps,
      });
      setShowCreate(false);
      setCreateForm({
        name: "",
        resource_type: "agent",
        resource_ref: "",
        description: "",
        capabilities: "python, analysis",
      });
      await fetchResources();
    } catch (err) {
      setError(err.message || "Failed to register resource");
    } finally {
      setActionLoading(false);
    }
  };

  const filtered = resources.filter((r) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return r.name?.toLowerCase().includes(q) || r.resource_type?.toLowerCase().includes(q);
  });

  return (
    <div className="space-y-8 p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 border-b border-border/40 pb-6">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-primary/10 text-primary border border-primary/20">
              <Users2 className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-foreground">
                Work Resources
              </h1>
              <p className="text-sm text-muted-foreground mt-0.5">
                Agents, multi-agent teams, workflows, and humans available for factual work planning.
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <Button variant="outline" size="sm" onClick={fetchResources} disabled={loading} className="gap-2">
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </Button>
          <Button size="sm" onClick={() => setShowCreate(true)} className="gap-2">
            <Plus className="w-4 h-4" />
            Register Resource
          </Button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-destructive/10 border border-destructive/20 text-destructive text-sm flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {showCreate && (
        <Card className="p-6 border-primary/40 bg-card/80">
          <form onSubmit={handleCreateResource} className="space-y-4">
            <h3 className="font-semibold text-sm text-foreground">Register Work Resource Reference</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-xs text-muted-foreground">Resource Name</label>
                <Input
                  placeholder="e.g. Code Reviewer Agent"
                  value={createForm.name}
                  onChange={(e) => setCreateForm({ ...createForm, name: e.target.value })}
                  required
                />
              </div>
              <div>
                <label className="text-xs text-muted-foreground">Resource Type</label>
                <select
                  value={createForm.resource_type}
                  onChange={(e) => setCreateForm({ ...createForm, resource_type: e.target.value })}
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm"
                >
                  <option value="agent">AI Agent</option>
                  <option value="agent_team">AI Agent Team</option>
                  <option value="workflow">Workflow</option>
                  <option value="human">Human User</option>
                  <option value="tool">Tool</option>
                  <option value="connector">Connector</option>
                  <option value="system">System Capacity</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-xs text-muted-foreground">Existing Entity Reference (UUID)</label>
                <Input
                  placeholder="UUID of Agent, User, Workflow, etc."
                  value={createForm.resource_ref}
                  onChange={(e) => setCreateForm({ ...createForm, resource_ref: e.target.value })}
                  required
                />
              </div>
              <div>
                <label className="text-xs text-muted-foreground">Capabilities (comma separated)</label>
                <Input
                  placeholder="e.g. python, security_review, javascript"
                  value={createForm.capabilities}
                  onChange={(e) => setCreateForm({ ...createForm, capabilities: e.target.value })}
                />
              </div>
            </div>

            <div>
              <label className="text-xs text-muted-foreground">Description</label>
              <Input
                placeholder="Capability description and suitability notes..."
                value={createForm.description}
                onChange={(e) => setCreateForm({ ...createForm, description: e.target.value })}
              />
            </div>

            <div className="flex items-center justify-end gap-2 pt-2">
              <Button type="button" variant="ghost" size="sm" onClick={() => setShowCreate(false)}>
                Cancel
              </Button>
              <Button type="submit" size="sm" disabled={actionLoading}>
                Register
              </Button>
            </div>
          </form>
        </Card>
      )}

      {/* Search & Filters */}
      <Card className="p-4 bg-card/60 border-border/60">
        <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
          <div className="relative w-full md:w-80">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Search resources..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9"
            />
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {["ALL", "AGENT", "AGENT_TEAM", "WORKFLOW", "HUMAN", "TOOL"].map((t) => (
              <Button
                key={t}
                size="sm"
                variant={typeFilter === t ? "primary" : "ghost"}
                onClick={() => setTypeFilter(t)}
                className="text-xs capitalize"
              >
                {t.toLowerCase().replace("_", " ")}
              </Button>
            ))}
          </div>
        </div>
      </Card>

      {/* Resource Grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3].map((i) => (
            <Card key={i} className="p-6 h-48 animate-pulse bg-card/60" />
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <Card className="p-12 text-center text-muted-foreground border-dashed">
          No resources found. Register an agent, workflow, or human resource to begin planning.
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filtered.map((res) => (
            <Card key={res.id} className="p-6 space-y-4 flex flex-col justify-between hover:border-primary/40 transition-colors">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <Badge variant="outline" className="text-xs uppercase font-mono">
                    {res.resource_type}
                  </Badge>
                  <Badge variant={res.status === "active" ? "success" : "neutral"} className="text-xs">
                    {res.status}
                  </Badge>
                </div>

                <div>
                  <h3 className="font-semibold text-lg text-foreground">{res.name}</h3>
                  <p className="text-xs text-muted-foreground line-clamp-2 mt-1">
                    {res.description || "No description provided."}
                  </p>
                </div>

                <div className="pt-2 border-t border-border/40 space-y-1">
                  <span className="text-xs font-semibold text-foreground">Capabilities:</span>
                  <div className="flex flex-wrap gap-1">
                    {(res.capabilities || []).map((cap, i) => (
                      <Badge key={i} variant="secondary" className="text-[10px]">
                        {cap}
                      </Badge>
                    ))}
                  </div>
                </div>
              </div>

              <div className="pt-4 border-t border-border/40 flex items-center justify-between">
                <Link href={`/app/resources/${res.id}`}>
                  <Button variant="ghost" size="sm" className="text-xs">
                    Details
                  </Button>
                </Link>
                <Link href={`/app/resources/${res.id}/capacity`}>
                  <Button variant="outline" size="sm" className="text-xs gap-1.5">
                    Capacity
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Button>
                </Link>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
