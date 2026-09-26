import React from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { MODEL_PROVIDERS } from "@/config/constants";
import { Cpu, CheckCircle2, ShieldCheck, Key } from "lucide-react";

export function ProviderStatusCard() {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>LLM Providers & Execution Targets</CardTitle>
            <CardDescription>
              Model providers and runtime environments available for orchestrator dynamic routing
            </CardDescription>
          </div>
          <Badge variant="primary">Multi-Provider</Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {MODEL_PROVIDERS.map((provider) => (
            <div
              key={provider.id}
              className="p-3.5 rounded-lg bg-slate-950/60 border border-slate-800 flex items-center justify-between hover:border-slate-700 transition-colors"
            >
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded-md bg-slate-900 border border-slate-700 text-indigo-400">
                  <Cpu className="w-4 h-4" />
                </div>
                <div>
                  <div className="text-xs font-semibold text-slate-200">{provider.name}</div>
                  <div className="text-[10px] text-slate-400">Routing Target</div>
                </div>
              </div>
              <Badge variant="success" dot className="text-[10px]">
                {provider.status}
              </Badge>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
