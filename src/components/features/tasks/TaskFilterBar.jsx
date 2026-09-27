import React from "react";
import { Search } from "lucide-react";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";

export function TaskFilterBar({
  searchQuery,
  onSearchChange,
  statusFilter,
  onStatusFilterChange,
}) {
  return (
    <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 w-full">
      <div className="flex-1">
        <Input
          placeholder="Filter tasks by title, description, or UUID..."
          icon={Search}
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          className="bg-slate-900/90"
        />
      </div>

      <div className="w-full sm:w-48">
        <Select
          value={statusFilter}
          onChange={(e) => onStatusFilterChange(e.target.value)}
          options={[
            { value: "ALL", label: "All Statuses" },
            { value: "draft", label: "Draft" },
            { value: "active", label: "Active" },
            { value: "completed", label: "Completed" },
            { value: "archived", label: "Archived" },
          ]}
        />
      </div>
    </div>
  );
}
