"use client";

import React from "react";
import Link from "next/link";
import {
  Package,
  Workflow,
  FileCode2,
  FlaskConical,
  Wrench,
  Plug,
  Layers,
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  Building2,
  Lock,
  Globe,
  Tag,
} from "lucide-react";

const TYPE_ICONS = {
  workflow: Workflow,
  prompt: FileCode2,
  evaluation: FlaskConical,
  tool: Wrench,
  connector_template: Plug,
  task_template: Layers,
  work_pack: Package,
};

export function PackageCard({ pkg, onInstallClick }) {
  const TypeIcon = TYPE_ICONS[pkg.package_type] || Package;

  return (
    <div className="flex flex-col justify-between p-5 rounded-xl border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 shadow-sm hover:border-neutral-300 dark:hover:border-neutral-700 transition-all">
      <div>
        {/* Header Badges */}
        <div className="flex items-center justify-between gap-2 mb-3">
          <div className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-neutral-100 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300">
            <TypeIcon className="w-3.5 h-3.5 text-blue-500" />
            <span className="capitalize">{pkg.package_type?.replace("_", " ")}</span>
          </div>

          <div className="flex items-center gap-1.5">
            {pkg.visibility === "public" ? (
              <span className="flex items-center gap-1 text-[11px] text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/40 px-2 py-0.5 rounded-full">
                <Globe className="w-3 h-3" /> Public
              </span>
            ) : pkg.visibility === "organization" ? (
              <span className="flex items-center gap-1 text-[11px] text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/40 px-2 py-0.5 rounded-full">
                <Building2 className="w-3 h-3" /> Org
              </span>
            ) : (
              <span className="flex items-center gap-1 text-[11px] text-neutral-500 dark:text-neutral-400 bg-neutral-100 dark:bg-neutral-800 px-2 py-0.5 rounded-full">
                <Lock className="w-3 h-3" /> Private
              </span>
            )}

            {pkg.status === "published" && (
              <span className="flex items-center gap-0.5 text-[11px] text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/40 px-2 py-0.5 rounded-full">
                <ShieldCheck className="w-3 h-3" /> Published
              </span>
            )}
            {pkg.status === "review" && (
              <span className="flex items-center gap-0.5 text-[11px] text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/40 px-2 py-0.5 rounded-full">
                <AlertTriangle className="w-3 h-3" /> In Review
              </span>
            )}
            {pkg.status === "suspended" && (
              <span className="flex items-center gap-0.5 text-[11px] text-rose-600 dark:text-rose-400 bg-rose-50 dark:bg-rose-950/40 px-2 py-0.5 rounded-full">
                <ShieldAlert className="w-3 h-3" /> Suspended
              </span>
            )}
            {pkg.status === "draft" && (
              <span className="text-[11px] text-neutral-500 bg-neutral-100 dark:bg-neutral-800 px-2 py-0.5 rounded-full">
                Draft
              </span>
            )}
          </div>
        </div>

        {/* Title & Slug */}
        <Link
          href={`/app/marketplace/packages/${pkg.slug}`}
          className="group block"
        >
          <h3 className="text-base font-semibold text-neutral-900 dark:text-neutral-100 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
            {pkg.name}
          </h3>
          <p className="text-xs text-neutral-400 font-mono mt-0.5">{pkg.slug}</p>
        </Link>

        {/* Description */}
        <p className="text-xs text-neutral-600 dark:text-neutral-300 mt-2 line-clamp-2 leading-relaxed">
          {pkg.description || "No description provided."}
        </p>

        {/* Tags */}
        {pkg.tags && pkg.tags.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-3">
            {pkg.tags.slice(0, 4).map((tag, idx) => (
              <span
                key={idx}
                className="flex items-center gap-0.5 text-[10px] text-neutral-500 dark:text-neutral-400 bg-neutral-50 dark:bg-neutral-800/80 px-1.5 py-0.5 rounded border border-neutral-200 dark:border-neutral-700/50"
              >
                <Tag className="w-2.5 h-2.5" />
                {tag}
              </span>
            ))}
            {pkg.tags.length > 4 && (
              <span className="text-[10px] text-neutral-400 self-center">
                +{pkg.tags.length - 4}
              </span>
            )}
          </div>
        )}
      </div>

      {/* Footer Meta & Actions */}
      <div className="mt-5 pt-3 border-t border-neutral-100 dark:border-neutral-800/80 flex items-center justify-between text-xs">
        <div className="text-neutral-500 dark:text-neutral-400">
          <span className="font-medium text-neutral-700 dark:text-neutral-300">
            {pkg.current_version?.version || "v0.0.0"}
          </span>
          <span className="mx-1.5">•</span>
          <span className="capitalize">{pkg.category}</span>
        </div>

        <div className="flex items-center gap-2">
          <Link
            href={`/app/marketplace/packages/${pkg.slug}`}
            className="text-xs font-medium text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-white px-2 py-1"
          >
            Details
          </Link>
          {pkg.status === "published" && onInstallClick && (
            <button
              onClick={() => onInstallClick(pkg)}
              className="text-xs font-semibold px-3 py-1 rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition-colors shadow-xs"
            >
              Install
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
