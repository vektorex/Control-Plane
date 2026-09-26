import React from "react";
import Link from "next/link";
import { Button } from "@/components/ui/Button";
import { HelpCircle, ArrowLeft, Home } from "lucide-react";

export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-[#07090e] p-6">
      <div className="max-w-md w-full p-8 rounded-2xl bg-slate-900 border border-slate-800 text-center shadow-2xl space-y-6">
        <div className="w-12 h-12 rounded-xl bg-indigo-950/60 border border-indigo-800/80 text-indigo-400 mx-auto flex items-center justify-center">
          <HelpCircle className="w-6 h-6" />
        </div>

        <div>
          <span className="font-mono text-xs text-indigo-400 font-bold uppercase tracking-wider">
            404 Error
          </span>
          <h1 className="text-xl font-bold text-slate-100 mt-1">Route Not Found</h1>
          <p className="text-xs text-slate-400 mt-2 leading-relaxed">
            The requested orchestration path or workspace resource does not exist in this layer.
          </p>
        </div>

        <div className="flex items-center justify-center gap-3">
          <Link href="/app">
            <Button variant="secondary" size="sm" icon={ArrowLeft}>
              To Dashboard
            </Button>
          </Link>
          <Link href="/">
            <Button variant="primary" size="sm" icon={Home}>
              Landing Page
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
}
