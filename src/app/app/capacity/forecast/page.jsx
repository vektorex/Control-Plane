"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { StatCard } from "@/components/ui/StatCard";
import { planningService } from "@/services/planning";
import {
  Gauge,
  RefreshCw,
  Clock,
  CheckCircle2,
  AlertTriangle,
  Info,
  Layers,
  Activity,
} from "lucide-react";

export default function CapacityForecastPage() {
  const [forecast, setForecast] = useState(null);
  const [horizonDays, setHorizonDays] = useState(14);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchForecast = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await planningService.getCapacityForecast(horizonDays);
      setForecast(data);
    } catch (err) {
      setError(err.message || "Failed to load capacity forecast");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchForecast();
  }, [horizonDays]);

  return (
    <div className="space-y-8 p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 border-b border-border/40 pb-6">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-primary/10 text-primary border border-primary/20">
              <Gauge className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-2xl font-bold tracking-tight text-foreground">
                  Capacity Forecasting
                </h1>
                <Badge variant="warning" className="text-xs">
                  FORECAST (NOT FACT)
                </Badge>
              </div>
              <p className="text-sm text-muted-foreground mt-0.5">
                Aggregate projected demand against verified available resource capacity.
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <Button variant="outline" size="sm" onClick={fetchForecast} disabled={loading} className="gap-2">
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </Button>
          <div className="flex items-center gap-1 border border-border/60 rounded-md p-1 bg-card/60">
            {[7, 14, 30, 60].map((days) => (
              <Button
                key={days}
                size="sm"
                variant={horizonDays === days ? "primary" : "ghost"}
                onClick={() => setHorizonDays(days)}
                className="text-xs px-2.5 h-7"
              >
                {days}d
              </Button>
            ))}
          </div>
        </div>
      </div>

      {/* Sub-nav */}
      <div className="flex border-b border-border/40 gap-2 text-sm pb-1">
        <Link href="/app/capacity/forecast">
          <Button variant="ghost" size="sm" className="border-b-2 border-primary text-primary font-medium rounded-none">
            Forecast Overview
          </Button>
        </Link>
        <Link href="/app/capacity/workload">
          <Button variant="ghost" size="sm" className="text-muted-foreground rounded-none">
            Resource Workload
          </Button>
        </Link>
      </div>

      {/* Forecast Disclaimer */}
      <Card className="p-4 bg-muted/20 border-border/60">
        <div className="flex items-start gap-3">
          <Info className="w-5 h-5 text-primary flex-shrink-0 mt-0.5" />
          <div className="text-xs space-y-1">
            <span className="font-semibold text-foreground">Forecast Integrity Policy:</span>
            <p className="text-muted-foreground">
              Capacity forecasts project planned demand from active plans against explicitly configured availability windows. Resources without verified availability are reported as unknown rather than assuming availability.
            </p>
          </div>
        </div>
      </Card>

      {error && (
        <div className="p-4 rounded-xl bg-destructive/10 border border-destructive/20 text-destructive text-sm flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Planned Demand"
          value={forecast ? `${forecast.planned_demand} units` : "--"}
          icon={Activity}
          description="Demands from active plans"
        />
        <StatCard
          title="Available Capacity"
          value={forecast ? `${forecast.available_capacity} units` : "--"}
          icon={CheckCircle2}
          description="Total recorded available units"
        />
        <StatCard
          title="Reserved Capacity"
          value={forecast ? `${forecast.reserved_capacity} units` : "--"}
          icon={Clock}
          description="Committed reservations"
        />
        <StatCard
          title="Remaining Capacity"
          value={forecast ? `${forecast.remaining_capacity} units` : "--"}
          icon={Layers}
          description="Projected surplus capacity"
        />
      </div>

      {/* Breakdown Card */}
      <Card className="p-6 space-y-4">
        <h3 className="font-semibold text-base text-foreground">Forecast Provenance & Unknowns</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
          <div className="p-4 rounded-lg bg-muted/30 border border-border/40 space-y-2">
            <span className="font-semibold text-foreground">Recorded Measurement Sources:</span>
            <ul className="space-y-1 text-muted-foreground list-disc list-inside">
              {(forecast?.sources || []).map((s, idx) => (
                <li key={idx}>{s}</li>
              ))}
            </ul>
          </div>
          <div className="p-4 rounded-lg bg-muted/30 border border-border/40 space-y-2">
            <span className="font-semibold text-foreground">Unknown Availability Count:</span>
            <p className="text-muted-foreground">
              {forecast?.unknown_capacity_count || 0} resources have no registered availability for this horizon and are excluded from capacity claims.
            </p>
          </div>
        </div>
      </Card>
    </div>
  );
}
