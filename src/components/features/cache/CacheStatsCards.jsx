"use client";

import React from "react";
import {
  Database,
  CheckCircle2,
  Sparkles,
  XCircle,
  SkipForward,
  TrendingUp,
  Layers,
  HardDrive,
} from "lucide-react";

export function CacheStatsCards({ stats = {}, loading = false }) {
  const formatBytes = (bytes) => {
    if (!bytes || bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`;
  };

  const hitPercentage = Math.round((stats.hit_ratio || 0) * 100);

  const cards = [
    {
      title: "Total Lookups",
      value: stats.lookups?.toLocaleString() || "0",
      description: "Cache queries processed",
      icon: Database,
      color: "text-blue-500",
      bgColor: "bg-blue-500/10",
    },
    {
      title: "Exact Hits",
      value: stats.exact_hits?.toLocaleString() || "0",
      description: "Deterministic 100% hash reuse",
      icon: CheckCircle2,
      color: "text-emerald-500",
      bgColor: "bg-emerald-500/10",
    },
    {
      title: "Semantic Hits",
      value: stats.semantic_hits?.toLocaleString() || "0",
      description: "Vector cosine similarity matches",
      icon: Sparkles,
      color: "text-indigo-500",
      bgColor: "bg-indigo-500/10",
    },
    {
      title: "Hit Ratio",
      value: `${hitPercentage}%`,
      description: "Reuse efficiency",
      icon: TrendingUp,
      color: "text-cyan-500",
      bgColor: "bg-cyan-500/10",
    },
    {
      title: "Cache Misses",
      value: stats.misses?.toLocaleString() || "0",
      description: "Routed to AI Gateway execution",
      icon: XCircle,
      color: "text-amber-500",
      bgColor: "bg-amber-500/10",
    },
    {
      title: "Bypasses",
      value: stats.bypasses?.toLocaleString() || "0",
      description: "Side-effects & refresh bypasses",
      icon: SkipForward,
      color: "text-purple-500",
      bgColor: "bg-purple-500/10",
    },
    {
      title: "Active Entries",
      value: stats.active_entries?.toLocaleString() || "0",
      description: "Valid reusable entries",
      icon: Layers,
      color: "text-teal-500",
      bgColor: "bg-teal-500/10",
    },
    {
      title: "Storage Usage",
      value: formatBytes(stats.storage_bytes),
      description: "Persisted responses footprint",
      icon: HardDrive,
      color: "text-rose-500",
      bgColor: "bg-rose-500/10",
    },
  ];

  if (loading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(8)].map((_, i) => (
          <div
            key={i}
            className="h-28 rounded-xl border border-border/40 bg-card/50 p-4 animate-pulse"
          />
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((card, idx) => {
        const Icon = card.icon;
        return (
          <div
            key={idx}
            className="relative overflow-hidden rounded-xl border border-border/50 bg-card/60 p-5 shadow-sm backdrop-blur-sm transition-all hover:border-border hover:shadow-md"
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                {card.title}
              </span>
              <div className={`rounded-lg p-2 ${card.bgColor}`}>
                <Icon className={`h-4 w-4 ${card.color}`} />
              </div>
            </div>
            <div className="mt-3">
              <div className="text-2xl font-bold tracking-tight text-foreground">
                {card.value}
              </div>
              <p className="mt-1 text-xs text-muted-foreground">
                {card.description}
              </p>
            </div>
          </div>
        );
      })}
    </div>
  );
}
