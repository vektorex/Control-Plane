"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { AppSidebar } from "@/components/shell/AppSidebar";
import { AppHeader } from "@/components/shell/AppHeader";
import { useAuth } from "@/lib/authContext";
import { Loader2, ShieldCheck } from "lucide-react";

export default function AppShellLayout({ children }) {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    if (!loading && !user) {
      router.push("/login");
    }
  }, [user, loading, router]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-[#07090e] text-slate-100 space-y-4">
        <div className="relative flex items-center justify-center w-16 h-16 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
          <Loader2 className="w-8 h-8 animate-spin" />
        </div>
        <div className="text-center">
          <p className="text-sm font-medium text-slate-300">Resolving workspace session...</p>
          <p className="text-xs text-slate-500 mt-1">Verifying authenticated identity</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return null; // Will redirect in useEffect
  }

  return (
    <div className="flex h-screen overflow-hidden bg-[#07090e] text-slate-100">
      {/* Desktop Sidebar */}
      <div className="hidden md:flex md:shrink-0">
        <AppSidebar />
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="fixed inset-0 z-50 flex md:hidden">
          <div
            className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm"
            onClick={() => setMobileMenuOpen(false)}
          />
          <div className="relative flex-1 flex flex-col max-w-xs w-full bg-slate-950">
            <AppSidebar onCloseMobile={() => setMobileMenuOpen(false)} />
          </div>
        </div>
      )}

      {/* Main Content Area */}
      <div className="flex flex-col flex-1 min-w-0 overflow-hidden">
        <AppHeader onToggleMobile={() => setMobileMenuOpen(!mobileMenuOpen)} />
        <main className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8 bg-[#080b12]">
          <div className="max-w-7xl mx-auto space-y-6">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
