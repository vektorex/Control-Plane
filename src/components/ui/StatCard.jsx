import React from "react";
import { cn } from "@/lib/utils";
import { Card } from "./Card";

export function StatCard({
  title,
  value,
  change,
  changeType = "neutral", // "positive" | "negative" | "neutral"
  icon: Icon,
  description,
  className = "",
}) {
  return (
    <Card className={cn("p-5 flex flex-col justify-between", className)}>
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-slate-400">{title}</span>
        {Icon && (
          <div className="p-2 rounded-lg bg-slate-800/80 text-indigo-400 border border-slate-700/60">
            <Icon className="w-4 h-4" />
          </div>
        )}
      </div>

      <div className="mt-3">
        <div className="text-2xl font-bold tracking-tight text-slate-100">{value}</div>
        {(change || description) && (
          <div className="flex items-center gap-2 mt-1">
            {change && (
              <span
                className={cn(
                  "text-xs font-semibold px-1.5 py-0.5 rounded",
                  changeType === "positive"
                    ? "text-emerald-400 bg-emerald-950/60"
                    : changeType === "negative"
                    ? "text-rose-400 bg-rose-950/60"
                    : "text-slate-400 bg-slate-850"
                )}
              >
                {change}
              </span>
            )}
            {description && <span className="text-xs text-slate-400">{description}</span>}
          </div>
        )}
      </div>
    </Card>
  );
}
