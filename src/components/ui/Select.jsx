import React from "react";
import { cn } from "@/lib/utils";

export function Select({
  label,
  options = [],
  value,
  onChange,
  error,
  helperText,
  className = "",
  containerClassName = "",
  id,
  placeholder = "Select an option",
  disabled = false,
  ...props
}) {
  const selectId = id || (label ? label.toLowerCase().replace(/\s+/g, "-") : undefined);

  return (
    <div className={cn("flex flex-col space-y-1.5 w-full", containerClassName)}>
      {label && (
        <label htmlFor={selectId} className="text-xs font-medium text-slate-300">
          {label}
        </label>
      )}
      <select
        id={selectId}
        value={value}
        onChange={onChange}
        disabled={disabled}
        className={cn(
          "w-full rounded-lg bg-slate-900 border border-slate-700 px-3.5 py-2 text-sm text-slate-100",
          "focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-colors",
          "disabled:opacity-50 disabled:bg-slate-800/50 disabled:cursor-not-allowed cursor-pointer",
          error ? "border-rose-500 focus:border-rose-500" : "",
          className
        )}
        {...props}
      >
        {placeholder && (
          <option value="" disabled className="bg-slate-900 text-slate-500">
            {placeholder}
          </option>
        )}
        {options.map((option) => {
          const optValue = typeof option === "object" ? option.value : option;
          const optLabel = typeof option === "object" ? option.label : option;
          return (
            <option key={optValue} value={optValue} className="bg-slate-900 text-slate-100 py-1">
              {optLabel}
            </option>
          );
        })}
      </select>
      {error && <p className="text-xs text-rose-400 mt-1">{error}</p>}
      {helperText && !error && <p className="text-xs text-slate-400 mt-1">{helperText}</p>}
    </div>
  );
}
