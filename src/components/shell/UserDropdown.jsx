"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Avatar } from "@/components/ui/Avatar";
import { ChevronDown, Settings, LogOut, ExternalLink, HelpCircle, KeyRound } from "lucide-react";
import { siteConfig } from "@/config/site";

export function UserDropdown() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 p-1.5 rounded-lg hover:bg-slate-800 transition-colors cursor-pointer text-left"
        aria-label="User profile menu"
      >
        <Avatar name="Rayulu Mukku" size="sm" />
        <div className="hidden md:block text-left">
          <div className="text-xs font-medium text-slate-200 leading-none">Rayulu Mukku</div>
          <div className="text-[10px] text-slate-400 mt-0.5">Admin / Developer</div>
        </div>
        <ChevronDown className="w-3.5 h-3.5 text-slate-400 hidden md:block" />
      </button>

      {isOpen && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setIsOpen(false)} />
          <div className="absolute right-0 top-full mt-2 w-56 bg-slate-900 border border-slate-700 rounded-xl shadow-2xl py-1.5 z-50 text-xs animate-in fade-in zoom-in-95 duration-100">
            <div className="px-3 py-2 border-b border-slate-800">
              <p className="font-medium text-slate-100">Rayulu Mukku</p>
              <p className="text-[11px] text-slate-400 truncate">rayulu@worklayer.internal</p>
            </div>

            <div className="py-1">
              <Link
                href="/app/settings"
                onClick={() => setIsOpen(false)}
                className="flex items-center gap-2 px-3 py-2 text-slate-300 hover:bg-slate-800 hover:text-white transition-colors"
              >
                <Settings className="w-3.5 h-3.5" />
                <span>Account & Settings</span>
              </Link>
              <Link
                href="/app/settings"
                onClick={() => setIsOpen(false)}
                className="flex items-center gap-2 px-3 py-2 text-slate-300 hover:bg-slate-800 hover:text-white transition-colors"
              >
                <KeyRound className="w-3.5 h-3.5" />
                <span>API Keys & Credentials</span>
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
                  <HelpCircle className="w-3.5 h-3.5" />
                  <span>GitHub Repository</span>
                </div>
                <ExternalLink className="w-3 h-3 text-slate-500" />
              </a>
            </div>

            <div className="border-t border-slate-800 pt-1">
              <Link
                href="/"
                onClick={() => setIsOpen(false)}
                className="flex items-center gap-2 px-3 py-2 text-rose-400 hover:bg-rose-950/40 hover:text-rose-300 transition-colors"
              >
                <LogOut className="w-3.5 h-3.5" />
                <span>Exit App Shell</span>
              </Link>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
