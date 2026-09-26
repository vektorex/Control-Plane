"use client";

import React, { useState } from "react";
import { ChevronDown, Check, Plus, Layers } from "lucide-react";
import { cn } from "@/lib/utils";
import { env } from "@/config/env";

export function WorkspaceSelector() {
  const [isOpen, setIsOpen] = useState(false);
  const [workspaces, setWorkspaces] = useState([
    { id: "ws-default", name: env.app.defaultWorkspace, plan: "Enterprise" },
    { id: "ws-research", name: "Autonomous Research Lab", plan: "Production" },
    { id: "ws-data-eng", name: "Data Engineering Pipeline", plan: "Pro" },
  ]);
  const [activeWorkspace, setActiveWorkspace] = useState(workspaces[0]);

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-2 rounded-lg bg-slate-900/80 hover:bg-slate-800 border border-slate-800 transition-colors text-left cursor-pointer group"
      >
        <div className="flex items-center gap-2.5 min-w-0">
          <div className="w-7 h-7 rounded-md bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400 shrink-0">
            <Layers className="w-4 h-4" />
          </div>
          <div className="truncate">
            <div className="text-xs font-semibold text-slate-200 truncate">{activeWorkspace.name}</div>
            <div className="text-[10px] text-slate-400">{activeWorkspace.plan} Workspace</div>
          </div>
        </div>
        <ChevronDown className={cn("w-3.5 h-3.5 text-slate-400 transition-transform duration-200", isOpen && "rotate-180")} />
      </button>

      {isOpen && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setIsOpen(false)} />
          <div className="absolute top-full left-0 mt-1.5 w-full bg-slate-900 border border-slate-700 rounded-lg shadow-xl py-1 z-50 animate-in fade-in zoom-in-95 duration-100">
            <div className="px-2.5 py-1 text-[10px] font-medium text-slate-400 uppercase tracking-wider">
              Workspaces
            </div>
            {workspaces.map((ws) => {
              const isSelected = ws.id === activeWorkspace.id;
              return (
                <button
                  key={ws.id}
                  onClick={() => {
                    setActiveWorkspace(ws);
                    setIsOpen(false);
                  }}
                  className="w-full flex items-center justify-between px-2.5 py-2 text-xs text-left hover:bg-slate-800 text-slate-200 transition-colors cursor-pointer"
                >
                  <span className="truncate">{ws.name}</span>
                  {isSelected && <Check className="w-3.5 h-3.5 text-indigo-400 shrink-0 ml-2" />}
                </button>
              );
            })}
            <div className="border-t border-slate-800 my-1 pt-1">
              <button
                onClick={() => {
                  const newName = `Workspace ${workspaces.length + 1}`;
                  const newWs = { id: `ws-${Date.now()}`, name: newName, plan: "Pro" };
                  setWorkspaces([...workspaces, newWs]);
                  setActiveWorkspace(newWs);
                  setIsOpen(false);
                }}
                className="w-full flex items-center gap-2 px-2.5 py-1.5 text-xs text-indigo-400 hover:text-indigo-300 hover:bg-slate-800/60 transition-colors cursor-pointer"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Create workspace</span>
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
