"use client";

import React from "react";
import { ShieldAlert, FlaskConical, Lock } from "lucide-react";

export function SimulationBanner({ mode = "ISOLATED", seed = 42 }) {
  return (
    <div className="rounded-lg border border-amber-500/40 bg-gradient-to-r from-amber-950/40 via-zinc-900 to-amber-950/30 p-4 shadow-lg backdrop-blur">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-md bg-amber-500/20 text-amber-400 border border-amber-500/30">
            <FlaskConical className="w-5 h-5 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-black uppercase tracking-wider px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/40">
                SIMULATION SANDBOX
              </span>
              <span className="text-xs text-zinc-400 font-mono">
                MODE: {mode.toUpperCase()}
              </span>
              <span className="text-xs text-zinc-500 font-mono">
                SEED: {seed}
              </span>
            </div>
            <p className="text-sm font-medium text-amber-100/90 mt-1">
              Zero External Side Effects: All writes, emails, webhooks, and tickets are intercepted and recorded safely.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 text-xs font-semibold px-3 py-1.5 rounded-md bg-zinc-800/80 border border-zinc-700/80 text-zinc-300">
          <Lock className="w-3.5 h-3.5 text-amber-400" />
          <span>PRODUCTION GUARD ACTIVE</span>
        </div>
      </div>
    </div>
  );
}
