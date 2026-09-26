"use client";

import React, { useState } from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { Button } from "@/components/ui/Button";
import { Save, Check } from "lucide-react";
import { env } from "@/config/env";

export function GeneralSettingsForm() {
  const [workspaceName, setWorkspaceName] = useState(env.app.defaultWorkspace);
  const [defaultMode, setDefaultMode] = useState("auto");
  const [defaultTimeout, setDefaultTimeout] = useState("30");
  const [saved, setSaved] = useState(false);

  const handleSave = (e) => {
    e.preventDefault();
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  };

  return (
    <Card>
      <form onSubmit={handleSave}>
        <CardHeader>
          <CardTitle>Workspace General Settings</CardTitle>
          <CardDescription>
            Manage default workspace attributes, task timeout bounds, and default execution policies
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Input
            label="Primary Workspace Name"
            value={workspaceName}
            onChange={(e) => setWorkspaceName(e.target.value)}
            helperText="The display identifier used across orchestration logs and tasks."
          />

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Select
              label="Default Routing Strategy"
              value={defaultMode}
              onChange={(e) => setDefaultMode(e.target.value)}
              options={[
                { value: "auto", label: "Autonomous Smart Router" },
                { value: "fast", label: "Fast / Cost-First Tier" },
                { value: "deep_reasoning", label: "Deep Reasoning Tier" },
              ]}
              helperText="Fallback policy applied when tasks do not explicitly specify a mode."
            />

            <Input
              label="Task Max Execution Timeout (seconds)"
              type="number"
              value={defaultTimeout}
              onChange={(e) => setDefaultTimeout(e.target.value)}
              helperText="Orchestration job abort threshold before raising timeout exception."
            />
          </div>
        </CardContent>
        <CardFooter className="flex items-center justify-between">
          <span className="text-xs text-slate-400">
            {saved ? (
              <span className="text-emerald-400 flex items-center gap-1">
                <Check className="w-3.5 h-3.5" /> Workspace preferences updated
              </span>
            ) : (
              "Settings are persisted per workspace."
            )}
          </span>
          <Button type="submit" variant="primary" size="sm" icon={Save}>
            Save General Settings
          </Button>
        </CardFooter>
      </form>
    </Card>
  );
}
