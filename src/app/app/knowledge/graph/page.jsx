"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import {
  Network,
  Search,
  Filter,
  RefreshCw,
  Sparkles,
  Layers,
  ArrowLeft,
  Sliders,
} from "lucide-react";
import { knowledgeGraphService } from "@/services/knowledgeGraph";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { GraphCanvas } from "@/components/features/knowledge/GraphCanvas";

export default function GraphVisualizerPage() {
  const [entities, setEntities] = useState([]);
  const [relationships, setRelationships] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [maxHops, setMaxHops] = useState(1);
  const [maxEntities, setMaxEntities] = useState(50);
  const [selectedEntityTypes, setSelectedEntityTypes] = useState([]);
  const [seedSearch, setSeedSearch] = useState("");

  const loadGraphData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // Perform bounded graph query
      const queryPayload = {
        seed_entities: seedSearch.trim() ? [seedSearch.trim()] : [],
        entity_types: selectedEntityTypes.length > 0 ? selectedEntityTypes : [],
        relationship_types: [],
        max_hops: maxHops,
        max_entities: maxEntities,
        max_relationships: 100,
      };

      const res = await knowledgeGraphService.queryGraph(queryPayload);
      setEntities(res?.entities || []);
      setRelationships(res?.relationships || []);
    } catch (err) {
      console.error("Failed to query knowledge graph:", err);
      // Fallback: list initial entities and relationships
      try {
        const [entList, relList] = await Promise.all([
          knowledgeGraphService.listEntities({ limit: 40 }),
          knowledgeGraphService.listRelationships({ limit: 60 }),
        ]);
        setEntities(entList || []);
        setRelationships(relList || []);
      } catch (err2) {
        setError(err.message || "Failed to load graph data");
      }
    } finally {
      setLoading(false);
    }
  }, [maxHops, maxEntities, selectedEntityTypes, seedSearch]);

  useEffect(() => {
    loadGraphData();
  }, [loadGraphData]);

  const handleExpandNeighbors = async (entityId) => {
    try {
      return await knowledgeGraphService.getNeighbors(entityId);
    } catch (err) {
      console.error("Failed to expand neighbors:", err);
      return null;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Network className="w-6 h-6 text-indigo-400" />
            <h1 className="text-2xl font-bold tracking-tight text-slate-100">
              Visual Knowledge Graph
            </h1>
          </div>
          <p className="text-xs text-slate-400">
            Interactive node-link graph visualization with bounded traversal and neighbor inspection.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Link href="/app/knowledge">
            <Button variant="outline" size="sm" className="text-xs">
              <ArrowLeft className="w-3.5 h-3.5 mr-1" /> Dashboard
            </Button>
          </Link>
          <Button
            size="sm"
            onClick={loadGraphData}
            disabled={loading}
            className="text-xs"
          >
            <RefreshCw className={`w-3.5 h-3.5 mr-1.5 ${loading ? "animate-spin" : ""}`} />
            Refresh Graph
          </Button>
        </div>
      </div>

      {/* Traversal Controls Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 bg-slate-900/60 border border-slate-800 p-3 rounded-xl text-xs">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 text-slate-400">
            <Sliders className="w-3.5 h-3.5 text-indigo-400" />
            <span>Traversal Depth:</span>
          </div>
          <div className="flex items-center gap-1">
            {[1, 2, 3].map((hop) => (
              <button
                key={hop}
                onClick={() => setMaxHops(hop)}
                className={`px-2.5 py-1 rounded-md text-xs font-semibold transition ${
                  maxHops === hop
                    ? "bg-indigo-600 text-white"
                    : "bg-slate-800 text-slate-400 hover:text-white"
                }`}
              >
                {hop}-Hop
              </button>
            ))}
          </div>

          <div className="h-4 w-px bg-slate-800" />

          <div className="flex items-center gap-1.5 text-slate-400">
            <span>Max Nodes:</span>
            <select
              value={maxEntities}
              onChange={(e) => setMaxEntities(Number(e.target.value))}
              className="bg-slate-800 border border-slate-700 rounded px-2 py-0.5 text-slate-200"
            >
              <option value="25">25</option>
              <option value="50">50</option>
              <option value="100">100</option>
            </select>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-slate-400 text-xs">
            Displaying: <strong className="text-slate-200">{entities.length}</strong> nodes,{" "}
            <strong className="text-slate-200">{relationships.length}</strong> edges
          </span>
        </div>
      </div>

      {/* Error state */}
      {error && (
        <div className="p-3 bg-red-950/40 border border-red-800/60 rounded-lg text-xs text-red-300">
          {error}
        </div>
      )}

      {/* Interactive Visual Canvas */}
      <GraphCanvas
        initialEntities={entities}
        initialRelationships={relationships}
        onExpandNeighbors={handleExpandNeighbors}
      />
    </div>
  );
}
