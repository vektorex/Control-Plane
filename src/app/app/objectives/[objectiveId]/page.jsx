"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { StatCard } from "@/components/ui/StatCard";
import { outcomeService } from "@/services/outcomes";
import {
  Target,
  ArrowLeft,
  Calendar,
  Clock,
  ShieldCheck,
  AlertTriangle,
  Award,
  CheckCircle2,
  ListTodo,
  Layers,
  Sparkles,
  ArrowRight,
  RefreshCw,
  GitPullRequest,
  Scale,
  Activity,
  Plus,
} from "lucide-react";

export default function ObjectiveDetailPage() {
  const params = useParams();
  const router = useRouter();
  const objectiveId = params.objectiveId;

  const [objective, setObjective] = useState(null);
  const [health, setHealth] = useState(null);
  const [targets, setTargets] = useState([]);
  const [milestones, setMilestones] = useState([]);
  const [outcomes, setOutcomes] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [objData, healthData, targetsData, milestonesData, outcomesData, recsData] =
        await Promise.allSettled([
          outcomeService.getObjective(objectiveId),
          outcomeService.getObjectiveHealth(objectiveId),
          outcomeService.listTargets(objectiveId),
          outcomeService.listMilestones(objectiveId),
          outcomeService.listOutcomes({ objectiveId }),
          outcomeService.getObjectiveRecommendations(objectiveId),
        ]);

      if (objData.status === "fulfilled") {
        setObjective(objData.value);
      } else {
        throw new Error(objData.reason?.message || "Failed to load objective");
      }

      if (healthData.status === "fulfilled") setHealth(healthData.value);
      if (targetsData.status === "fulfilled") setTargets(targetsData.value || []);
      if (milestonesData.status === "fulfilled") setMilestones(milestonesData.value || []);
      if (outcomesData.status === "fulfilled") setOutcomes(outcomesData.value || []);
      if (recsData.status === "fulfilled") setRecommendations(recsData.value?.recommendations || []);
    } catch (err) {
      console.error("[ObjectiveDetailPage] Error:", err);
      setError(err.message || "Failed to load objective details");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (objectiveId) fetchData();
  }, [objectiveId]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[50vh] space-y-4">
        <RefreshCw className="h-8 w-8 animate-spin text-indigo-400" />
        <p className="text-sm text-zinc-400">Loading objective intelligence...</p>
      </div>
    );
  }

  if (error || !objective) {
    return (
      <div className="max-w-4xl mx-auto space-y-4">
        <Link href="/app/objectives">
          <Button variant="ghost" size="sm" className="gap-2 text-zinc-400">
            <ArrowLeft className="h-4 w-4" /> Back to Objectives
          </Button>
        </Link>
        <Card className="p-8 text-center bg-rose-500/5 border-rose-500/20 text-rose-400">
          <AlertTriangle className="h-10 w-10 mx-auto mb-2 text-rose-400" />
          <h2 className="text-lg font-bold">Objective Not Found or Error</h2>
          <p className="text-sm text-zinc-400 mt-1">{error || "Could not retrieve objective data"}</p>
        </Card>
      </div>
    );
  }

  const getHealthBadge = (hStatus) => {
    switch (hStatus) {
      case "healthy":
        return <Badge className="bg-emerald-500/10 text-emerald-400 border-emerald-500/20">HEALTHY</Badge>;
      case "at_risk":
        return <Badge className="bg-amber-500/10 text-amber-400 border-amber-500/20">AT RISK</Badge>;
      case "blocked":
        return <Badge className="bg-rose-500/10 text-rose-400 border-rose-500/20">BLOCKED</Badge>;
      case "stale":
        return <Badge className="bg-zinc-700/50 text-zinc-300 border-zinc-600">STALE</Badge>;
      default:
        return <Badge className="bg-zinc-800 text-zinc-400 border-zinc-700">{hStatus || "UNKNOWN"}</Badge>;
    }
  };

  const completedMilestones = milestones.filter((m) => m.status === "completed").length;
  const verifiedOutcomes = outcomes.filter((o) => o.status === "verified").length;

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Top Breadcrumb & Nav */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link href="/app/objectives">
            <Button variant="ghost" size="sm" className="gap-2 text-zinc-400 hover:text-zinc-100">
              <ArrowLeft className="h-4 w-4" />
              Objectives
            </Button>
          </Link>
          <span className="text-zinc-600">/</span>
          <span className="text-sm text-zinc-300 font-mono">{objective.id.slice(0, 8)}...</span>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={fetchData}
            className="gap-2 border-zinc-800 text-zinc-300 hover:bg-zinc-800"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            Refresh
          </Button>
          <Link href={`/app/objectives/${objective.id}/work`}>
            <Button size="sm" className="gap-2 bg-indigo-600 hover:bg-indigo-500 text-white">
              <GitPullRequest className="h-3.5 w-3.5" />
              Work Map
            </Button>
          </Link>
        </div>
      </div>

      {/* Main Header Card */}
      <Card className="p-6 bg-zinc-900/60 border-zinc-800 space-y-4">
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
          <div className="space-y-2 max-w-3xl">
            <div className="flex items-center gap-2 flex-wrap">
              <Badge className="bg-indigo-500/10 text-indigo-400 border-indigo-500/20 uppercase font-mono text-[10px]">
                {objective.objective_type}
              </Badge>
              <Badge className="bg-zinc-800 text-zinc-300 border-zinc-700 uppercase font-mono text-[10px]">
                Priority: {objective.priority}
              </Badge>
              <Badge className="bg-zinc-800 text-zinc-300 border-zinc-700 uppercase font-mono text-[10px]">
                Status: {objective.status}
              </Badge>
              {health && getHealthBadge(health.health_status)}
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-zinc-100">
              {objective.name}
            </h1>
            <p className="text-sm text-zinc-300 leading-relaxed">
              {objective.description || "No description provided."}
            </p>
          </div>

          <div className="flex flex-col sm:items-end gap-2 text-xs text-zinc-400 shrink-0 font-mono">
            {objective.target_at && (
              <div className="flex items-center gap-1.5">
                <Calendar className="h-3.5 w-3.5 text-zinc-500" />
                Target: {new Date(objective.target_at).toLocaleDateString()}
              </div>
            )}
            <div className="flex items-center gap-1.5">
              <Clock className="h-3.5 w-3.5 text-zinc-500" />
              Created: {new Date(objective.created_at).toLocaleDateString()}
            </div>
          </div>
        </div>

        {/* Deterministic Health Reason Banner */}
        {health && health.reasons && health.reasons.length > 0 && (
          <div className="mt-4 p-3 rounded-lg border border-zinc-800 bg-zinc-950/80 space-y-1.5">
            <div className="text-xs font-semibold text-zinc-300 flex items-center gap-2">
              <Activity className="h-3.5 w-3.5 text-amber-400" />
              Deterministic Health Diagnostics:
            </div>
            <ul className="text-xs text-zinc-400 space-y-1 pl-5 list-disc">
              {health.reasons.map((r, idx) => (
                <li key={idx}>{r}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Sub Navigation Bar */}
        <div className="flex items-center gap-2 pt-2 border-t border-zinc-800/80 overflow-x-auto">
          <Link href={`/app/objectives/${objective.id}`}>
            <Button variant="ghost" size="sm" className="text-indigo-400 bg-indigo-500/10 hover:bg-indigo-500/20 text-xs">
              Overview
            </Button>
          </Link>
          <Link href={`/app/objectives/${objective.id}/targets`}>
            <Button variant="ghost" size="sm" className="text-zinc-400 hover:text-zinc-200 text-xs">
              Key Results ({targets.length})
            </Button>
          </Link>
          <Link href={`/app/objectives/${objective.id}/milestones`}>
            <Button variant="ghost" size="sm" className="text-zinc-400 hover:text-zinc-200 text-xs">
              Milestones ({milestones.length})
            </Button>
          </Link>
          <Link href={`/app/objectives/${objective.id}/outcomes`}>
            <Button variant="ghost" size="sm" className="text-zinc-400 hover:text-zinc-200 text-xs">
              Outcomes ({outcomes.length})
            </Button>
          </Link>
          <Link href={`/app/objectives/${objective.id}/work`}>
            <Button variant="ghost" size="sm" className="text-zinc-400 hover:text-zinc-200 text-xs">
              Work & Attribution Map
            </Button>
          </Link>
        </div>
      </Card>

      {/* Overview Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Key Results / Targets"
          value={targets.length}
          description="Factual target metrics"
          icon={<Target className="h-5 w-5 text-indigo-400" />}
        />
        <StatCard
          title="Milestones"
          value={`${completedMilestones} / ${milestones.length}`}
          description="Progress to strategic checkpoints"
          icon={<ListTodo className="h-5 w-5 text-blue-400" />}
        />
        <StatCard
          title="Verified Outcomes"
          value={`${verifiedOutcomes} / ${outcomes.length}`}
          description="Evidence-backed deliverables"
          icon={<Award className="h-5 w-5 text-emerald-400" />}
        />
        <StatCard
          title="Health Status"
          value={health?.health_status?.toUpperCase() || "ACTIVE"}
          description="Rule-evaluated integrity"
          icon={<ShieldCheck className="h-5 w-5 text-amber-400" />}
        />
      </div>

      {/* Grid: Targets & Milestones */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Targets */}
        <Card className="p-5 bg-zinc-900/60 border-zinc-800 space-y-4">
          <div className="flex items-center justify-between border-b border-zinc-800/80 pb-3">
            <div className="flex items-center gap-2">
              <Target className="h-4 w-4 text-indigo-400" />
              <h3 className="text-sm font-semibold text-zinc-200">Key Results & Targets</h3>
            </div>
            <Link href={`/app/objectives/${objective.id}/targets`}>
              <Button size="xs" variant="ghost" className="gap-1 text-xs text-indigo-400 hover:text-indigo-300">
                Manage <ArrowRight className="h-3 w-3" />
              </Button>
            </Link>
          </div>

          {targets.length === 0 ? (
            <div className="text-center py-6 text-zinc-500 text-xs">
              No key results configured yet. Add targets to track factual metric baselines.
            </div>
          ) : (
            <div className="space-y-3">
              {targets.slice(0, 4).map((t) => (
                <div key={t.id} className="p-3 rounded-lg border border-zinc-800/80 bg-zinc-950/40 space-y-1.5">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-medium text-zinc-200">{t.name}</span>
                    <Badge className="text-[10px] bg-zinc-800 text-zinc-400 border-zinc-700">
                      {t.status}
                    </Badge>
                  </div>
                  <div className="text-xs text-zinc-400 flex items-center justify-between">
                    <span>
                      Baseline: <strong className="text-zinc-300">{t.baseline_value ?? "—"}</strong>
                    </span>
                    <span>
                      Current: <strong className="text-zinc-200">{t.current_value ?? "—"}</strong>
                    </span>
                    <span>
                      Target: <strong className="text-indigo-400">{t.target_value ?? "—"} {t.target_unit || ""}</strong>
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>

        {/* Milestones */}
        <Card className="p-5 bg-zinc-900/60 border-zinc-800 space-y-4">
          <div className="flex items-center justify-between border-b border-zinc-800/80 pb-3">
            <div className="flex items-center gap-2">
              <ListTodo className="h-4 w-4 text-blue-400" />
              <h3 className="text-sm font-semibold text-zinc-200">Strategic Milestones</h3>
            </div>
            <Link href={`/app/objectives/${objective.id}/milestones`}>
              <Button size="xs" variant="ghost" className="gap-1 text-xs text-blue-400 hover:text-blue-300">
                Manage <ArrowRight className="h-3 w-3" />
              </Button>
            </Link>
          </div>

          {milestones.length === 0 ? (
            <div className="text-center py-6 text-zinc-500 text-xs">
              No milestones defined. Break this objective down into trackable delivery phases.
            </div>
          ) : (
            <div className="space-y-2.5">
              {milestones.slice(0, 4).map((m) => (
                <div key={m.id} className="p-2.5 rounded-lg border border-zinc-800/80 bg-zinc-950/40 flex items-center justify-between text-xs">
                  <div className="space-y-0.5">
                    <div className="font-medium text-zinc-200 flex items-center gap-2">
                      {m.status === "completed" ? (
                        <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
                      ) : m.status === "blocked" ? (
                        <AlertTriangle className="h-3.5 w-3.5 text-rose-400" />
                      ) : (
                        <Clock className="h-3.5 w-3.5 text-zinc-500" />
                      )}
                      <span>{m.name}</span>
                    </div>
                    {m.due_at && (
                      <div className="text-[11px] text-zinc-500 pl-5">
                        Due: {new Date(m.due_at).toLocaleDateString()}
                      </div>
                    )}
                  </div>
                  <Badge className={`text-[10px] ${
                    m.status === "completed"
                      ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                      : m.status === "blocked"
                      ? "bg-rose-500/10 text-rose-400 border-rose-500/20"
                      : "bg-zinc-800 text-zinc-400 border-zinc-700"
                  }`}>
                    {m.status}
                  </Badge>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>

      {/* AI Recommendations */}
      {recommendations.length > 0 && (
        <Card className="p-5 bg-indigo-950/20 border-indigo-800/40 space-y-3">
          <div className="flex items-center gap-2 text-indigo-300 font-semibold text-sm">
            <Sparkles className="h-4 w-4 text-indigo-400" />
            AI Work Recommendations (Evidence-Backed Suggestions)
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {recommendations.map((rec, i) => (
              <div key={i} className="p-3 rounded-lg border border-indigo-900/50 bg-zinc-950/60 space-y-1.5">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold text-indigo-200">{rec.action?.toUpperCase()}</span>
                  <Badge className="bg-indigo-900/40 text-indigo-300 border-indigo-700/50 text-[10px]">
                    Priority: {rec.priority}
                  </Badge>
                </div>
                <p className="text-xs text-zinc-300">{rec.reason}</p>
                {rec.missing_evidence && (
                  <div className="text-[11px] text-amber-400">
                    Missing Evidence: {rec.missing_evidence}
                  </div>
                )}
                {rec.suggested_task && (
                  <div className="text-[11px] text-zinc-400 italic">
                    Suggested Task: &quot;{rec.suggested_task}&quot;
                  </div>
                )}
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Connected Outcomes */}
      <Card className="p-5 bg-zinc-900/60 border-zinc-800 space-y-4">
        <div className="flex items-center justify-between border-b border-zinc-800/80 pb-3">
          <div className="flex items-center gap-2">
            <Award className="h-4 w-4 text-emerald-400" />
            <h3 className="text-sm font-semibold text-zinc-200">Connected Deliverables & Outcomes</h3>
          </div>
          <Link href={`/app/objectives/${objective.id}/outcomes`}>
            <Button size="xs" variant="ghost" className="gap-1 text-xs text-emerald-400 hover:text-emerald-300">
              View All ({outcomes.length}) <ArrowRight className="h-3 w-3" />
            </Button>
          </Link>
        </div>

        {outcomes.length === 0 ? (
          <div className="text-center py-6 text-zinc-500 text-xs">
            No outcomes connected to this objective yet.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {outcomes.slice(0, 4).map((o) => (
              <Link key={o.id} href={`/app/outcomes/${o.id}`}>
                <div className="p-3 rounded-lg border border-zinc-800 bg-zinc-950/50 hover:border-zinc-700 transition space-y-2">
                  <div className="flex items-start justify-between gap-2">
                    <span className="text-xs font-semibold text-zinc-100 hover:text-indigo-300 transition">
                      {o.name}
                    </span>
                    <Badge className={`text-[10px] shrink-0 ${
                      o.status === "verified"
                        ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                        : o.status === "observed"
                        ? "bg-blue-500/10 text-blue-400 border-blue-500/20"
                        : "bg-zinc-800 text-zinc-400 border-zinc-700"
                    }`}>
                      {o.status}
                    </Badge>
                  </div>
                  <div className="text-xs text-zinc-400 line-clamp-1">
                    {o.description || "No description"}
                  </div>
                  <div className="flex items-center justify-between text-[11px] text-zinc-500 pt-1 border-t border-zinc-800/60 font-mono">
                    <span>Confidence: {o.confidence}</span>
                    <span>Type: {o.outcome_type}</span>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
