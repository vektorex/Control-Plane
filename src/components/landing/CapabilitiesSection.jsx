import React from "react";
import { Badge } from "@/components/ui/Badge";
import { Cpu, Server, Shield, Layers, Zap, Terminal } from "lucide-react";

export function CapabilitiesSection() {
  const capabilities = [
    {
      title: "Model Agnostic Routing",
      desc: "Route queries dynamically across Claude 3.5, GPT-4o, Gemini 1.5, DeepSeek R1, and custom vLLM instances without vendor lock-in.",
      icon: Cpu,
    },
    {
      title: "FastAPI Backend Readiness",
      desc: "Built from day one with dedicated API client services tailored to hook cleanly into a Python FastAPI orchestration backend.",
      icon: Server,
    },
    {
      title: "Project-Scoped Workspaces",
      desc: "Isolate enterprise contexts, access tokens, knowledge graph indexes, and execution histories into partitioned project scopes.",
      icon: Layers,
    },
    {
      title: "Zero-Latency Layer Overhead",
      desc: "Optimized Next.js frontend state management with instant optimistic UI feedback and structured streaming event listeners.",
      icon: Zap,
    },
    {
      title: "Enterprise Context Security",
      desc: "Zero hardcoded secrets, strict environment variable segregation, and scoped bearer tokens for external agent actions.",
      icon: Shield,
    },
    {
      title: "Developer First Control Plane",
      desc: "Full observability into prompt deconstruction, token consumption, latency breakdown, and execution logs.",
      icon: Terminal,
    },
  ];

  return (
    <section id="capabilities" className="py-24 border-t border-slate-800 bg-slate-950/20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <Badge variant="primary" dot className="mb-3">
            Core Capabilities
          </Badge>
          <h2 className="text-3xl sm:text-4xl font-bold text-white tracking-tight">
            Built for Serious AI Workloads
          </h2>
          <p className="mt-4 text-sm sm:text-base text-slate-400">
            A production-ready foundation designed to transform raw generative models into reliable, orchestrated enterprise workflows.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {capabilities.map((cap) => {
            const Icon = cap.icon;
            return (
              <div
                key={cap.title}
                className="p-6 rounded-xl border border-slate-800 bg-slate-900/40 hover:bg-slate-900/80 hover:border-slate-700 transition-all space-y-2.5 group"
              >
                <div className="w-9 h-9 rounded-lg bg-indigo-950/60 border border-indigo-800/50 flex items-center justify-center text-indigo-400 group-hover:bg-indigo-600 group-hover:text-white transition-colors">
                  <Icon className="w-4.5 h-4.5" />
                </div>
                <h3 className="text-sm font-semibold text-slate-100">{cap.title}</h3>
                <p className="text-xs text-slate-400 leading-relaxed">{cap.desc}</p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
