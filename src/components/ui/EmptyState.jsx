import React from "react";
import { cn } from "@/lib/utils";
import { Button } from "./Button";

export function EmptyState({
  icon: Icon,
  title,
  description,
  actionLabel,
  onAction,
  actionIcon,
  className = "",
}) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center p-12 text-center rounded-xl border border-dashed border-slate-800 bg-slate-900/30",
        className
      )}
    >
      {Icon && (
        <div className="p-3.5 mb-4 rounded-xl bg-slate-800/80 border border-slate-700 text-indigo-400">
          <Icon className="w-6 h-6" />
        </div>
      )}
      <h3 className="text-base font-semibold text-slate-200">{title}</h3>
      {description && <p className="text-xs text-slate-400 max-w-sm mt-1 mb-5">{description}</p>}
      {actionLabel && onAction && (
        <Button onClick={onAction} icon={actionIcon} variant="primary" size="sm">
          {actionLabel}
        </Button>
      )}
    </div>
  );
}
