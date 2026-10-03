"use client";

import React from "react";
import { Search, Filter, X } from "lucide-react";

export function PackageFilters({
  search,
  setSearch,
  category,
  setCategory,
  packageType,
  setPackageType,
  visibility,
  setVisibility,
  categories = [],
  packageTypes = [
    { value: "", label: "All Types" },
    { value: "work_pack", label: "Work Packs" },
    { value: "workflow", label: "Workflows" },
    { value: "prompt", label: "Prompts" },
    { value: "tool", label: "Tools" },
    { value: "connector_template", label: "Connector Templates" },
    { value: "task_template", label: "Task Templates" },
    { value: "evaluation", label: "Evaluations" },
  ],
  onReset,
}) {
  const hasFilters = search || category || packageType || visibility;

  return (
    <div className="flex flex-col md:flex-row gap-3 items-stretch md:items-center justify-between p-3.5 rounded-xl border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 shadow-xs">
      <div className="flex-1 relative">
        <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-neutral-400" />
        <input
          type="text"
          placeholder="Search packages by name, description, tags..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full pl-9 pr-4 py-2 text-xs rounded-lg border border-neutral-200 dark:border-neutral-700 bg-neutral-50 dark:bg-neutral-800 text-neutral-900 dark:text-neutral-100 placeholder-neutral-400 focus:outline-hidden focus:ring-1 focus:ring-blue-500"
        />
      </div>

      <div className="flex flex-wrap items-center gap-2">
        {/* Category */}
        <select
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          className="text-xs px-2.5 py-2 rounded-lg border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-800 text-neutral-800 dark:text-neutral-200 focus:outline-hidden focus:ring-1 focus:ring-blue-500"
        >
          <option value="">All Categories</option>
          {categories.map((cat) => (
            <option key={cat.id || cat.slug || cat} value={cat.slug || cat}>
              {cat.name || cat}
            </option>
          ))}
        </select>

        {/* Package Type */}
        <select
          value={packageType}
          onChange={(e) => setPackageType(e.target.value)}
          className="text-xs px-2.5 py-2 rounded-lg border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-800 text-neutral-800 dark:text-neutral-200 focus:outline-hidden focus:ring-1 focus:ring-blue-500"
        >
          {packageTypes.map((pt) => (
            <option key={pt.value} value={pt.value}>
              {pt.label}
            </option>
          ))}
        </select>

        {/* Visibility */}
        <select
          value={visibility}
          onChange={(e) => setVisibility(e.target.value)}
          className="text-xs px-2.5 py-2 rounded-lg border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-800 text-neutral-800 dark:text-neutral-200 focus:outline-hidden focus:ring-1 focus:ring-blue-500"
        >
          <option value="">All Visibilities</option>
          <option value="public">Public</option>
          <option value="organization">Organization</option>
          <option value="private">Private</option>
        </select>

        {hasFilters && (
          <button
            onClick={onReset}
            className="flex items-center gap-1 text-xs text-neutral-500 hover:text-neutral-800 dark:hover:text-neutral-200 px-2 py-2 rounded-lg hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-colors"
          >
            <X className="w-3.5 h-3.5" />
            Reset
          </button>
        )}
      </div>
    </div>
  );
}
