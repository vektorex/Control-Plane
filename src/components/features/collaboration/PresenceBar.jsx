"use client";

import React from "react";
import { Users, Circle, Clock } from "lucide-react";

export function PresenceBar({ participants = [], currentUserId, onHeartbeat }) {
  const getStatusColor = (status) => {
    switch (status) {
      case "active":
        return "bg-emerald-500 ring-emerald-500/20";
      case "idle":
        return "bg-amber-500 ring-amber-500/20";
      case "away":
        return "bg-orange-500 ring-orange-500/20";
      default:
        return "bg-slate-400 ring-slate-400/20";
    }
  };

  const getRoleBadge = (role) => {
    const map = {
      owner: "bg-purple-500/10 text-purple-400 border-purple-500/20",
      editor: "bg-blue-500/10 text-blue-400 border-blue-500/20",
      reviewer: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
      viewer: "bg-slate-500/10 text-slate-400 border-slate-500/20",
    };
    return map[role] || map.viewer;
  };

  return (
    <div className="flex items-center justify-between px-4 py-2 bg-slate-900/60 border border-slate-800 rounded-lg text-xs backdrop-blur-md">
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-1.5 text-slate-400 font-medium">
          <Users className="w-3.5 h-3.5 text-indigo-400" />
          <span>Active Collaborators ({participants.filter((p) => p.status !== "offline").length})</span>
        </div>

        <div className="flex items-center -space-x-1.5 overflow-hidden">
          {participants.map((p) => {
            const isMe = p.user_id === currentUserId;
            return (
              <div
                key={p.id || p.user_id}
                title={`${p.user_id} (${p.role}) - ${p.status}`}
                className="relative group flex items-center justify-center w-7 h-7 rounded-full bg-slate-800 border-2 border-slate-900 text-[10px] font-semibold text-slate-200 cursor-pointer transition-transform hover:scale-110 hover:z-10"
              >
                <span>{p.user_id.slice(0, 2).toUpperCase()}</span>
                <span
                  className={`absolute -bottom-0.5 -right-0.5 w-2 h-2 rounded-full ring-2 ${getStatusColor(
                    p.status
                  )}`}
                />
              </div>
            );
          })}
        </div>
      </div>

      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2">
          {participants.slice(0, 3).map((p) => (
            <span
              key={`badge-${p.id || p.user_id}`}
              className={`px-2 py-0.5 rounded-full border text-[10px] font-medium ${getRoleBadge(p.role)}`}
            >
              {p.user_id.slice(0, 8)}: {p.role}
            </span>
          ))}
        </div>
        <div className="flex items-center gap-1 text-[11px] text-slate-500">
          <Clock className="w-3 h-3 text-slate-400" />
          <span>90s TTL Auto-expiring Presence</span>
        </div>
      </div>
    </div>
  );
}
