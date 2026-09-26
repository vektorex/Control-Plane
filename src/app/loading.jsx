import React from "react";
import { Loader2, Cpu } from "lucide-react";

export default function RootLoading() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-[#07090e] p-6 space-y-4">
      <div className="w-12 h-12 rounded-2xl bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
        <Cpu className="w-6 h-6 animate-pulse" />
      </div>
      <div className="flex items-center gap-2 text-xs font-medium text-slate-400 font-mono">
        <Loader2 className="w-4 h-4 animate-spin text-indigo-400" />
        <span>Initializing AI Work Layer...</span>
      </div>
    </div>
  );
}
