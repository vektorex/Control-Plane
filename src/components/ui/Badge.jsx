import React from "react";
import { cn } from "@/lib/utils";

export function Badge({
  children,
  className = "",
  variant = "default",
  dot = false,
  dotColor,
  ...props
}) {
  const variants = {
    default: "bg-slate-800 text-slate-300 border-slate-700",
    primary: "bg-indigo-950/60 text-indigo-300 border-indigo-800/60",
    success: "bg-emerald-950/60 text-emerald-300 border-emerald-800/60",
    warning: "bg-amber-950/60 text-amber-300 border-amber-800/60",
    destructive: "bg-rose-950/60 text-rose-300 border-rose-800/60",
    info: "bg-cyan-950/60 text-cyan-300 border-cyan-800/60",
    purple: "bg-purple-950/60 text-purple-300 border-purple-800/60",
    outline: "bg-transparent text-slate-400 border-slate-700",
  };

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border transition-colors",
        variants[variant],
        className
      )}
      {...props}
    >
      {dot && (
        <span
          className={cn(
            "w-1.5 h-1.5 rounded-full",
            dotColor ||
              (variant === "success"
                ? "bg-emerald-400"
                : variant === "warning"
                ? "bg-amber-400"
                : variant === "destructive"
                ? "bg-rose-400"
                : variant === "primary"
                ? "bg-indigo-400"
                : variant === "info"
                ? "bg-cyan-400"
                : "bg-slate-400")
          )}
        />
      )}
      {children}
    </span>
  );
}
