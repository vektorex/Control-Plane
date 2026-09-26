import React from "react";
import { cn } from "@/lib/utils";

export function Card({ children, className = "", hoverable = false, ...props }) {
  return (
    <div
      className={cn(
        "rounded-xl bg-slate-900/70 border border-slate-800 text-slate-100 shadow-sm backdrop-blur-sm",
        hoverable && "transition-all duration-200 hover:border-slate-700 hover:bg-slate-900/90 hover:shadow-md hover:shadow-indigo-950/30",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}

export function CardHeader({ children, className = "", ...props }) {
  return (
    <div className={cn("flex flex-col space-y-1.5 p-5 border-b border-slate-800/60", className)} {...props}>
      {children}
    </div>
  );
}

export function CardTitle({ children, className = "", ...props }) {
  return (
    <h3 className={cn("text-base font-semibold text-slate-100 leading-none tracking-tight", className)} {...props}>
      {children}
    </h3>
  );
}

export function CardDescription({ children, className = "", ...props }) {
  return (
    <p className={cn("text-xs text-slate-400 leading-relaxed", className)} {...props}>
      {children}
    </p>
  );
}

export function CardContent({ children, className = "", ...props }) {
  return (
    <div className={cn("p-5", className)} {...props}>
      {children}
    </div>
  );
}

export function CardFooter({ children, className = "", ...props }) {
  return (
    <div className={cn("flex items-center p-5 pt-0 border-t border-slate-800/40 mt-auto", className)} {...props}>
      {children}
    </div>
  );
}
