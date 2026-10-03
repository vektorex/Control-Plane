"use client";

import React, { useState } from "react";
import { CheckSquare, UserCheck, Calendar, ArrowRight, CheckCircle2 } from "lucide-react";

export function AssignmentCard({
  assignments = [],
  currentUserId,
  onCreateAssignment,
  onUpdateStatus,
}) {
  const [assignedTo, setAssignedTo] = useState("");
  const [assignmentType, setAssignmentType] = useState("review");
  const [submitting, setSubmitting] = useState(false);
  const [isAdding, setIsAdding] = useState(false);

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!assignedTo.trim() || submitting) return;
    setSubmitting(true);
    try {
      await onCreateAssignment({
        assigned_to: assignedTo,
        assignment_type: assignmentType,
      });
      setAssignedTo("");
      setIsAdding(false);
    } finally {
      setSubmitting(false);
    }
  };

  const getTypeBadge = (type) => {
    const map = {
      review: "bg-blue-500/10 text-blue-400 border-blue-500/20",
      approval: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
      execution: "bg-purple-500/10 text-purple-400 border-purple-500/20",
      investigation: "bg-amber-500/10 text-amber-400 border-amber-500/20",
      implementation: "bg-indigo-500/10 text-indigo-400 border-indigo-500/20",
    };
    return map[type] || map.review;
  };

  return (
    <div className="flex flex-col gap-3 p-4 rounded-xl bg-slate-900/70 border border-slate-800">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <CheckSquare className="w-4 h-4 text-indigo-400" />
          <h4 className="text-xs font-semibold text-slate-200">Actionable Assignments ({assignments.length})</h4>
        </div>
        <button
          onClick={() => setIsAdding(!isAdding)}
          className="text-xs text-indigo-400 hover:text-indigo-300 font-medium"
        >
          {isAdding ? "Cancel" : "+ New"}
        </button>
      </div>

      {isAdding && (
        <form onSubmit={handleCreate} className="flex flex-col gap-2 p-2.5 rounded-lg bg-slate-950 border border-slate-800">
          <input
            type="text"
            value={assignedTo}
            onChange={(e) => setAssignedTo(e.target.value)}
            placeholder="Assignee User ID or Email..."
            className="w-full bg-slate-900 border border-slate-800 rounded px-2 py-1 text-xs text-slate-200 placeholder-slate-600 focus:outline-none focus:border-indigo-500"
          />
          <div className="flex items-center gap-2">
            <select
              value={assignmentType}
              onChange={(e) => setAssignmentType(e.target.value)}
              className="bg-slate-900 border border-slate-800 rounded px-2 py-1 text-xs text-slate-200 focus:outline-none"
            >
              <option value="review">Review</option>
              <option value="approval">Approval</option>
              <option value="execution">Execution</option>
              <option value="investigation">Investigation</option>
              <option value="implementation">Implementation</option>
            </select>
            <button
              type="submit"
              disabled={submitting || !assignedTo.trim()}
              className="px-3 py-1 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded text-xs font-medium ml-auto"
            >
              Assign
            </button>
          </div>
        </form>
      )}

      <div className="flex flex-col gap-2 max-h-[220px] overflow-y-auto">
        {assignments.length === 0 ? (
          <div className="text-center py-4 text-slate-500 text-xs">No pending assignments.</div>
        ) : (
          assignments.map((a) => (
            <div
              key={a.id}
              className="flex items-center justify-between p-2.5 rounded-lg bg-slate-950/70 border border-slate-800/80 text-xs"
            >
              <div className="flex items-center gap-2">
                <span className={`px-2 py-0.5 rounded border text-[10px] font-semibold uppercase ${getTypeBadge(a.assignment_type)}`}>
                  {a.assignment_type}
                </span>
                <span className="text-slate-300 font-medium">To: {a.assigned_to.slice(0, 10)}</span>
              </div>

              <div className="flex items-center gap-2">
                <span
                  className={`text-[10px] px-1.5 py-0.5 rounded ${
                    a.status === "completed"
                      ? "text-emerald-400 bg-emerald-500/10"
                      : a.status === "accepted"
                      ? "text-blue-400 bg-blue-500/10"
                      : "text-amber-400 bg-amber-500/10"
                  }`}
                >
                  {a.status}
                </span>

                {a.status !== "completed" && onUpdateStatus && (
                  <button
                    onClick={() => onUpdateStatus(a.id, a.status === "pending" ? "accepted" : "completed")}
                    className="p-1 hover:text-emerald-400 text-slate-400 transition-colors"
                    title={a.status === "pending" ? "Accept assignment" : "Mark completed"}
                  >
                    <CheckCircle2 className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
