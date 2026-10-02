"use client";

import React from "react";
import { usePathname } from "next/navigation";
import Link from "next/link";
import { Menu, Search, ChevronRight, Activity, Bell } from "lucide-react";
import { UserDropdown } from "./UserDropdown";
import { notificationService } from "@/services/notifications";
import { useWorkspace } from "@/lib/workspaceContext";
import { useEventStream } from "@/lib/events";

export function AppHeader({ onToggleMobile }) {
  const pathname = usePathname();
  const { activeWorkspace } = useWorkspace();
  const [unreadCount, setUnreadCount] = React.useState(0);

  const fetchUnread = React.useCallback(async () => {
    try {
      const res = await notificationService.getUnreadCount();
      if (res?.unread_count !== undefined) {
        setUnreadCount(res.unread_count);
      }
    } catch (e) {
      // silent
    }
  }, []);

  React.useEffect(() => {
    fetchUnread();
  }, [pathname, fetchUnread]);

  const { isConnected, isPollingFallback } = useEventStream({
    workspaceId: activeWorkspace?.id,
    eventType: "notification.*",
    onEvent: (event) => {
      if (event.type === "notification.created") {
        setUnreadCount((prev) => prev + 1);
      } else {
        fetchUnread();
      }
    },
    fallbackPollingInterval: 30000,
    fallbackPollingFn: fetchUnread,
  });

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

        {/* Real-time SSE Stream Status */}
        <div
          className="hidden md:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-900 border border-slate-800 text-[11px] text-slate-300"
          title={isConnected ? "Real-time Event Stream Connected" : isPollingFallback ? "Polling Fallback Active" : "Connecting to Event Stream..."}
        >
          <span
            className={`w-2 h-2 rounded-full ${
              isConnected ? "bg-emerald-400 animate-pulse" : isPollingFallback ? "bg-amber-400" : "bg-slate-500"
            }`}
          />
          <span className="text-slate-400 font-mono text-[10px]">
            {isConnected ? "LIVE SSE" : isPollingFallback ? "FALLBACK" : "SYNC"}
          </span>
        </div>

        {/* Notification Bell */}
        <Link
          href="/app/notifications"
          className="relative p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-900 border border-transparent hover:border-slate-800 transition-colors"
          title="Notification Center"
          aria-label="View notifications"
        >
          <Bell className="w-4 h-4" />
          {unreadCount > 0 && (
            <span className="absolute top-1.5 right-1.5 flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-indigo-500" />
            </span>
          )}
        </Link>

        {/* User Menu */}
        <UserDropdown />
      </div>
    </header>
  );
}
