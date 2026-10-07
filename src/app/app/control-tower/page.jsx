"use client";

import React, { useState, useEffect } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Input } from "@/components/ui/Input";
import {
  Activity,
  AlertTriangle,
  Briefcase,
  CheckCircle2,
  Clock,
  Search,
  ShieldAlert,
  TerminalSquare,
  Network,
  ListTodo,
  RefreshCw,
  MoreVertical,
  Volume2
} from "lucide-react";
import { useWorkspace } from "@/lib/workspaceContext";
import { controlTowerService } from "@/services/controlTower";
import { formatDate, cn } from "@/lib/utils";

export default function ControlTowerPage() {
  const { activeWorkspace } = useWorkspace();
  const [overview, setOverview] = useState(null);
  const [attentionItems, setAttentionItems] = useState([]);
  const [searchResults, setSearchResults] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  const [isBriefing, setIsBriefing] = useState(false);
  const [briefing, setBriefing] = useState(null);

  const loadData = async () => {
    if (!activeWorkspace?.id) return;
    try {
      const [overviewData, attentionData] = await Promise.all([
        controlTowerService.getOverview(activeWorkspace.id),
        controlTowerService.getAttention(activeWorkspace.id),
      ]);
      setOverview(overviewData);
      setAttentionItems(attentionData || []);
    } catch (err) {
      console.error("[ControlTower] Error loading data", err);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, [activeWorkspace?.id]);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!searchQuery.trim() || !activeWorkspace?.id) return;
    setIsSearching(true);
    try {
      const res = await controlTowerService.search(searchQuery, activeWorkspace.id);
      setSearchResults(res.results || []);
    } catch (err) {
      console.error("[ControlTower] Search failed", err);
    } finally {
      setIsSearching(false);
    }
  };

  const handleAcknowledge = async (id) => {
    if (!activeWorkspace?.id) return;
    try {
      await controlTowerService.acknowledgeAttention(id, "current-user", activeWorkspace.id);
      loadData();
    } catch (err) {
      console.error("[ControlTower] Acknowledge failed", err);
    }
  };

  const handleGenerateBriefing = async () => {
    if (!activeWorkspace?.id) return;
    setIsBriefing(true);
    try {
      const res = await controlTowerService.generateBriefing("brief", activeWorkspace.id);
      setBriefing(res);
    } catch (err) {
      console.error("[ControlTower] Briefing failed", err);
    } finally {
      setIsBriefing(false);
    }
  };

  const getSeverityColor = (sev) => {
    switch (sev) {
      case "critical":
        return "bg-red-500/20 text-red-400 border-red-500/50";
      case "high":
        return "bg-orange-500/20 text-orange-400 border-orange-500/50";
      case "medium":
        return "bg-amber-500/20 text-amber-400 border-amber-500/50";
      default:
        return "bg-slate-500/20 text-slate-400 border-slate-500/50";
    }
  };

  const getIconForType = (type) => {
    switch (type) {
      case "security_incident":
        return <ShieldAlert className="w-5 h-5 text-red-400" />;
      case "job_failure":
        return <AlertTriangle className="w-5 h-5 text-orange-400" />;
      case "task_deadline":
        return <Clock className="w-5 h-5 text-amber-400" />;
      default:
        return <Activity className="w-5 h-5 text-blue-400" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner / Welcome */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-850">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Activity className="w-6 h-6 text-primary" />
            <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-white">
              Control Tower
            </h1>
          </div>
          <p className="text-slate-400 text-sm">
            Unified operational visibility, real-time metrics, and cross-system command.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" size="sm" onClick={loadData}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
          <Button
            variant="default"
            size="sm"
            onClick={handleGenerateBriefing}
            disabled={isBriefing}
            className="bg-indigo-600 hover:bg-indigo-700 text-white"
          >
            {isBriefing ? (
              <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <Volume2 className="w-4 h-4 mr-2" />
            )}
            Morning Briefing
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Metrics & Search */}
        <div className="lg:col-span-2 space-y-6">
          {/* Universal Search Box */}
          <Card className="bg-slate-900 border-slate-800 shadow-xl overflow-hidden">
            <div className="p-1">
              <form onSubmit={handleSearch} className="relative flex items-center">
                <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                <Input
                  className="w-full bg-transparent border-0 h-14 pl-12 pr-20 text-lg text-white focus-visible:ring-0 placeholder:text-slate-500"
                  placeholder="Search globally across jobs, workflows, incidents..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
                <Button
                  type="submit"
                  size="sm"
                  disabled={isSearching || !searchQuery.trim()}
                  className="absolute right-2 top-1/2 -translate-y-1/2"
                >
                  {isSearching ? <RefreshCw className="w-4 h-4 animate-spin" /> : "Search"}
                </Button>
              </form>
            </div>
            {searchResults.length > 0 && (
              <div className="border-t border-slate-800 p-4 max-h-64 overflow-y-auto">
                <h4 className="text-sm font-medium text-slate-400 mb-3 uppercase tracking-wider">Results</h4>
                <div className="space-y-2">
                  {searchResults.map((res, i) => (
                    <div key={i} className="p-3 bg-slate-850 hover:bg-slate-800 rounded-lg flex items-center justify-between transition-colors border border-slate-800/50 cursor-pointer">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded bg-slate-800 flex items-center justify-center shrink-0">
                          {res.entity_type === "task" ? <ListTodo className="w-4 h-4 text-emerald-400" /> :
                           res.entity_type === "job" ? <TerminalSquare className="w-4 h-4 text-blue-400" /> :
                           res.entity_type === "security_incident" ? <ShieldAlert className="w-4 h-4 text-red-400" /> :
                           <Activity className="w-4 h-4 text-slate-400" />}
                        </div>
                        <div>
                          <p className="text-sm font-medium text-slate-200">{res.title}</p>
                          <p className="text-xs text-slate-500 capitalize">{res.entity_type} • ID: {res.entity_id.split("-")[0]}</p>
                        </div>
                      </div>
                      <Badge variant="outline" className="bg-slate-900 border-slate-700">{res.status}</Badge>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </Card>

          {/* Aggregated Overview */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <Card className="bg-slate-900 border-slate-800">
              <CardContent className="p-4 flex flex-col items-center justify-center text-center">
                <ListTodo className="w-6 h-6 text-emerald-400 mb-2" />
                <p className="text-3xl font-bold text-white">{overview?.sections?.active_tasks?.count || 0}</p>
                <p className="text-xs text-slate-400 mt-1 uppercase tracking-wider font-medium">Active Tasks</p>
              </CardContent>
            </Card>
            <Card className="bg-slate-900 border-slate-800">
              <CardContent className="p-4 flex flex-col items-center justify-center text-center">
                <TerminalSquare className="w-6 h-6 text-blue-400 mb-2" />
                <p className="text-3xl font-bold text-white">{overview?.sections?.running_jobs?.count || 0}</p>
                <p className="text-xs text-slate-400 mt-1 uppercase tracking-wider font-medium">Running Jobs</p>
              </CardContent>
            </Card>
            <Card className="bg-slate-900 border-slate-800 relative overflow-hidden group">
              <div className="absolute inset-0 bg-red-500/5 group-hover:bg-red-500/10 transition-colors" />
              <CardContent className="p-4 flex flex-col items-center justify-center text-center relative z-10">
                <ShieldAlert className="w-6 h-6 text-red-400 mb-2" />
                <p className="text-3xl font-bold text-white">{overview?.sections?.open_security_incidents?.count || 0}</p>
                <p className="text-xs text-slate-400 mt-1 uppercase tracking-wider font-medium">Security Alerts</p>
              </CardContent>
            </Card>
            <Card className="bg-slate-900 border-slate-800">
              <CardContent className="p-4 flex flex-col items-center justify-center text-center">
                <AlertTriangle className="w-6 h-6 text-orange-400 mb-2" />
                <p className="text-3xl font-bold text-white">{overview?.sections?.failed_jobs?.count || 0}</p>
                <p className="text-xs text-slate-400 mt-1 uppercase tracking-wider font-medium">Failed Jobs</p>
              </CardContent>
            </Card>
          </div>

          {/* Briefing Area */}
          {briefing && (
            <Card className="bg-gradient-to-br from-indigo-950/40 to-slate-900 border-indigo-500/30">
              <CardHeader className="pb-2">
                <CardTitle className="text-lg flex items-center gap-2 text-indigo-300">
                  <Volume2 className="w-5 h-5" />
                  Morning Briefing
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-3">
                  {briefing.statements.map((stmt, i) => (
                    <li key={i} className="flex gap-3 text-slate-300 text-sm">
                      <span className="shrink-0 mt-0.5 w-1.5 h-1.5 rounded-full bg-indigo-500/50" />
                      <span>{stmt}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}

          {/* System Status / Health (Mocked visually as requested to not fabricate backend data, but using UI to represent overview state) */}
          <Card className="bg-slate-900 border-slate-800">
            <CardHeader className="pb-2">
              <CardTitle className="text-lg">Subsystem Operational Status</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {["Tasks & Workflows", "Job Execution", "Security Operations"].map((sys) => {
                   let sysStatus = "healthy";
                   let sysColor = "text-emerald-400";
                   if (sys === "Tasks & Workflows" && (overview?.sections?.active_tasks?.count > 50)) {
                       sysStatus = "high_load"; sysColor = "text-amber-400";
                   }
                   if (sys === "Job Execution" && (overview?.sections?.failed_jobs?.count > 0)) {
                       sysStatus = "degraded"; sysColor = "text-orange-400";
                   }
                   if (sys === "Security Operations" && (overview?.sections?.open_security_incidents?.count > 0)) {
                       sysStatus = "alert"; sysColor = "text-red-400";
                   }

                   return (
                    <div key={sys} className="flex items-center justify-between p-3 rounded bg-slate-850/50 border border-slate-800">
                      <div className="flex items-center gap-3">
                        <Network className="w-4 h-4 text-slate-400" />
                        <span className="text-sm font-medium text-slate-200">{sys}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className={`text-xs uppercase font-bold tracking-wider ${sysColor}`}>{sysStatus.replace("_", " ")}</span>
                        <div className={`w-2 h-2 rounded-full ${sysStatus === 'healthy' ? 'bg-emerald-500' : sysStatus === 'high_load' ? 'bg-amber-500' : sysStatus === 'degraded' ? 'bg-orange-500' : 'bg-red-500'} animate-pulse`} />
                      </div>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right Column: Attention Feed */}
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-slate-200 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-amber-400" />
            Requires Attention
          </h3>
          <div className="space-y-3">
            {attentionItems.length === 0 ? (
              <Card className="bg-slate-900 border-slate-800 border-dashed">
                <CardContent className="p-8 flex flex-col items-center justify-center text-center">
                  <CheckCircle2 className="w-8 h-8 text-emerald-500 mb-3 opacity-50" />
                  <p className="text-sm text-slate-400">All clear! No items require immediate attention.</p>
                </CardContent>
              </Card>
            ) : (
              attentionItems.map((item) => (
                <Card key={item.id} className="bg-slate-900 border-slate-800 hover:border-slate-700 transition-colors">
                  <div className="p-4">
                    <div className="flex items-start justify-between gap-2 mb-2">
                      <div className="flex items-start gap-3">
                        <div className="mt-0.5">
                          {getIconForType(item.attention_type)}
                        </div>
                        <div>
                          <h4 className="text-sm font-medium text-slate-200 leading-tight">
                            {item.title}
                          </h4>
                          <p className="text-xs text-slate-400 mt-1">
                            {item.description}
                          </p>
                        </div>
                      </div>
                      <Badge variant="outline" className={cn("shrink-0 uppercase text-[10px]", getSeverityColor(item.severity))}>
                        {item.severity}
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between mt-4 pt-3 border-t border-slate-800">
                      <div className="text-[10px] text-slate-500">
                        {item.created_at ? formatDate(item.created_at) : 'Just now'}
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-7 text-xs text-indigo-400 hover:text-indigo-300 hover:bg-indigo-500/10"
                        onClick={() => handleAcknowledge(item.id)}
                      >
                        Acknowledge
                      </Button>
                    </div>
                  </div>
                </Card>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
