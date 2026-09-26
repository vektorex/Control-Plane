import React from "react";
import { cn } from "@/lib/utils";

export function Table({ children, className = "", ...props }) {
  return (
    <div className="w-full overflow-x-auto">
      <table className={cn("w-full caption-bottom text-sm text-left", className)} {...props}>
        {children}
      </table>
    </div>
  );
}

export function TableHeader({ children, className = "", ...props }) {
  return (
    <thead className={cn("border-b border-slate-800 bg-slate-900/50 text-xs text-slate-400 font-medium uppercase tracking-wider", className)} {...props}>
      {children}
    </thead>
  );
}

export function TableBody({ children, className = "", ...props }) {
  return (
    <tbody className={cn("divide-y divide-slate-800/60 text-slate-200", className)} {...props}>
      {children}
    </tbody>
  );
}

export function TableRow({ children, className = "", hoverable = true, ...props }) {
  return (
    <tr
      className={cn(
        "transition-colors",
        hoverable && "hover:bg-slate-800/40",
        className
      )}
      {...props}
    >
      {children}
    </tr>
  );
}

export function TableHead({ children, className = "", ...props }) {
  return (
    <th className={cn("h-10 px-4 text-left align-middle font-medium text-slate-400", className)} {...props}>
      {children}
    </th>
  );
}

export function TableCell({ children, className = "", ...props }) {
  return (
    <td className={cn("p-4 align-middle", className)} {...props}>
      {children}
    </td>
  );
}
