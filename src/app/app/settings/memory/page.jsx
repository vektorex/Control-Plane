"use client";

import React from "react";
import Link from "next/link";
import { Brain, ChevronLeft } from "lucide-react";
import { MemorySettingsForm } from "@/components/features/settings/MemorySettingsForm";
import { Button } from "@/components/ui/Button";

export default function MemorySettingsPage() {
  return (
    <div className="space-y-6 max-w-4xl mx-auto pb-12">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div className="flex items-center gap-3">
          <Link href="/app/settings">
            <Button variant="ghost" size="sm" className="h-8 px-2 text-slate-400 hover:text-slate-200">
              <ChevronLeft className="w-4 h-4 mr-1" />
              Settings
            </Button>
          </Link>
          <div className="h-4 w-px bg-slate-800" />
          <h1 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <Brain className="w-5 h-5 text-indigo-400" />
            Memory & Persistent Context Settings
          </h1>
        </div>
      </div>

      <MemorySettingsForm />
    </div>
  );
}
