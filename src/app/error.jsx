"use client";

import React, { useEffect } from "react";
import { AlertTriangle, RefreshCw, Home } from "lucide-react";
import { Button } from "@/components/ui/Button";
import Link from "next/link";

export default function RootError({ error, reset }) {
  useEffect(() => {
    console.error("[WorkLayer App Error]", error);
  }, [error]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#07090e] p-6">
      <div className="max-w-md w-full p-8 rounded-2xl bg-slate-900 border border-slate-800 text-center shadow-2xl space-y-6">
        <div className="w-12 h-12 rounded-xl bg-rose-950/60 border border-rose-800/80 text-rose-400 mx-auto flex items-center justify-center">
          <AlertTriangle className="w-6 h-6" />
        </div>

        <div>
          <h1 className="text-lg font-bold text-slate-100">Application Error</h1>
          <p className="text-xs text-slate-400 mt-2 leading-relaxed">
            {error?.message || "An unexpected error occurred while executing orchestrator components."}
          </p>
        </div>

        <div className="flex items-center justify-center gap-3">
          <Button variant="secondary" size="sm" onClick={() => reset()} icon={RefreshCw}>
            Try Again
          </Button>
          <Link href="/">
            <Button variant="primary" size="sm" icon={Home}>
              Return Home
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
}
