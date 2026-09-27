"use client";

import React, { useState } from "react";
import { Tabs } from "@/components/ui/Tabs";
import { GeneralSettingsForm } from "@/components/features/settings/GeneralSettingsForm";
import { OrchestratorConfigForm } from "@/components/features/settings/OrchestratorConfigForm";
import { ProviderStatusCard } from "@/components/features/settings/ProviderStatusCard";
import { AccountProfileCard } from "@/components/features/settings/AccountProfileCard";
import { Sliders, Server, Cpu, ShieldCheck } from "lucide-react";

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState("general");

  const tabs = [
    { id: "general", label: "General & Workspace", icon: Sliders },
    { id: "account", label: "Account & Auth", icon: ShieldCheck },
    { id: "engine", label: "FastAPI Engine Target", icon: Server },
    { id: "providers", label: "Model Providers", icon: Cpu },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="pb-2 border-b border-slate-850">
        <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-white">
          System & Orchestrator Settings
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Configure workspace policies, authentication profile, FastAPI backend connection, and LLM provider parameters.
        </p>
      </div>

      {/* Tabs Switcher */}
      <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />

      {/* Tab Panels */}
      <div className="pt-2">
        {activeTab === "general" && <GeneralSettingsForm />}
        {activeTab === "account" && <AccountProfileCard />}
        {activeTab === "engine" && <OrchestratorConfigForm />}
        {activeTab === "providers" && <ProviderStatusCard />}
      </div>
    </div>
  );
}

