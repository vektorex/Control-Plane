import React from "react";
import { StatCard } from "@/components/ui/StatCard";
import { Cpu, CheckCircle2, Zap, GitBranch, Layers } from "lucide-react";

export function ExecutionMetrics() {
  const metrics = [
    {
      title: "Active Workloads",
      value: "12",
      change: "+4 today",
      changeType: "positive",
      icon: Layers,
      description: "in queue",
    },
    {
      title: "Routing Decisions",
      value: "1,482",
      change: "99.8%",
      changeType: "positive",
      icon: GitBranch,
      description: "optimal match rate",
    },
    {
      title: "Model Dispatches",
      value: "4,890",
      change: "+18%",
      changeType: "positive",
      icon: Cpu,
      description: "across 5 providers",
    },
    {
      title: "Avg Layer Overhead",
      value: "14ms",
      change: "-2ms",
      changeType: "positive",
      icon: Zap,
      description: "orchestration delay",
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {metrics.map((metric) => (
        <StatCard
          key={metric.title}
          title={metric.title}
          value={metric.value}
          change={metric.change}
          changeType={metric.changeType}
          icon={metric.icon}
          description={metric.description}
        />
      ))}
    </div>
  );
}
