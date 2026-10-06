"use client";

import React, { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Input } from "@/components/ui/Input";
import { StatCard } from "@/components/ui/StatCard";
import { planningService } from "@/services/planning";
import {
  Gauge,
  ArrowLeft,
  Plus,
  CheckCircle2,
  AlertTriangle,
  Clock,
  ShieldCheck,
  Lock,
} from "lucide-react";

export default function ResourceCapacityPage() {
  const { resourceId } = useParams();

  const [resource, setResource] = useState(null);
  const [capacity, setCapacity] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState(null);

  const [showAddAvail, setShowAddAvail] = useState(false);
  const [availForm, setAvailForm] = useState({
    start_at: new Date().toISOString().slice(0, 16),
    end_at: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().slice(0, 16),
    capacity_units: "10.0",
    source: "manual",
  });

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await planningService.getResource(resourceId);
      setResource(res);
      const cap = await planningService.getResourceCapacity(resourceId);
      setCapacity(cap);
    } catch (err) {
      setError(err.message || "Failed to load resource capacity");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (resourceId) loadData();
  }, [resourceId]);

  const handleAddAvailability = async (e) => {
    e.preventDefault();
    try {
      setActionLoading(true);
      setError(null);
      await planningService.addResourceAvailability(resourceId, {
        start_at: new Date(availForm.start_at).toISOString(),
        end_at: new Date(availForm.end_at).toISOString(),
        capacity_units: parseFloat(availForm.capacity_units || 1.0),
        source: availForm.source,
      });
      setShowAddAvail(false);
      await loadData();
    } catch (err) {
      setError(err.message || "Failed to add availability");
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div className="space-y-8 p-6 max-w-5xl mx-auto">
      <div>
        <Link href={`/app/resources/${resourceId}`}>
          <Button variant="ghost" size="sm" className="gap-2 mb-4">
            <ArrowLeft className="w-4 h-4" />
            Back to Resource
          </Button>
        </Link>
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-primary/10 text-primary border border-primary/20">
              <Gauge className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-foreground">
                Capacity & Availability: {resource?.name}
              </h1>
              <p className="text-sm text-muted-foreground mt-0.5">
                Measurable units, active reservations, and source provenance. Never fabricated.
              </p>
            </div>
          </div>

          <Button size="sm" onClick={() => setShowAddAvail(true)} className="gap-2">
            <Plus className="w-4 h-4" />
            Add Availability Window
          </Button>
        </div>
      </div>

      {resource?.resource_type === "human" && (
        <Card className="p-4 bg-muted/20 border-border/60">
          <div className="flex items-start gap-3">
            <Lock className="w-5 h-5 text-primary flex-shrink-0 mt-0.5" />
            <div className="text-xs space-y-1">
              <span className="font-semibold text-foreground">Human Privacy Notice:</span>
              <p className="text-muted-foreground">
                Human availability is strictly based on explicitly registered working windows. Personal calendars, private habits, and productivity scores are strictly protected and never inferred.
              </p>
            </div>
          </div>
        </Card>
      )}

      {error && (
        <div className="p-4 rounded-xl bg-destructive/10 border border-destructive/20 text-destructive text-sm flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {showAddAvail && (
        <Card className="p-6 border-primary/40 bg-card/80">
          <form onSubmit={handleAddAvailability} className="space-y-4">
            <h3 className="font-semibold text-sm text-foreground">Add Availability Window</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-xs text-muted-foreground">Start Date & Time</label>
                <Input
                  type="datetime-local"
                  value={availForm.start_at}
                  onChange={(e) => setAvailForm({ ...availForm, start_at: e.target.value })}
                  required
                />
              </div>
              <div>
                <label className="text-xs text-muted-foreground">End Date & Time</label>
                <Input
                  type="datetime-local"
                  value={availForm.end_at}
                  onChange={(e) => setAvailForm({ ...availForm, end_at: e.target.value })}
                  required
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-xs text-muted-foreground">Capacity Units (e.g. hours or concurrent runs)</label>
                <Input
                  type="number"
                  step="0.5"
                  value={availForm.capacity_units}
                  onChange={(e) => setAvailForm({ ...availForm, capacity_units: e.target.value })}
                  required
                />
              </div>
              <div>
                <label className="text-xs text-muted-foreground">Measurement Source</label>
                <select
                  value={availForm.source}
                  onChange={(e) => setAvailForm({ ...availForm, source: e.target.value })}
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm"
                >
                  <option value="manual">Manual Configuration</option>
                  <option value="calendar">Published Calendar</option>
                  <option value="system">System Registered</option>
                  <option value="policy">Governance Policy</option>
                </select>
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-2">
              <Button type="button" variant="ghost" size="sm" onClick={() => setShowAddAvail(false)}>
                Cancel
              </Button>
              <Button type="submit" size="sm" disabled={actionLoading}>
                Save Window
              </Button>
            </div>
          </form>
        </Card>
      )}

      {/* Capacity Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Available Units"
          value={capacity ? capacity.available_units : "--"}
          icon={CheckCircle2}
          description={`Source: ${capacity?.source || "unknown"}`}
        />
        <StatCard
          title="Reserved Units"
          value={capacity ? capacity.reserved_units : "--"}
          icon={Clock}
          description="Committed to plan items"
        />
        <StatCard
          title="Proposed Units"
          value={capacity ? capacity.proposed_units : "--"}
          icon={Gauge}
          description="In uncommitted schedules"
        />
        <StatCard
          title="Remaining Units"
          value={capacity ? capacity.remaining_units : "--"}
          icon={ShieldCheck}
          description="Free capacity available"
        />
      </div>
    </div>
  );
}
