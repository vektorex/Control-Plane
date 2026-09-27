"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Avatar } from "@/components/ui/Avatar";
import { ChevronDown, Settings, LogOut, ExternalLink, HelpCircle, KeyRound, User } from "lucide-react";
import { siteConfig } from "@/config/site";
import { useAuth } from "@/lib/authContext";

export function UserDropdown() {
  const [isOpen, setIsOpen] = useState(false);
  const { user, signOut } = useAuth();

  const userEmail = user?.email || "developer@worklayer.internal";
  const displayName = user?.email ? user.email.split("@")[0] : "Authenticated User";

  const handleLogout = async () => {
    setIsOpen(false);
    await signOut();
  };

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 p-1.5 rounded-lg hover:bg-slate-800 transition-colors cursor-pointer text-left"
        aria-label="User profile menu"
      >
        <Avatar name={displayName} size="sm" />
        <div className="hidden md:block text-left max-w-[140px]">
          <div className="text-xs font-medium text-slate-200 leading-none truncate">{displayName}</div>
          <div className="text-[10px] text-slate-400 mt-0.5 truncate">{userEmail}</div>
        </div>
        <ChevronDown className="w-3.5 h-3.5 text-slate-400 hidden md:block" />
      </button>

      {isOpen && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setIsOpen(false)} />
          <div className="absolute right-0 top-full mt-2 w-60 bg-slate-900 border border-slate-700 rounded-xl shadow-2xl py-1.5 z-50 text-xs animate-in fade-in zoom-in-95 duration-100">
            <div className="px-3 py-2 border-b border-slate-800">
              <p className="font-semibold text-slate-100 capitalize truncate">{displayName}</p>
              <p className="text-[11px] text-slate-400 truncate">{userEmail}</p>
            </div>

            <div className="py-1">
              <Link
                href="/app/settings"
                onClick={() => setIsOpen(false)}
                className="flex items-center gap-2 px-3 py-2 text-slate-300 hover:bg-slate-800 hover:text-white transition-colors"
              >
                <Settings className="w-3.5 h-3.5 text-slate-400" />
                <span>Account & Settings</span>
              </Link>
            </div>

            <div className="border-t border-slate-800 py-1">
              <a
                href={siteConfig.links.github}
                target="_blank"
                rel="noreferrer"
                className="flex items-center justify-between px-3 py-2 text-slate-300 hover:bg-slate-800 hover:text-white transition-colors"
              >
                <div className="flex items-center gap-2">
                  <HelpCircle className="w-3.5 h-3.5 text-slate-400" />
                  <span>Documentation / GitHub</span>
                </div>
                <ExternalLink className="w-3 h-3 text-slate-500" />
              </a>
            </div>

            <div className="border-t border-slate-800 pt-1">
              <button
                type="button"
                onClick={handleLogout}
                className="w-full flex items-center gap-2 px-3 py-2 text-rose-400 hover:bg-rose-950/40 hover:text-rose-300 transition-colors cursor-pointer text-left"
              >
                <LogOut className="w-3.5 h-3.5" />
                <span>Sign Out</span>
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
