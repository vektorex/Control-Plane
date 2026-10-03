"use client";

import React, { useState, useEffect, useCallback, use } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  FlaskConical,
  Play,
  Square,
  RefreshCw,
  Terminal,
  CheckCircle2,
  AlertTriangle,
} from "lucide-react";
import { recoveryService } from "@/services/recovery";

export default function ExerciseDetailPage({ params }) {
  const unwrappedParams = use(params);
  const exerciseId = unwrappedParams.exerciseId;

  const [exercise, setExercise] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState("");
  const [actionLoading, setActionLoading] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      setIsLoading(true);
      setErrorMsg("");
      const res = await recoveryService.getExercise(exerciseId);
      setExercise(res);
    } catch (err) {
      setErrorMsg(err.message || "Failed to load recovery exercise.");
    } finally {
      setIsLoading(false);
    }
  }, [exerciseId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleRun = async () => {
    try {
      setActionLoading(true);
      await recoveryService.runExercise(exerciseId);
      await fetchData();
    } catch (err) {
      alert(`Error running exercise: ${err.message}`);
    } finally {
      setActionLoading(false);
    }
  };

  const handleAbort = async () => {
    try {
      setActionLoading(true);
      await recoveryService.abortExercise(exerciseId, "Manual abort from exercise detail");
      await fetchData();
    } catch (err) {
      alert(`Error aborting exercise: ${err.message}`);
    } finally {
      setActionLoading(false);
    }
  };

  if (isLoading && !exercise) {
    return (
      <div className="p-8 text-center text-slate-400 text-sm">
        <RefreshCw className="w-5 h-5 animate-spin mx-auto mb-2 text-indigo-400" />
        Loading recovery exercise...
      </div>
    );
  }

  if (errorMsg || !exercise) {
    return (
      <div className="p-6 max-w-4xl mx-auto space-y-4">
        <Link
          href="/app/recovery/exercises"
          className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200"
        >
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Exercises
        </Link>
        <div className="p-4 bg-red-950/40 border border-red-800 rounded-xl text-red-200 text-sm">
          {errorMsg || "Exercise not found."}
        </div>
      </div>
    );
  }

  const observations = exercise.observations || [];

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      <div>
        <Link
          href="/app/recovery/exercises"
          className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 transition mb-2"
        >
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Exercises
        </Link>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-slate-900 border border-slate-800 rounded-xl">
              <FlaskConical className="w-6 h-6 text-indigo-400" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl font-bold text-white tracking-tight">
                  {exercise.name}
                </h1>
                <span className="text-xs uppercase font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                  {exercise.environment}
                </span>
                <span className="text-xs px-2 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-800 font-mono">
                  {exercise.status}
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-1">
                Scenario: <span className="font-mono text-white">{exercise.scenario.replace(/_/g, " ")}</span> • Created: {new Date(exercise.created_at).toLocaleDateString()}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {exercise.status === "planned" && (
              <button
                onClick={handleRun}
                disabled={actionLoading}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-sm transition disabled:opacity-50"
              >
                <Play className="w-3.5 h-3.5" /> Run Drill
              </button>
            )}

            {exercise.status === "running" && (
              <button
                onClick={handleAbort}
                disabled={actionLoading}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-red-600 hover:bg-red-500 text-white text-xs font-semibold shadow-sm transition disabled:opacity-50"
              >
                <Square className="w-3.5 h-3.5" /> Abort
              </button>
            )}

            <button
              onClick={fetchData}
              disabled={isLoading}
              className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
              title="Refresh"
            >
              <RefreshCw className={`w-4 h-4 ${isLoading ? "animate-spin" : ""}`} />
            </button>
          </div>
        </div>
      </div>

      {/* Drill Specification */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-3 text-xs">
        <h3 className="text-sm font-semibold text-white">Exercise Assertion & Abort Conditions</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 font-mono">
          <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 space-y-1">
            <span className="text-slate-500 block text-[11px]">Expected Recovery:</span>
            <span className="text-slate-300">{exercise.expected_recovery}</span>
          </div>
          <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 space-y-1">
            <span className="text-slate-500 block text-[11px]">Abort Conditions:</span>
            <span className="text-amber-300">{exercise.abort_conditions || "Abort on error"}</span>
          </div>
        </div>
      </div>

      {/* Observations Log */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Terminal className="w-4 h-4 text-indigo-400" />
            <h3 className="text-sm font-semibold text-white">Empirical Drill Observations</h3>
          </div>
          <span className="text-xs text-slate-500 font-mono">{observations.length} observations</span>
        </div>

        {observations.length === 0 ? (
          <div className="p-8 text-center text-slate-500 text-xs font-mono">
            No observations recorded yet. Run drill to simulate recovery assertion.
          </div>
        ) : (
          <div className="divide-y divide-slate-800/60 font-mono text-xs">
            {observations.map((obs) => (
              <div key={obs.id} className="p-3 flex items-center justify-between hover:bg-slate-800/20">
                <div>
                  <div className="text-white font-semibold">{obs.metric}</div>
                  <div className="text-[11px] text-slate-400">
                    Observed: {obs.value} • Expected: {obs.expected_value || "-"}
                  </div>
                </div>
                <div className="text-right">
                  <span className="text-emerald-400 font-bold uppercase">{obs.status}</span>
                  <span className="text-[10px] text-slate-500 block">
                    {new Date(obs.timestamp).toLocaleTimeString()}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
