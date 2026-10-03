"use client";

import React from "react";
import { User, Bot, GitBranch, Cpu } from "lucide-react";
import { cn } from "@/lib/utils";

/**
 * AgentIdentityBadge: Clearly distinguishes Human, AI Agent, Delegated Agent, and System.
 * Invariant: An AI Agent can never claim to be human or impersonate a human.
 */
export function AgentIdentityBadge({
  type = "ai_agent",
  name,
  versionNumber,
  className = "",
}) {
  const configs = {
    human: {
      label: "HUMAN",
      icon: User,
      bg: "bg-blue-500/10 text-blue-400 border-blue-500/20",
      dot: "bg-blue-400",
    },
    ai_agent: {
      label: "AI AGENT",
      icon: Bot,
      bg: "bg-purple-500/10 text-purple-400 border-purple-500/20",
      dot: "bg-purple-400",
    },
    ai_agent_delegated: {
      label: "DELEGATED AGENT",
      icon: GitBranch,
      bg: "bg-cyan-500/10 text-cyan-400 border-cyan-500/20",
      dot: "bg-cyan-400",
    },
    system: {
      label: "SYSTEM",
      icon: Cpu,
      bg: "bg-zinc-500/10 text-zinc-400 border-zinc-500/20",
      dot: "bg-zinc-400",
    },
  };

  const current = configs[type] || configs.ai_agent;
  const Icon = current.icon;

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border tracking-wide",
        current.bg,
        className
      )}
      title={`Principal Type: ${current.label}`}
    >
      <Icon className="w-3.5 h-3.5" />
      <span className="font-semibold">{current.label}</span>
      {name && <span className="opacity-90 font-normal">| {name}</span>}
      {versionNumber && (
        <span className="text-[10px] px-1 py-0.2 rounded bg-black/30 font-mono">
          v{versionNumber}
        </span>
      )}
    </span>
  );
}
