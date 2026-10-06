"""
Capacity Management, Snapshots, Reservations, and Forecasting for Step 44.
"""
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from backend.app.services.planning.errors import (
    CapacityExceededError,
    FabricatedCapacityError,
    UnauthorizedCapacityReservationError,
)
from backend.app.services.planning.models import (
    CapacityReservation,
    CapacitySnapshot,
    ResourceAvailability,
    WorkResource,
)
from backend.app.services.planning.policies import PlanningPolicyEngine


class CapacityManager:
    """
    Computes capacity, evaluates reservations, and generates verifiable forecasts.
    Never invents availability or capacity without explicit records.
    """

    @staticmethod
    def calculate_resource_capacity(
        resource: WorkResource,
        availabilities: List[ResourceAvailability],
        reservations: List[CapacityReservation],
        window_start: datetime,
        window_end: datetime,
    ) -> Dict[str, Any]:
        """
        Calculates factual available, reserved, allocated, and remaining units.
        If no availability entry exists for the window, source is marked 'unknown'
        and available_units is 0.0.
        """
        relevant_avails = [
            a for a in availabilities
            if a.resource_id == resource.id and a.start_at <= window_end and a.end_at >= window_start
        ]

        total_available = 0.0
        sources = set()
        for a in relevant_avails:
            if a.source == "unknown":
                continue
            total_available += float(a.capacity_units)
            sources.add(a.source)

        # Check active reservations
        relevant_res = [
            r for r in reservations
            if r.resource_id == resource.id and r.status in ("reserved", "proposed")
            and r.start_at <= window_end and r.end_at >= window_start
        ]

        total_reserved = sum(float(r.units) for r in relevant_res if r.status == "reserved")
        total_proposed = sum(float(r.units) for r in relevant_res if r.status == "proposed")

        remaining = max(0.0, total_available - total_reserved)
        primary_source = ", ".join(sources) if sources else "unknown"

        return {
            "resource_id": resource.id,
            "resource_name": resource.name,
            "resource_type": resource.resource_type,
            "window_start": window_start,
            "window_end": window_end,
            "available_units": total_available,
            "reserved_units": total_reserved,
            "proposed_units": total_proposed,
            "remaining_units": remaining,
            "source": primary_source,
            "is_unknown": len(sources) == 0 or "unknown" in sources,
        }

    @staticmethod
    def evaluate_reservation_request(
        resource_id: str,
        available_units: float,
        current_reserved: float,
        requested_units: float,
        is_authorized: bool = True,
    ) -> None:
        """
        Validates that reservation is authorized and within capacity bounds.
        """
        PlanningPolicyEngine.validate_reservation_authorization(is_authorized)
        if (current_reserved + requested_units) > available_units:
            raise CapacityExceededError(
                resource_id=resource_id,
                requested=requested_units,
                available=max(0.0, available_units - current_reserved),
            )

    @staticmethod
    def generate_capacity_forecast(
        resources: List[WorkResource],
        availabilities: List[ResourceAvailability],
        reservations: List[CapacityReservation],
        planned_demands: List[Dict[str, Any]],
        period_start: datetime,
        period_end: datetime,
    ) -> Dict[str, Any]:
        """
        Aggregates forecast across resources for a given horizon.
        Explicitly marked with is_forecast=True and tracks unknown availability.
        """
        total_available = 0.0
        total_reserved = 0.0
        unknown_count = 0
        sources: List[str] = []

        for r in resources:
            cap = CapacityManager.calculate_resource_capacity(
                resource=r,
                availabilities=availabilities,
                reservations=reservations,
                window_start=period_start,
                window_end=period_end,
            )
            total_available += cap["available_units"]
            total_reserved += cap["reserved_units"]
            if cap["is_unknown"]:
                unknown_count += 1
            if cap["source"] and cap["source"] != "unknown":
                sources.append(f"{r.name}:{cap['source']}")

        total_demand = sum(float(d.get("estimated_units", 1.0)) for d in planned_demands)
        remaining = max(0.0, total_available - total_reserved - total_demand)

        return {
            "period_start": period_start,
            "period_end": period_end,
            "planned_demand": total_demand,
            "available_capacity": total_available,
            "reserved_capacity": total_reserved,
            "remaining_capacity": remaining,
            "unknown_capacity_count": unknown_count,
            "is_forecast": True,
            "sources": sources or ["none_recorded"],
        }
