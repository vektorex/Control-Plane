"use client";

import React, { useState } from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Server, Save, RefreshCw, CheckCircle2, Shield } from "lucide-react";
import { env } from "@/config/env";

export function OrchestratorConfigForm() {
  const [apiUrl, setApiUrl] = useState(env.orchestrator.apiUrl);
  const [apiSecret, setApiSecret] = useState(env.orchestrator.apiSecret);
  const [isTesting, setIsTesting] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState("configured"); // "configured" | "testing" | "ready"

  const handleTestConnection = () => {
    setIsTesting(true);
    setTimeout(() => {
      setIsTesting(false);
      setConnectionStatus("ready");
    }, 1200);
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>FastAPI Orchestration Engine Target</CardTitle>
            <CardDescription>
              Configure the connection to the Python/FastAPI service responsible for execution graphs
            </CardDescription>
          </div>
          <Badge variant="info" dot>
            FastAPI Contract Ready
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        <Input
          label="Backend Orchestration API Endpoint"
          value={apiUrl}
          onChange={(e) => setApiUrl(e.target.value)}
          placeholder="http://localhost:8000/api/v1"
          helperText="Target URL where your FastAPI application is running."
          icon={Server}
        />

        <Input
          label="Orchestration Layer Secret / Bearer Token"
          type="password"
          value={apiSecret}
          onChange={(e) => setApiSecret(e.target.value)}
          placeholder="••••••••••••••••••••••••••••••••"
          helperText="Optional shared secret used to authenticate API requests between Next.js and FastAPI."
          icon={Shield}
        />

        <div className="p-4 rounded-lg bg-slate-950/80 border border-slate-800 space-y-2 text-xs">
          <div className="flex items-center justify-between font-mono">
            <span className="text-slate-400">Architecture Integration Status:</span>
            <span className="text-emerald-400 font-semibold flex items-center gap-1">
              <CheckCircle2 className="w-3.5 h-3.5" /> Client Contracts Initialized
            </span>
          </div>
          <p className="text-slate-400 text-[11px] leading-relaxed">
            The Next.js client is mapped to send all work orchestration payloads, model routing criteria, and context references via structured API contracts in <code className="text-indigo-300">src/services/orchestrator.js</code>.
          </p>
        </div>
      </CardContent>

      <CardFooter className="flex items-center justify-between">
        <Button
          variant="secondary"
          size="sm"
          onClick={handleTestConnection}
          isLoading={isTesting}
          icon={RefreshCw}
        >
          Verify Endpoint
        </Button>
        <Button variant="primary" size="sm" icon={Save}>
          Update Engine Configuration
        </Button>
      </CardFooter>
    </Card>
  );
}
