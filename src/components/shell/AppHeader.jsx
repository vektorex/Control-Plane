"use client";

import React from "react";
import { usePathname } from "next/navigation";
import Link from "next/link";
import { Menu, Search, ChevronRight, Activity } from "lucide-react";
import { UserDropdown } from "./UserDropdown";

export function AppHeader({ onToggleMobile }) {
  const pathname = usePathname();

  // Generate breadcrumb items
  const pathSegments = pathname.split("/").filter(Boolean);
  const breadcrumbs = pathSegments.map((segment, index) => {
    const href = "/" + pathSegments.slice(0, index + 1).join("/");
    const label = segment.charAt(0).toUpperCase() + segment.slice(1);
    const isLast = index === pathSegments.length - 1;
    return { href, label, isLast };
  });

  return (
    <header className="h-14 border-b border-slate-800 bg-slate-950/80 backdrop-blur-md sticky top-0 z-30 px-4 flex items-center justify-between gap-4">
      <div className="flex items-center gap-3 min-w-0">
        <button
          onClick={onToggleMobile}
          className="md:hidden p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          aria-label="Toggle navigation menu"
        >
          <Menu className="w-5 h-5" />
        </button>

        {/* Breadcrumb Navigation */}
        <nav aria-label="Breadcrumb" className="flex items-center gap-1.5 text-xs text-slate-400 overflow-hidden">
          <Link href="/app" className="hover:text-slate-200 transition-colors shrink-0">
            Workspace
          </Link>
          {breadcrumbs.map((crumb) => (
            <React.Fragment key={crumb.href}>
              <ChevronRight className="w-3.5 h-3.5 text-slate-400 shrink-0" />
              {crumb.isLast ? (
                <span className="font-semibold text-slate-100 truncate">{crumb.label}</span>
              ) : (
                <Link href={crumb.href} className="hover:text-slate-200 transition-colors truncate">
                  {crumb.label}
                </Link>
              )}
            </React.Fragment>
          ))}
        </nav>
      </div>

      {/* Header Actions */}
      <div className="flex items-center gap-3 shrink-0">
        {/* Quick Search Shell */}
        <button
          type="button"
          onClick={() => {}}
          className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 hover:border-slate-700 text-xs text-slate-400 hover:text-slate-300 transition-colors cursor-pointer"
        >
          <Search className="w-3.5 h-3.5" />
          <span>Search tasks, projects, tools...</span>
          <kbd className="hidden lg:inline-block text-[10px] bg-slate-800 text-slate-400 px-1.5 py-0.5 rounded font-mono border border-slate-700">
            Ctrl+K
          </kbd>
        </button>

        {/* System Status Pill */}
        <div className="hidden lg:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-900 border border-slate-800 text-[11px] text-slate-300">
          <Activity className="w-3 h-3 text-emerald-400 animate-pulse" />
          <span className="text-slate-400">Layer:</span>
          <span className="text-slate-200 font-mono">FastAPI Target Ready</span>
        </div>

        {/* User Menu */}
        <UserDropdown />
      </div>
    </header>
  );
}
