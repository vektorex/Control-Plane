import React from "react";
import { cn } from "@/lib/utils";

export function Input({
  label,
  error,
  helperText,
  icon: Icon,
  className = "",
  containerClassName = "",
  id,
  type = "text",
  ...props
}) {
  const inputId = id || (label ? label.toLowerCase().replace(/\s+/g, "-") : undefined);

  return (
    <div className={cn("flex flex-col space-y-1.5 w-full", containerClassName)}>
      {label && (
        <label htmlFor={inputId} className="text-xs font-medium text-slate-300">
          {label}
        </label>
      )}
      <div className="relative flex items-center">
        {Icon && (
          <div className="absolute left-3 text-slate-400 pointer-events-none">
            <Icon className="w-4 h-4" />
          </div>
        )}
        <input
          id={inputId}
          type={type}
          className={cn(
            "w-full rounded-lg bg-slate-900 border border-slate-700 px-3.5 py-2 text-sm text-slate-100 placeholder:text-slate-500",
            "focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-colors",
            "disabled:opacity-50 disabled:bg-slate-800/50 disabled:cursor-not-allowed",
            Icon ? "pl-9" : "",
            error ? "border-rose-500 focus:border-rose-500 focus:ring-rose-500" : "",
            className
          )}
          {...props}
        />
      </div>
      {error && <p className="text-xs text-rose-400 mt-1">{error}</p>}
      {helperText && !error && <p className="text-xs text-slate-400 mt-1">{helperText}</p>}
    </div>
  );
}

export function Textarea({
  label,
  error,
  helperText,
  className = "",
  containerClassName = "",
  id,
  rows = 3,
  ...props
}) {
  const inputId = id || (label ? label.toLowerCase().replace(/\s+/g, "-") : undefined);

  return (
    <div className={cn("flex flex-col space-y-1.5 w-full", containerClassName)}>
      {label && (
        <label htmlFor={inputId} className="text-xs font-medium text-slate-300">
          {label}
        </label>
      )}
      <textarea
        id={inputId}
        rows={rows}
        className={cn(
          "w-full rounded-lg bg-slate-900 border border-slate-700 px-3.5 py-2 text-sm text-slate-100 placeholder:text-slate-500",
          "focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-colors resize-y",
          "disabled:opacity-50 disabled:bg-slate-800/50 disabled:cursor-not-allowed",
          error ? "border-rose-500 focus:border-rose-500 focus:ring-rose-500" : "",
          className
        )}
        {...props}
      />
      {error && <p className="text-xs text-rose-400 mt-1">{error}</p>}
      {helperText && !error && <p className="text-xs text-slate-400 mt-1">{helperText}</p>}
    </div>
  );
}
