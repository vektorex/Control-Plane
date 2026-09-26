import React from "react";
import { cn } from "@/lib/utils";

export function Avatar({ name = "Workspace User", src, size = "md", className = "" }) {
  const sizes = {
    sm: "w-7 h-7 text-[10px]",
    md: "w-8 h-8 text-xs",
    lg: "w-10 h-10 text-sm",
  };

  const getInitials = (n) => {
    if (!n) return "U";
    const parts = n.split(" ").filter(Boolean);
    if (parts.length >= 2) return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
    return n.slice(0, 2).toUpperCase();
  };

  if (src) {
    return (
      // eslint-disable-next-line @next/next/no-img-element
      <img
        src={src}
        alt={name}
        className={cn("rounded-full object-cover border border-slate-700", sizes[size], className)}
      />
    );
  }

  return (
    <div
      className={cn(
        "rounded-full bg-gradient-to-tr from-indigo-600 to-indigo-400 text-white font-semibold flex items-center justify-center border border-indigo-300/30 select-none shadow-sm",
        sizes[size],
        className
      )}
      title={name}
    >
      {getInitials(name)}
    </div>
  );
}
