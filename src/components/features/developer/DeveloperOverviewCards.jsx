"use client";

import React from "react";
import { AppWindow, Key, Webhook, Activity, AlertTriangle, Clock } from "lucide-react";

export function DeveloperOverviewCards({ overview = {} }) {
  const cards = [
    {
      title: "Applications",
      value: overview.total_applications ?? 0,
      subtext: `${overview.active_environments?.length || 1} Active Environments`,
      icon: AppWindow,
      color: "text-blue-500",
      bg: "bg-blue-500/10",
    },
    {
      title: "Active Credentials",
      value: overview.active_credentials ?? 0,
      subtext: "Scoped API Keys",
      icon: Key,
      color: "text-emerald-500",
      bg: "bg-emerald-500/10",
    },
    {
      title: "Webhooks",
      value: overview.active_webhooks ?? 0,
      subtext: "Subscribed Endpoints",
      icon: Webhook,
      color: "text-purple-500",
      bg: "bg-purple-500/10",
    },
    {
      title: "Requests (24h)",
      value: overview.total_requests_24h ?? 0,
      subtext: "Total Public API Invocations",
      icon: Activity,
      color: "text-cyan-500",
      bg: "bg-cyan-500/10",
    },
    {
      title: "Error Rate (24h)",
      value: `${((overview.error_rate_24h || 0) * 100).toFixed(1)}%`,
      subtext: "4xx/5xx Responses",
      icon: AlertTriangle,
      color: (overview.error_rate_24h || 0) > 0.05 ? "text-rose-500" : "text-amber-500",
      bg: (overview.error_rate_24h || 0) > 0.05 ? "bg-rose-500/10" : "bg-amber-500/10",
    },
    {
      title: "Avg Latency",
      value: `${(overview.average_latency_ms || 0).toFixed(0)}ms`,
      subtext: "End-to-End Response Time",
      icon: Clock,
      color: "text-indigo-500",
      bg: "bg-indigo-500/10",
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
      {cards.map((c, i) => {
        const Icon = c.icon;
        return (
          <div
            key={i}
            className="p-4 rounded-xl border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 shadow-sm"
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-medium text-neutral-500 dark:text-neutral-400">
                {c.title}
              </span>
              <div className={`p-2 rounded-lg ${c.bg} ${c.color}`}>
                <Icon className="w-4 h-4" />
              </div>
            </div>
            <div className="text-2xl font-bold text-neutral-900 dark:text-neutral-100">
              {c.value}
            </div>
            <div className="text-xs text-neutral-500 dark:text-neutral-400 mt-1">
              {c.subtext}
            </div>
          </div>
        );
      })}
    </div>
  );
}
