import React from "react";
import { Search, Filter, SlidersHorizontal } from "lucide-react";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";

export function TaskFilterBar({
  searchQuery,
  onSearchChange,
  statusFilter,
  onStatusFilterChange,
  priorityFilter,
  onPriorityFilterChange,
}) {
  return (
    <div className="flex flex-col md:flex-row items-stretch md:items-center gap-3 w-full">
      <div className="flex-1">
        <Input
          placeholder="Filter tasks by prompt, title, or ID..."
          icon={Search}
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          className="bg-slate-900/90"
        />
      </div>

      <div className="flex items-center gap-2">
        <div className="w-36">
          <Select
            value={statusFilter}
            onChange={(e) => onStatusFilterChange(e.target.value)}
            options={[
              { value: "ALL", label: "All Statuses" },
              { value: "PENDING", label: "Pending" },
              { value: "ROUTING", label: "Routing" },
              { value: "PROCESSING", label: "Processing" },
              { value: "COMPLETED", label: "Completed" },
              { value: "FAILED", label: "Failed" },
            ]}
            placeholder=""
          />
        </div>

        <div className="w-36">
          <Select
            value={priorityFilter}
            onChange={(e) => onPriorityFilterChange(e.target.value)}
            options={[
              { value: "ALL", label: "All Priorities" },
              { value: "low", label: "Low Priority" },
              { value: "medium", label: "Medium Priority" },
              { value: "high", label: "High Priority" },
              { value: "critical", label: "Critical" },
            ]}
            placeholder=""
          />
        </div>
      </div>
    </div>
  );
}
