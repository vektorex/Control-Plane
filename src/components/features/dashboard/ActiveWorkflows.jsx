import React from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { ArrowRight, Cpu, Database, Wrench, Sparkles, Network } from "lucide-react";

export function ActiveWorkflows() {
  const steps = [
    {
      title: "1. Task Ingestion",
      desc: "Intent extraction, schema validation & complexity grading",
      icon: Network,
      tag: "Ingest",
      color: "border-indigo-800 bg-indigo-950/40 text-indigo-300",
    },
    {
      title: "2. Routing Engine",
      desc: "Determines optimal model tier based on cost & latency requirements",
      icon: Cpu,
      tag: "FastAPI Engine",
      color: "border-cyan-800 bg-cyan-950/40 text-cyan-300",
    },
    {
      title: "3. Context Synthesis",
      desc: "Retrieves knowledge graphs, vectors, and live workspace context",
      icon: Database,
      tag: "RAG & Graphs",
      color: "border-emerald-800 bg-emerald-950/40 text-emerald-300",
    },
    {
      title: "4. Tool Dispatch",
      desc: "Executes verified sandboxed tools, APIs, and code execution",
      icon: Wrench,
      tag: "Toolkits",
      color: "border-amber-800 bg-amber-950/40 text-amber-300",
    },
    {
      title: "5. Work Delivery",
      desc: "Evaluates output confidence and streams results back to user",
      icon: Sparkles,
      tag: "Output",
      color: "border-purple-800 bg-purple-950/40 text-purple-300",
    },
  ];

  return (
    <Card className="overflow-hidden">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Orchestration Pipeline Architecture</CardTitle>
            <CardDescription>
              How the AI Work Layer coordinates models, context, and tools for every work unit
            </CardDescription>
          </div>
          <Badge variant="primary" dot>
            Architecture Ready
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-5 gap-3 relative">
          {steps.map((step, idx) => {
            const Icon = step.icon;
            return (
              <div
                key={step.title}
                className="relative p-4 rounded-xl border border-slate-800 bg-slate-900/60 flex flex-col justify-between hover:border-slate-700 transition-all group"
              >
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <div className={`p-2 rounded-lg border ${step.color}`}>
                      <Icon className="w-4 h-4" />
                    </div>
                    <span className="text-[10px] font-mono text-slate-400 bg-slate-800/80 px-2 py-0.5 rounded">
                      {step.tag}
                    </span>
                  </div>
                  <h4 className="text-xs font-semibold text-slate-200">{step.title}</h4>
                  <p className="text-[11px] text-slate-400 mt-1 leading-relaxed">{step.desc}</p>
                </div>

                {idx < steps.length - 1 && (
                  <div className="hidden md:flex absolute -right-3.5 top-1/2 -translate-y-1/2 z-10 w-6 h-6 rounded-full bg-slate-900 border border-slate-700 items-center justify-center text-slate-400 shadow-sm">
                    <ArrowRight className="w-3 h-3" />
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
