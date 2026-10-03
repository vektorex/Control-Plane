"use client";

import React, { useState, useEffect, useRef, useMemo } from "react";
import {
  ZoomIn,
  ZoomOut,
  Maximize2,
  RefreshCw,
  Search,
  Filter,
  Eye,
  Info,
  ChevronRight,
  ExternalLink,
  Shield,
  Layers,
} from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";

// Curated harmonious color palette per entity type
const TYPE_COLORS = {
  person: { bg: "#fef3c7", border: "#f59e0b", text: "#92400e", darkBg: "rgba(245, 158, 11, 0.15)", darkBorder: "#d97706" },
  organization: { bg: "#e0e7ff", border: "#6366f1", text: "#3730a3", darkBg: "rgba(99, 102, 241, 0.15)", darkBorder: "#4f46e5" },
  project: { bg: "#dbeafe", border: "#3b82f6", text: "#1e40af", darkBg: "rgba(59, 130, 246, 0.15)", darkBorder: "#2563eb" },
  repository: { bg: "#ede9fe", border: "#8b5cf6", text: "#5b21b6", darkBg: "rgba(139, 92, 246, 0.15)", darkBorder: "#7c3aed" },
  file: { bg: "#f1f5f9", border: "#64748b", text: "#334155", darkBg: "rgba(100, 116, 139, 0.15)", darkBorder: "#475569" },
  document: { bg: "#fae8ff", border: "#d946ef", text: "#86198f", darkBg: "rgba(217, 70, 239, 0.15)", darkBorder: "#c026d3" },
  task: { bg: "#ffedd5", border: "#f97316", text: "#9a3412", darkBg: "rgba(249, 115, 22, 0.15)", darkBorder: "#ea580c" },
  workflow: { bg: "#cffafe", border: "#06b6d4", text: "#155e75", darkBg: "rgba(6, 182, 212, 0.15)", darkBorder: "#0891b2" },
  workflow_step: { bg: "#e0f2fe", border: "#0284c7", text: "#0369a1", darkBg: "rgba(2, 132, 199, 0.15)", darkBorder: "#0284c7" },
  technology: { bg: "#d1fae5", border: "#10b981", text: "#065f46", darkBg: "rgba(16, 185, 129, 0.15)", darkBorder: "#059669" },
  service: { bg: "#ccfbf1", border: "#14b8a6", text: "#115e59", darkBg: "rgba(20, 184, 166, 0.15)", darkBorder: "#0d9488" },
  api: { bg: "#e0e7ff", border: "#4f46e5", text: "#312e81", darkBg: "rgba(79, 70, 229, 0.15)", darkBorder: "#4338ca" },
  database: { bg: "#fef9c3", border: "#eab308", text: "#854d0e", darkBg: "rgba(234, 179, 8, 0.15)", darkBorder: "#ca8a04" },
  model: { bg: "#ffe4e6", border: "#f43f5e", text: "#9f1239", darkBg: "rgba(244, 63, 94, 0.15)", darkBorder: "#e11d48" },
  prompt: { bg: "#fce7f3", border: "#ec4899", text: "#9d174d", darkBg: "rgba(236, 72, 153, 0.15)", darkBorder: "#db2777" },
  issue: { bg: "#fee2e2", border: "#ef4444", text: "#991b1b", darkBg: "rgba(239, 68, 68, 0.15)", darkBorder: "#dc2626" },
  pull_request: { bg: "#ecfdf5", border: "#10b981", text: "#047857", darkBg: "rgba(16, 185, 129, 0.15)", darkBorder: "#059669" },
  concept: { bg: "#f3e8ff", border: "#a855f7", text: "#6b21a8", darkBg: "rgba(168, 85, 247, 0.15)", darkBorder: "#9333ea" },
};

function getNodeColor(type) {
  return (
    TYPE_COLORS[type] || {
      bg: "#f3f4f6",
      border: "#9ca3af",
      text: "#374151",
      darkBg: "rgba(156, 163, 175, 0.15)",
      darkBorder: "#6b7280",
    }
  );
}

export function GraphCanvas({
  initialEntities = [],
  initialRelationships = [],
  onExpandNeighbors,
  onSelectEntity,
  className = "",
}) {
  const containerRef = useRef(null);
  const [entities, setEntities] = useState(initialEntities);
  const [relationships, setRelationships] = useState(initialRelationships);
  const [selectedNode, setSelectedNode] = useState(null);
  const [selectedEdge, setSelectedEdge] = useState(null);
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isPanning, setIsPanning] = useState(false);
  const [startPan, setStartPan] = useState({ x: 0, y: 0 });
  const [filterType, setFilterType] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [nodePositions, setNodePositions] = useState({});

  useEffect(() => {
    setEntities(initialEntities);
  }, [initialEntities]);

  useEffect(() => {
    setRelationships(initialRelationships);
  }, [initialRelationships]);

  // Layout node positions in a bounded circular/force layout
  useEffect(() => {
    const width = 800;
    const height = 600;
    const centerX = width / 2;
    const centerY = height / 2;
    const count = entities.length;

    if (count === 0) return;

    const positions = {};
    const radius = Math.min(centerX, centerY) - 80;

    entities.forEach((entity, idx) => {
      // Golden angle distribution for natural spread
      const angle = idx * (Math.PI * (3 - Math.sqrt(5)));
      const r = Math.sqrt(idx / count) * radius;
      positions[entity.id] = {
        x: centerX + r * Math.cos(angle),
        y: centerY + r * Math.sin(angle),
      };
    });

    setNodePositions(positions);
  }, [entities]);

  // Filter entities based on search and type
  const visibleEntities = useMemo(() => {
    return entities.filter((e) => {
      const matchType = filterType === "all" || e.entity_type === filterType;
      const matchSearch =
        !searchQuery ||
        e.canonical_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        e.description?.toLowerCase().includes(searchQuery.toLowerCase());
      return matchType && matchSearch;
    });
  }, [entities, filterType, searchQuery]);

  const visibleNodeIds = useMemo(
    () => new Set(visibleEntities.map((e) => e.id)),
    [visibleEntities]
  );

  const visibleRelationships = useMemo(() => {
    return relationships.filter(
      (r) =>
        visibleNodeIds.has(r.source_entity_id) &&
        visibleNodeIds.has(r.target_entity_id)
    );
  }, [relationships, visibleNodeIds]);

  // Pan controls
  const handleMouseDown = (e) => {
    if (e.target.tagName === "svg" || e.target.tagName === "g") {
      setIsPanning(true);
      setStartPan({ x: e.clientX - pan.x, y: e.clientY - pan.y });
    }
  };

  const handleMouseMove = (e) => {
    if (isPanning) {
      setPan({ x: e.clientX - startPan.x, y: e.clientY - startPan.y });
    }
  };

  const handleMouseUp = () => {
    setIsPanning(false);
  };

  const handleNodeClick = (entity, e) => {
    e.stopPropagation();
    setSelectedNode(entity);
    setSelectedEdge(null);
    if (onSelectEntity) {
      onSelectEntity(entity);
    }
  };

  const handleEdgeClick = (rel, e) => {
    e.stopPropagation();
    setSelectedEdge(rel);
    setSelectedNode(null);
  };

  const resetView = () => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
  };

  const expandNodeNeighbors = async (entity) => {
    if (onExpandNeighbors) {
      const res = await onExpandNeighbors(entity.id);
      if (res && res.entities) {
        // Merge in newly fetched entities and relationships
        const existingIds = new Set(entities.map((e) => e.id));
        const newEntities = res.entities.filter((e) => !existingIds.has(e.id));
        setEntities((prev) => [...prev, ...newEntities]);

        const existingRelKeys = new Set(
          relationships.map(
            (r) => `${r.source_entity_id}-${r.relationship_type}-${r.target_entity_id}`
          )
        );
        const newRels = (res.relationships || []).filter(
          (r) =>
            !existingRelKeys.has(
              `${r.source_entity_id}-${r.relationship_type}-${r.target_entity_id}`
            )
        );
        setRelationships((prev) => [...prev, ...newRels]);
      }
    }
  };

  return (
    <div
      ref={containerRef}
      className={`relative w-full h-[650px] bg-slate-950/60 border border-slate-800 rounded-xl overflow-hidden select-none ${className}`}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
    >
      {/* Top Toolbar */}
      <div className="absolute top-4 left-4 right-4 z-10 flex flex-wrap items-center justify-between gap-3 pointer-events-none">
        <div className="flex items-center gap-2 pointer-events-auto bg-slate-900/90 backdrop-blur-md border border-slate-700/60 rounded-lg p-1.5 shadow-lg">
          <div className="relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Find entity..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-8 pr-3 py-1 text-xs bg-slate-800/80 border border-slate-700 rounded-md text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 w-44"
            />
          </div>

          <div className="h-4 w-px bg-slate-700 mx-1" />

          <Filter className="w-3.5 h-3.5 text-slate-400 ml-1" />
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="text-xs bg-slate-800/80 border border-slate-700 rounded-md px-2 py-1 text-slate-300 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          >
            <option value="all">All Types ({entities.length})</option>
            {Object.keys(TYPE_COLORS).map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </div>

        {/* View Controls */}
        <div className="flex items-center gap-1 pointer-events-auto bg-slate-900/90 backdrop-blur-md border border-slate-700/60 rounded-lg p-1 shadow-lg">
          <button
            onClick={() => setZoom((z) => Math.min(z + 0.2, 2.5))}
            className="p-1.5 text-slate-300 hover:text-white hover:bg-slate-800 rounded transition"
            title="Zoom In"
          >
            <ZoomIn className="w-4 h-4" />
          </button>
          <button
            onClick={() => setZoom((z) => Math.max(z - 0.2, 0.4))}
            className="p-1.5 text-slate-300 hover:text-white hover:bg-slate-800 rounded transition"
            title="Zoom Out"
          >
            <ZoomOut className="w-4 h-4" />
          </button>
          <button
            onClick={resetView}
            className="p-1.5 text-slate-300 hover:text-white hover:bg-slate-800 rounded transition"
            title="Reset View"
          >
            <Maximize2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* SVG Canvas */}
      <svg
        className="w-full h-full cursor-grab active:cursor-grabbing"
        viewBox="0 0 800 600"
      >
        <defs>
          <marker
            id="arrow"
            viewBox="0 0 10 10"
            refX="22"
            refY="5"
            markerWidth="6"
            markerHeight="6"
            orient="auto-start-reverse"
          >
            <path d="M 0 1 L 10 5 L 0 9 z" fill="#64748b" />
          </marker>
          <marker
            id="arrow-selected"
            viewBox="0 0 10 10"
            refX="22"
            refY="5"
            markerWidth="6"
            markerHeight="6"
            orient="auto-start-reverse"
          >
            <path d="M 0 1 L 10 5 L 0 9 z" fill="#818cf8" />
          </marker>
        </defs>

        <g
          transform={`translate(${pan.x}, ${pan.y}) scale(${zoom})`}
          transformOrigin="center"
        >
          {/* Render Relationships (Edges) */}
          {visibleRelationships.map((rel) => {
            const sourcePos = nodePositions[rel.source_entity_id];
            const targetPos = nodePositions[rel.target_entity_id];
            if (!sourcePos || !targetPos) return null;

            const isRelSelected = selectedEdge?.id === rel.id;
            const midX = (sourcePos.x + targetPos.x) / 2;
            const midY = (sourcePos.y + targetPos.y) / 2;

            return (
              <g
                key={rel.id}
                className="cursor-pointer"
                onClick={(e) => handleEdgeClick(rel, e)}
              >
                <line
                  x1={sourcePos.x}
                  y1={sourcePos.y}
                  x2={targetPos.x}
                  y2={targetPos.y}
                  stroke={isRelSelected ? "#818cf8" : "#475569"}
                  strokeWidth={isRelSelected ? 2.5 : 1.5}
                  strokeDasharray={rel.confidence && rel.confidence < 0.8 ? "4 3" : "none"}
                  markerEnd={isRelSelected ? "url(#arrow-selected)" : "url(#arrow)"}
                  className="transition-colors duration-200 hover:stroke-indigo-400"
                />
                {/* Edge Label Badge */}
                <rect
                  x={midX - 35}
                  y={midY - 10}
                  width="70"
                  height="18"
                  rx="9"
                  fill="#0f172a"
                  stroke={isRelSelected ? "#818cf8" : "#334155"}
                  strokeWidth="1"
                />
                <text
                  x={midX}
                  y={midY + 2.5}
                  textAnchor="middle"
                  fill={isRelSelected ? "#c7d2fe" : "#94a3b8"}
                  fontSize="9"
                  fontWeight="600"
                  fontFamily="sans-serif"
                >
                  {rel.relationship_type.replace(/_/g, " ")}
                </text>
              </g>
            );
          })}

          {/* Render Entities (Nodes) */}
          {visibleEntities.map((entity) => {
            const pos = nodePositions[entity.id];
            if (!pos) return null;

            const isSelected = selectedNode?.id === entity.id;
            const colors = getNodeColor(entity.entity_type);

            return (
              <g
                key={entity.id}
                transform={`translate(${pos.x}, ${pos.y})`}
                className="cursor-pointer"
                onClick={(e) => handleNodeClick(entity, e)}
              >
                {/* Glow filter if selected */}
                {isSelected && (
                  <circle
                    r="28"
                    fill="none"
                    stroke="#818cf8"
                    strokeWidth="3"
                    strokeDasharray="4 2"
                    className="animate-pulse"
                  />
                )}
                {/* Node circle */}
                <circle
                  r="20"
                  fill={colors.darkBg}
                  stroke={isSelected ? "#818cf8" : colors.darkBorder}
                  strokeWidth={isSelected ? 2.5 : 1.5}
                  className="transition-all duration-200 hover:scale-110"
                />
                {/* Center Icon Initial */}
                <text
                  textAnchor="middle"
                  dy="4"
                  fill={colors.text}
                  fontSize="10"
                  fontWeight="700"
                  fontFamily="sans-serif"
                >
                  {entity.entity_type.substring(0, 2).toUpperCase()}
                </text>
                {/* Label text under node */}
                <text
                  y="32"
                  textAnchor="middle"
                  fill={isSelected ? "#ffffff" : "#cbd5e1"}
                  fontSize="11"
                  fontWeight="600"
                  fontFamily="sans-serif"
                >
                  {entity.canonical_name?.length > 18
                    ? entity.canonical_name.substring(0, 16) + "…"
                    : entity.canonical_name}
                </text>
              </g>
            );
          })}
        </g>
      </svg>

      {/* Node Inspector Drawer */}
      {selectedNode && (
        <div className="absolute top-16 right-4 w-80 bg-slate-900/95 backdrop-blur-md border border-slate-700/80 rounded-xl p-4 shadow-2xl z-20 transition-all text-xs">
          <div className="flex items-start justify-between mb-3 pb-2 border-b border-slate-800">
            <div>
              <div className="flex items-center gap-1.5 mb-1">
                <Badge variant="outline" className="text-[10px] uppercase font-bold">
                  {selectedNode.entity_type}
                </Badge>
                {selectedNode.confidence && (
                  <span className="text-[10px] text-slate-400">
                    {Math.round(selectedNode.confidence * 100)}% conf
                  </span>
                )}
              </div>
              <h4 className="text-sm font-semibold text-slate-100">
                {selectedNode.canonical_name}
              </h4>
            </div>
            <button
              onClick={() => setSelectedNode(null)}
              className="text-slate-400 hover:text-white p-1"
            >
              ✕
            </button>
          </div>

          {selectedNode.description && (
            <p className="text-slate-300 text-xs mb-3 line-clamp-3">
              {selectedNode.description}
            </p>
          )}

          <div className="space-y-2 mb-4">
            <div className="flex justify-between text-slate-400">
              <span>Source Count:</span>
              <span className="text-slate-200 font-medium">
                {selectedNode.source_count || 1}
              </span>
            </div>
            <div className="flex justify-between text-slate-400">
              <span>Status:</span>
              <Badge variant="secondary" className="text-[10px]">
                {selectedNode.status || "active"}
              </Badge>
            </div>
          </div>

          <div className="flex items-center gap-2 pt-2 border-t border-slate-800">
            <Button
              size="sm"
              variant="outline"
              className="flex-1 text-xs"
              onClick={() => expandNodeNeighbors(selectedNode)}
            >
              <RefreshCw className="w-3 h-3 mr-1" /> Expand 1-Hop
            </Button>
            <a
              href={`/app/knowledge/entities/${selectedNode.id}`}
              className="inline-flex items-center justify-center p-2 rounded-lg bg-indigo-600/20 text-indigo-400 hover:bg-indigo-600/30 transition text-xs"
              title="Open Entity Detail"
            >
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
          </div>
        </div>
      )}

      {/* Edge Inspector Drawer */}
      {selectedEdge && (
        <div className="absolute top-16 right-4 w-72 bg-slate-900/95 backdrop-blur-md border border-slate-700/80 rounded-xl p-4 shadow-2xl z-20 text-xs">
          <div className="flex items-start justify-between mb-2 pb-2 border-b border-slate-800">
            <div>
              <Badge variant="secondary" className="text-[10px] font-bold">
                {selectedEdge.relationship_type}
              </Badge>
              <h4 className="text-xs font-semibold text-slate-200 mt-1">
                Relationship
              </h4>
            </div>
            <button
              onClick={() => setSelectedEdge(null)}
              className="text-slate-400 hover:text-white p-1"
            >
              ✕
            </button>
          </div>

          <div className="space-y-2 mb-3">
            <div className="text-slate-400">
              <span className="block text-[10px] uppercase text-slate-500">Source:</span>
              <span className="font-mono text-slate-300 truncate block">
                {selectedEdge.source_entity_id}
              </span>
            </div>
            <div className="text-slate-400">
              <span className="block text-[10px] uppercase text-slate-500">Target:</span>
              <span className="font-mono text-slate-300 truncate block">
                {selectedEdge.target_entity_id}
              </span>
            </div>
            {selectedEdge.confidence && (
              <div className="flex justify-between text-slate-400">
                <span>Confidence:</span>
                <span className="text-slate-200 font-medium">
                  {Math.round(selectedEdge.confidence * 100)}%
                </span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Empty State */}
      {entities.length === 0 && (
        <div className="absolute inset-0 flex flex-col items-center justify-center text-slate-400 pointer-events-none">
          <Layers className="w-12 h-12 text-slate-600 mb-2" />
          <p className="text-sm font-medium">No knowledge graph entities found</p>
          <p className="text-xs text-slate-500">
            Ingest documents, connect GitHub, or add entities manually to populate the graph.
          </p>
        </div>
      )}
    </div>
  );
}
