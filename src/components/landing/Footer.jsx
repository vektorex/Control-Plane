import React from "react";
import Link from "next/link";
import { Cpu } from "lucide-react";
import { GithubIcon } from "@/components/ui/Icons";
import { siteConfig } from "@/config/site";

export function LandingFooter() {
  return (
    <footer className="border-t border-slate-800 bg-slate-950 text-slate-400 text-xs py-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-lg bg-indigo-600 flex items-center justify-center text-white">
              <Cpu className="w-4 h-4" />
            </div>
            <div>
              <span className="font-bold text-slate-200">{siteConfig.name}</span>
              <p className="text-[11px] text-slate-400 mt-0.5">{siteConfig.tagline}</p>
            </div>
          </div>

          <div className="flex items-center gap-6">
            <Link href="/app" className="hover:text-slate-200 transition-colors">
              Workspace App
            </Link>
            <Link href="/app/tasks" className="hover:text-slate-200 transition-colors">
              Tasks
            </Link>
            <Link href="/app/projects" className="hover:text-slate-200 transition-colors">
              Projects
            </Link>
            <Link href="/app/settings" className="hover:text-slate-200 transition-colors">
              Settings
            </Link>
            <a
              href={siteConfig.links.github}
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-1.5 text-slate-300 hover:text-white transition-colors"
            >
              <GithubIcon className="w-4 h-4" />
              <span>GitHub</span>
            </a>
          </div>
        </div>

        <div className="mt-8 pt-6 border-t border-slate-900 flex flex-col sm:flex-row items-center justify-between gap-4 text-[11px] text-slate-400">
          <p>© {new Date().getFullYear()} {siteConfig.name}. Universal Orchestration Layer.</p>
          <p className="font-mono text-slate-400">Production-Ready Foundation v{siteConfig.version}</p>
        </div>
      </div>
    </footer>
  );
}
