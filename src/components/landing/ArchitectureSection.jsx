import React from "react";
import { Badge } from "@/components/ui/Badge";
import { Cpu, Database, Wrench, Shield, ArrowDown, Network, GitPullRequest, Code2 } from "lucide-react";

export function ArchitectureSection() {
  const layers = [
    {
      level: "Layer 01",
      title: "Task Ingestion & Semantic Deconstruction",
      desc: "Parses human and programmatic goals into structured execution DAGs (Directed Acyclic Graphs), identifying constraints, expected output schemas, and compute budget.",
      icon: Network,
      color: "border-indigo-500/40 text-indigo-400 bg-indigo-950/30",
    },
    {
      level: "Layer 02",
      title: "Intelligent Model Routing Engine",
      desc: "Evaluates task complexity, latency sensitivity, and domain specificity to select the optimal model tier across Claude, GPT, Gemini, DeepSeek, or local Ollama endpoints.",
      icon: Cpu,
      color: "border-cyan-500/40 text-cyan-400 bg-cyan-950/30",
    },
    {
      level: "Layer 03",
      title: "Context Synthesis & Retrieval Strategies",
      desc: "Dynamically switches between Hybrid Dense/Sparse RAG, Knowledge Graph Multi-Hop traversal, and Direct Context Window injection based on information density.",
      icon: Database,
      color: "border-emerald-500/40 text-emerald-400 bg-emerald-950/30",
    },
    {
      level: "Layer 04",
      title: "Sandboxed Tool & Agentic Action Execution",
      desc: "Executes verified Python scripts, REST API endpoints, SQL mutations, and web browser subagents within deterministic, isolated microVM sandboxes.",
      icon: Wrench,
      color: "border-amber-500/40 text-amber-400 bg-amber-950/30",
    },
  ];

  return (
    <section id="architecture" className="py-24 border-t border-slate-800/80 bg-slate-950/40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <Badge variant="info" dot className="mb-3">
            System Architecture
          </Badge>
          <h2 className="text-3xl sm:text-4xl font-bold text-white tracking-tight">
            Engineered for Autonomous, Deterministic Execution
          </h2>
          <p className="mt-4 text-sm sm:text-base text-slate-400">
            A modular 4-tier pipeline designed to bridge front-facing task interfaces with backend Python/FastAPI execution engines.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {layers.map((layer) => {
            const Icon = layer.icon;
            return (
              <div
                key={layer.level}
                className="p-6 rounded-xl border border-slate-800 bg-slate-900/60 hover:border-slate-700 transition-all space-y-3"
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs text-slate-400">{layer.level}</span>
                  <div className={`p-2 rounded-lg border ${layer.color}`}>
                    <Icon className="w-4 h-4" />
                  </div>
                </div>
                <h3 className="text-base font-semibold text-slate-100">{layer.title}</h3>
                <p className="text-xs text-slate-400 leading-relaxed">{layer.desc}</p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
