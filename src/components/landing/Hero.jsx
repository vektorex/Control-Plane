import React from "react";
import Link from "next/link";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { ArrowRight, Sparkles, Terminal, Cpu, Layers, Database, ShieldCheck } from "lucide-react";
import { siteConfig } from "@/config/site";

export function Hero() {
  return (
    <section className="relative pt-32 pb-20 md:pt-40 md:pb-28 overflow-hidden bg-grid-pattern">
      {/* Background glow accents */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[350px] bg-indigo-600/15 blur-[120px] rounded-full pointer-events-none -z-10" />
      <div className="absolute top-1/3 left-1/3 -translate-x-1/2 w-[400px] h-[250px] bg-cyan-600/10 blur-[100px] rounded-full pointer-events-none -z-10" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        {/* Release / Phase Pill */}
        <div className="inline-flex items-center gap-2 mb-6">
          <Badge variant="primary" dot className="px-3.5 py-1 text-xs">
            Universal LLM Orchestration Platform • Architecture Foundation
          </Badge>
        </div>

        {/* Product Title */}
        <h1 className="text-4xl sm:text-6xl lg:text-7xl font-extrabold text-white tracking-tight leading-[1.1]">
          {siteConfig.name}
        </h1>

        {/* Primary Tagline */}
        <p className="mt-4 text-xl sm:text-2xl lg:text-3xl font-medium text-transparent bg-clip-text bg-gradient-to-r from-indigo-200 via-slate-100 to-cyan-200 max-w-3xl mx-auto tracking-tight">
          {siteConfig.tagline}
        </p>

        {/* Narrative Description */}
        <p className="mt-6 text-sm sm:text-base text-slate-400 max-w-2xl mx-auto leading-relaxed">
          Accepts complex user work, decomposes goals, and autonomously routes tasks to the optimal LLMs, context stores, retrieval pipelines, and specialized execution tools.
        </p>

        {/* CTAs */}
        <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-3">
          <Link href="/app">
            <Button variant="primary" size="lg" icon={ArrowRight} className="w-full sm:w-auto shadow-lg shadow-indigo-600/25">
              Launch App Workspace
            </Button>
          </Link>
          <a href="#architecture">
            <Button variant="secondary" size="lg" icon={Terminal} className="w-full sm:w-auto">
              Inspect Layer Architecture
            </Button>
          </a>
        </div>

        {/* Live Orchestration Preview Mock Container */}
        <div className="mt-16 max-w-4xl mx-auto">
          <div className="rounded-xl border border-slate-700/80 bg-slate-900/90 shadow-2xl shadow-indigo-950/60 overflow-hidden text-left backdrop-blur-xl">
            {/* Window Header */}
            <div className="px-4 py-3 bg-slate-950/90 border-b border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-rose-500/80" />
                <span className="w-3 h-3 rounded-full bg-amber-500/80" />
                <span className="w-3 h-3 rounded-full bg-emerald-500/80" />
                <span className="ml-2 font-mono text-xs text-slate-400">
                  orchestrator_pipeline.py — execution_graph
                </span>
              </div>
              <Badge variant="info" dot className="text-[10px] font-mono">
                ROUTING ACTIVE
              </Badge>
            </div>

            {/* Simulated Live Routing Visualization */}
            <div className="p-6 space-y-4 font-mono text-xs">
              <div className="p-3.5 rounded-lg bg-slate-950 border border-slate-800 text-slate-300">
                <span className="text-indigo-400 font-bold">$ task_input:</span> &quot;Reconcile payment ledger anomalies against stripe webhooks & generate audit summary&quot;
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2">
                <div className="p-3 rounded-lg bg-slate-950/70 border border-indigo-900/60 text-slate-300">
                  <div className="text-[10px] text-indigo-400 uppercase font-semibold">1. Intent & Routing</div>
                  <div className="text-xs text-slate-200 mt-1 font-semibold">High Complexity • Reasoning</div>
                  <div className="text-[11px] text-slate-400 mt-1">Routed to: Claude 3.5 Sonnet</div>
                </div>

                <div className="p-3 rounded-lg bg-slate-950/70 border border-cyan-900/60 text-slate-300">
                  <div className="text-[10px] text-cyan-400 uppercase font-semibold">2. Context Layer</div>
                  <div className="text-xs text-slate-200 mt-1 font-semibold">Hybrid Vector + Ledger DB</div>
                  <div className="text-[11px] text-slate-400 mt-1">12 chunks retrieved (99.1% rel)</div>
                </div>

                <div className="p-3 rounded-lg bg-slate-950/70 border border-emerald-900/60 text-slate-300">
                  <div className="text-[10px] text-emerald-400 uppercase font-semibold">3. Tool Sandbox</div>
                  <div className="text-xs text-slate-200 mt-1 font-semibold">Financial Math & Code Exec</div>
                  <div className="text-[11px] text-slate-400 mt-1">2 verified tool calls executed</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
