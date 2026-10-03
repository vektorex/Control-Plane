"use client";

import React from "react";
import {
  Clock,
  ShieldAlert,
  AlertTriangle,
  Lock,
  CheckCircle2,
  XCircle,
  Activity,
  FileCheck,
  User,
  Workflow,
} from "lucide-react";

export function IncidentTimelineViewer({ events = [] }) {
  const getEventBadge = (type) => {
    switch (type) {
      case "observed_event":
        return {
          icon: <Activity className="w-4 h-4 text-blue-400" />,
          color: "border-blue-500/40 bg-blue-950/30 text-blue-400",
          label: "Observed Event",
        };
      case "signal_detected":
        return {
          icon: <ShieldAlert className="w-4 h-4 text-amber-400" />,
          color: "border-amber-500/40 bg-amber-950/30 text-amber-400",
          label: "Signal Detected",
        };
      case "incident_correlated":
      case "correlation":
        return {
          icon: <Workflow className="w-4 h-4 text-purple-400" />,
          color: "border-purple-500/40 bg-purple-950/30 text-purple-400",
          label: "Correlation",
        };
      case "containment_requested":
        return {
          icon: <Lock className="w-4 h-4 text-orange-400" />,
          color: "border-orange-500/40 bg-orange-950/30 text-orange-400",
          label: "Containment Requested",
        };
      case "containment_executed":
      case "action":
        return {
          icon: <CheckCircle2 className="w-4 h-4 text-emerald-400" />,
          color: "border-emerald-500/40 bg-emerald-950/30 text-emerald-400",
          label: "Action Executed",
        };
      case "approval_granted":
      case "approval":
        return {
          icon: <FileCheck className="w-4 h-4 text-cyan-400" />,
          color: "border-cyan-500/40 bg-cyan-950/30 text-cyan-400",
          label: "Approval Granted",
        };
      default:
        return {
          icon: <Clock className="w-4 h-4 text-slate-400" />,
          color: "border-slate-700 bg-slate-800 text-slate-300",
          label: type,
        };
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm space-y-4">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div>
          <h3 className="text-base font-semibold text-white flex items-center gap-2">
            <Clock className="w-4 h-4 text-indigo-400" />
            Append-Only Incident Timeline
          </h3>
          <p className="text-xs text-slate-500">
            Chronological audit of observed activity, security detections, correlations, and containment.
          </p>
        </div>
        <span className="text-xs text-slate-500 font-mono">
          {events.length} {events.length === 1 ? "entry" : "entries"}
        </span>
      </div>

      {events.length === 0 ? (
        <div className="py-8 text-center text-slate-500 text-xs">
          No timeline events recorded for this incident yet.
        </div>
      ) : (
        <div className="relative pl-6 space-y-6 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-800">
          {events.map((evt, idx) => {
            const badge = getEventBadge(evt.event_type);
            const ts = new Date(evt.timestamp);
            return (
              <div key={evt.id || idx} className="relative group">
                {/* Timeline node icon */}
                <div className="absolute -left-6 top-0.5 flex items-center justify-center w-5 h-5 rounded-full bg-slate-950 border border-slate-700 group-hover:border-indigo-500 transition-colors">
                  <div className="w-2 h-2 rounded-full bg-indigo-400" />
                </div>

                <div className="bg-slate-950/70 border border-slate-800/80 rounded-lg p-3 hover:border-slate-700 transition-colors space-y-2">
                  <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
                    <div className="flex items-center gap-2">
                      <span className={`px-2 py-0.5 rounded text-[11px] font-semibold border flex items-center gap-1 ${badge.color}`}>
                        {badge.icon}
                        {badge.label}
                      </span>
                      <span className="text-slate-400 font-mono">
                        {evt.source_type} ({evt.source_id || "direct"})
                      </span>
                    </div>

                    <div className="text-slate-500 font-mono text-[11px] flex items-center gap-1">
                      <Clock className="w-3 h-3 text-slate-600" />
                      <span>{ts.toLocaleTimeString()}</span>
                      <span className="text-slate-600">({ts.toLocaleDateString()})</span>
                    </div>
                  </div>

                  <p className="text-xs text-slate-200 font-medium leading-relaxed">
                    {evt.summary}
                  </p>

                  <div className="flex items-center justify-between text-[11px] text-slate-500 pt-1 border-t border-slate-900">
                    <div className="flex items-center gap-1">
                      <User className="w-3 h-3 text-slate-600" />
                      <span>
                        Actor: {evt.actor_type || "system"}/{evt.actor_id || "internal"}
                      </span>
                    </div>
                    {evt.metadata && Object.keys(evt.metadata).length > 0 && (
                      <span className="font-mono text-slate-600">
                        {JSON.stringify(evt.metadata).substring(0, 45)}...
                      </span>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
