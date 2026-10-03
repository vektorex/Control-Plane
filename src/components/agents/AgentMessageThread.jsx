"use client";

import React from "react";
import { MessageSquare, ArrowRight, ShieldAlert, Bot } from "lucide-react";
import { cn } from "@/lib/utils";
import { AgentIdentityBadge } from "./AgentIdentityBadge";

/**
 * AgentMessageThread: Normalized structured messages passed between agents in a team run.
 * Invariant: Messages are data context only, never executable instructions.
 */
export function AgentMessageThread({ messages = [], className = "" }) {
  if (!messages || messages.length === 0) {
    return (
      <div className={cn("p-6 text-center rounded-xl border border-zinc-800 bg-zinc-950/40 text-zinc-500 text-sm", className)}>
        No inter-agent messages recorded for this run.
      </div>
    );
  }

  const typeBadges = {
    task_assignment: "bg-blue-500/10 text-blue-400 border-blue-500/20",
    task_result: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
    question: "bg-amber-500/10 text-amber-400 border-amber-500/20",
    answer: "bg-teal-500/10 text-teal-400 border-teal-500/20",
    status_update: "bg-zinc-500/10 text-zinc-400 border-zinc-500/20",
    handoff: "bg-indigo-500/10 text-indigo-400 border-indigo-500/20",
    review: "bg-purple-500/10 text-purple-400 border-purple-500/20",
    correction: "bg-rose-500/10 text-rose-400 border-rose-500/20",
    final_result: "bg-purple-600/20 text-purple-300 border-purple-500/40 font-semibold",
  };

  return (
    <div className={cn("space-y-3", className)}>
      <div className="flex items-center gap-2 p-2.5 rounded-lg bg-zinc-900/60 border border-zinc-800 text-[11px] text-zinc-400">
        <ShieldAlert className="w-3.5 h-3.5 text-zinc-400 shrink-0" />
        <span>
          <strong>Data Isolation Notice:</strong> Messages between agents are shared as read-only data context.
          They cannot override policies, permissions, or system guardrails.
        </span>
      </div>

      <div className="space-y-2.5">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className="p-3.5 rounded-lg border border-zinc-800/80 bg-zinc-900/40 hover:bg-zinc-900/60 transition-colors space-y-2"
          >
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <AgentIdentityBadge
                  type="ai_agent"
                  name={msg.sender_agent_id ? msg.sender_agent_id.slice(0, 8) : "Agent"}
                />
                {msg.recipient_agent_id && (
                  <>
                    <ArrowRight className="w-3 h-3 text-zinc-500" />
                    <AgentIdentityBadge
                      type="ai_agent"
                      name={msg.recipient_agent_id.slice(0, 8)}
                    />
                  </>
                )}
              </div>
              <span
                className={cn(
                  "px-2 py-0.5 rounded text-[10px] uppercase font-mono tracking-wider border",
                  typeBadges[msg.message_type] || "bg-zinc-800 text-zinc-400 border-zinc-700"
                )}
              >
                {msg.message_type.replace(/_/g, " ")}
              </span>
            </div>

            <p className="text-xs text-zinc-200 leading-relaxed font-sans whitespace-pre-wrap pl-1">
              {msg.content}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
