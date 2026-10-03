"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  ListTodo,
  Workflow,
  Plug,
  FolderKanban,
  Files,
  Settings,
  Cpu,
  Terminal,
  Activity,
  ChevronRight,
  BarChart3,
  Brain,
  ShieldCheck,
  RotateCcw,
  FlaskConical,
  Layers,
  Bell,
  Building2,
  FileCode2,
  Network,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { siteConfig } from "@/config/site";
import { OrganizationSelector } from "./OrganizationSelector";
import { WorkspaceSelector } from "./WorkspaceSelector";
import { hitlService } from "@/services/hitl";
import { notificationService } from "@/services/notifications";

const iconMap = {
  LayoutDashboard,
  ListTodo,
  Workflow,
  FileCode2,
  Layers,
  RotateCcw,
  FlaskConical,
  ShieldCheck,
  Plug,
  Brain,
  Network,
  FolderKanban,
  Files,
  BarChart3,
  Cpu,
  Terminal,
  Bell,
  Settings,
  Building2,
};

export function AppSidebar({ className = "", onCloseMobile }) {
  const pathname = usePathname();
  const [pendingCount, setPendingCount] = React.useState(0);
  const [unreadNotifCount, setUnreadNotifCount] = React.useState(0);

  React.useEffect(() => {
    let mounted = true;
    const fetchCounters = async () => {
      try {
        const [hitlRes, notifRes] = await Promise.allSettled([
          hitlService.listRequests({ status: "pending", limit: 50 }),
          notificationService.getUnreadCount(),
        ]);
        if (mounted) {
          if (hitlRes.status === "fulfilled" && Array.isArray(hitlRes.value)) {
            setPendingCount(hitlRes.value.length);
          }
          if (notifRes.status === "fulfilled" && notifRes.value?.unread_count !== undefined) {
            setUnreadNotifCount(notifRes.value.unread_count);
          }
        }
      } catch (err) {
        // Silent error in background counter
      }
    };
    fetchCounters();
    const interval = setInterval(fetchCounters, 45000);
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, [pathname]);

  return (
    <aside
      className={cn(
        "flex flex-col w-64 bg-slate-950 border-r border-slate-800/80 h-screen sticky top-0 shrink-0 select-none",
        className
      )}
    >
      {/* Brand Header */}
      <div className="p-4 border-b border-slate-850 flex items-center justify-between">
        <Link
          href="/"
          className="flex items-center gap-2.5 font-semibold text-sm text-slate-100 group"
          onClick={onCloseMobile}
        >
          <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center text-white shadow-md shadow-indigo-900/50 group-hover:bg-indigo-500 transition-colors">
            <Cpu className="w-4 h-4" />
          </div>
          <div className="flex flex-col">
            <span className="font-bold tracking-tight text-white">{siteConfig.name}</span>
            <span className="text-[10px] text-indigo-400 font-mono tracking-wider font-normal">
              v{siteConfig.version}
            </span>
          </div>
        </Link>
      </div>

      {/* Organization & Workspace Switchers */}
      <div className="p-3 border-b border-slate-850/60 space-y-2">
        <OrganizationSelector />
        <WorkspaceSelector />
      </div>

      {/* Navigation Sections */}
      <div className="flex-1 overflow-y-auto px-3 py-4 space-y-6">
        <div>
          <div className="px-2 pb-2 text-[10px] font-semibold uppercase tracking-wider text-slate-400">
            Work Orchestration
          </div>
          <nav className="space-y-1">
            {siteConfig.appNav.map((item) => {
              const Icon = iconMap[item.icon] || Terminal;
              const isActive =
                item.href === "/app"
                  ? pathname === "/app"
                  : pathname === item.href || pathname?.startsWith(`${item.href}/`);

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={onCloseMobile}
                  className={cn(
                    "flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium transition-all group",
                    isActive
                      ? "bg-indigo-600/15 text-indigo-300 border border-indigo-500/20 font-semibold"
                      : "text-slate-400 hover:text-slate-200 hover:bg-slate-900/80"
                  )}
                >
                  <div className="flex items-center gap-2.5">
                    <Icon
                      className={cn(
                        "w-4 h-4 transition-colors",
                        isActive ? "text-indigo-400" : "text-slate-400 group-hover:text-slate-300"
                      )}
                    />
                    <span>{item.label}</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    {item.href === "/app/approvals" && pendingCount > 0 && (
                      <span className="px-1.5 py-0.2 rounded-full text-[10px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">
                        {pendingCount}
                      </span>
                    )}
                    {item.href === "/app/notifications" && unreadNotifCount > 0 && (
                      <span className="px-1.5 py-0.2 rounded-full text-[10px] font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                        {unreadNotifCount}
                      </span>
                    )}
                    {isActive && <ChevronRight className="w-3.5 h-3.5 text-indigo-400/80" />}
                  </div>
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Engine Readiness Status */}
        <div className="pt-2">
          <div className="px-2 pb-2 text-[10px] font-semibold uppercase tracking-wider text-slate-400">
            Backend Target
          </div>
          <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800/80 space-y-2 text-xs">
            <div className="flex items-center justify-between">
              <span className="text-slate-400">Engine API</span>
              <span className="inline-flex items-center gap-1 text-[11px] font-mono text-cyan-400 bg-cyan-950/50 px-1.5 py-0.5 rounded border border-cyan-800/40">
                <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" />
                FastAPI:8000
              </span>
            </div>
            <div className="flex items-center justify-between text-[11px]">
              <span className="text-slate-400">Mode</span>
              <span className="text-slate-300 font-mono">Autonomous Routing</span>
            </div>
          </div>
        </div>
      </div>

      {/* Footer Info */}
      <div className="p-3 border-t border-slate-850/80 bg-slate-950/40">
        <div className="flex items-center gap-2 px-2 py-1 text-[11px] text-slate-400">
          <Activity className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
          <span>Core Orchestrator Ready</span>
        </div>
      </div>
    </aside>
  );
}
