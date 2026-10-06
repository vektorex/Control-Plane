"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { outcomeService } from "@/services/outcomes";
import {
  GitPullRequest,
  ArrowLeft,
  RefreshCw,
  AlertCircle,
  Award,
  ShieldCheck,
  Scale,
  Box,
  Cpu,
  Layers,
  Activity,
  CheckCircle2,
} from "lucide-react";

export default function OutcomeGraphPage() {
  const params = useParams();
  const outcomeId = params.outcomeId;

  const [graphData, setGraphData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);

  const fetchGraph = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await outcomeService.getOutcomeGraph(outcomeId);
      setGraphData(res);
      if (res?.nodes?.length > 0) {
        setSelectedNode(res.nodes[0]);
      }
    } catch (err) {
      console.error("[OutcomeGraphPage] Error:", err);
      setError(err.message || "Failed to load outcome graph");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (outcomeId) fetchGraph();
  }, [outcomeId]);

  const getNodeIcon = (type) => {
    switch (type) {
      case "outcome":
        return <Award className="h-4 w-4 text-emerald-400" />;
      case "evidence":
        return <ShieldCheck className="h-4 w-4 text-amber-400" />;
      case "decision":
        return <Scale className="h-4 w-4 text-indigo-400" />;
      case "task":
      case "run":
        return <Box className="h-4 w-4 text-purple-400" />;
      case "agent":
      case "agent_run":
        return <Cpu className="h-4 w-4 text-cyan-400" />;
      default:
        return <Layers className="h-4 w-4 text-zinc-400" />;
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link href={`/app/outcomes/${outcomeId}`}>
            <Button variant="ghost" size="sm" className="gap-2 text-zinc-400 hover:text-zinc-100">
              <ArrowLeft className="h-4 w-4" />
              Back to Outcome
            </Button>
          </Link>
          <span className="text-zinc-600">/</span>
          <span className="text-sm font-semibold text-zinc-200">Attribution & Traversal Graph</span>
        </div>
        <Button
          onClick={fetchGraph}
          variant="outline"
          size="sm"
          className="gap-2 border-zinc-800 text-zinc-300"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          Refresh Graph
        </Button>
      </div>

      <div className="space-y-1">
        <h1 className="text-2xl font-bold tracking-tight text-zinc-100 flex items-center gap-2">
          <GitPullRequest className="h-6 w-6 text-indigo-400" />
          Outcome Attribution & Dependency Graph
        </h1>
        <p className="text-sm text-zinc-400">
          Bounded graph traversal (1–3 hops max) connecting executions, evidence records, and decisions to this outcome deliverable.
        </p>
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm flex items-center gap-2">
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {loading ? (
        <div className="flex justify-center py-16">
          <RefreshCw className="h-8 w-8 animate-spin text-zinc-500" />
        </div>
      ) : !graphData || graphData.nodes?.length === 0 ? (
        <Card className="p-10 text-center bg-zinc-900/40 border-zinc-800">
          <GitPullRequest className="h-10 w-10 text-zinc-600 mx-auto mb-3" />
          <h3 className="text-base font-medium text-zinc-300">No graph data found</h3>
          <p className="text-xs text-zinc-500 mt-1 max-w-sm mx-auto">
            Attach evidence, linked work, or decisions to populate the attribution graph.
          </p>
        </Card>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Nodes & Edges View */}
          <div className="lg:col-span-2 space-y-4">
            <Card className="p-4 bg-zinc-900/60 border-zinc-800 space-y-3">
              <div className="flex items-center justify-between text-xs text-zinc-400 border-b border-zinc-800/80 pb-2">
                <span>{graphData.nodes.length} Graph Entities</span>
                <span>{graphData.edges?.length || 0} Relationships</span>
              </div>

              <div className="space-y-2 max-h-[600px] overflow-y-auto pr-1">
                {graphData.nodes.map((node) => {
                  const isSelected = selectedNode?.id === node.id;
                  return (
                    <div
                      key={node.id}
                      onClick={() => setSelectedNode(node)}
                      className={`p-3 rounded-lg border cursor-pointer transition flex items-center justify-between ${
                        isSelected
                          ? "border-emerald-500 bg-emerald-950/20"
                          : "border-zinc-800 bg-zinc-950/60 hover:border-zinc-700"
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <div className="p-1.5 rounded-md bg-zinc-900 border border-zinc-800">
                          {getNodeIcon(node.type)}
                        </div>
                        <div>
                          <div className="text-xs font-semibold text-zinc-200">
                            {node.label || node.name || node.id}
                          </div>
                          <div className="text-[10px] text-zinc-500 font-mono">
                            Type: {node.type} | ID: {node.id.slice(0, 8)}...
                          </div>
                        </div>
                      </div>

                      <Badge className="bg-zinc-800 text-zinc-400 border-zinc-700 text-[10px] uppercase">
                        {node.status || "active"}
                      </Badge>
                    </div>
                  );
                })}
              </div>
            </Card>

            {/* Edge Connections List */}
            {graphData.edges && graphData.edges.length > 0 && (
              <Card className="p-4 bg-zinc-900/40 border-zinc-800 space-y-2">
                <h3 className="text-xs font-semibold text-zinc-300">Graph Relationships</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs">
                  {graphData.edges.map((edge, idx) => (
                    <div key={idx} className="p-2 rounded bg-zinc-950 border border-zinc-800/80 flex items-center justify-between">
                      <span className="font-mono text-zinc-400 text-[11px] truncate max-w-[100px]">
                        {edge.source?.slice(0, 8)}
                      </span>
                      <Badge className="text-[10px] bg-zinc-800 text-emerald-400 border-zinc-700">
                        {edge.relationship || edge.type}
                      </Badge>
                      <span className="font-mono text-zinc-400 text-[11px] truncate max-w-[100px]">
                        {edge.target?.slice(0, 8)}
                      </span>
                    </div>
                  ))}
                </div>
              </Card>
            )}
          </div>

          {/* Node Inspector Panel */}
          <div className="space-y-4">
            <Card className="p-5 bg-zinc-900/60 border-zinc-800 space-y-4 sticky top-6">
              <h3 className="text-sm font-semibold text-zinc-200 border-b border-zinc-800/80 pb-3 flex items-center gap-2">
                <Activity className="h-4 w-4 text-emerald-400" />
                Entity Details
              </h3>

              {selectedNode ? (
                <div className="space-y-3 text-xs">
                  <div>
                    <label className="text-[10px] uppercase font-mono text-zinc-500">Label / Name</label>
                    <div className="font-medium text-zinc-100 text-sm mt-0.5">
                      {selectedNode.label || selectedNode.name || selectedNode.id}
                    </div>
                  </div>

                  <div>
                    <label className="text-[10px] uppercase font-mono text-zinc-500">Entity Type</label>
                    <div className="mt-0.5">
                      <Badge className="bg-emerald-500/10 text-emerald-400 border-emerald-500/20 font-mono text-[10px] uppercase">
                        {selectedNode.type}
                      </Badge>
                    </div>
                  </div>

                  <div>
                    <label className="text-[10px] uppercase font-mono text-zinc-500">Resource ID</label>
                    <div className="font-mono text-zinc-400 text-[11px] bg-zinc-950 p-1.5 rounded border border-zinc-800 mt-0.5 break-all">
                      {selectedNode.id}
                    </div>
                  </div>

                  {selectedNode.properties && (
                    <div>
                      <label className="text-[10px] uppercase font-mono text-zinc-500">Provenance & Metadata</label>
                      <pre className="p-2 rounded bg-zinc-950 border border-zinc-800 text-[10px] text-zinc-300 font-mono mt-0.5 max-h-48 overflow-y-auto whitespace-pre-wrap">
                        {JSON.stringify(selectedNode.properties, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              ) : (
                <p className="text-xs text-zinc-500">Select any graph entity to inspect provenance.</p>
              )}
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}
