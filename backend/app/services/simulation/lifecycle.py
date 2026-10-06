"""
Simulation Lifecycle State Machine for Step 41.
Defines and enforces state transitions for simulations, versions, and runs.
"""
from typing import Dict, Set
from backend.app.services.simulation.errors import SimulationLifecycleError
from backend.app.services.simulation.schemas import SimulationStatus


ALLOWED_SIMULATION_TRANSITIONS: Dict[str, Set[str]] = {
    SimulationStatus.DRAFT.value: {SimulationStatus.READY.value, SimulationStatus.ARCHIVED.value},
    SimulationStatus.READY.value: {SimulationStatus.RUNNING.value, SimulationStatus.DRAFT.value, SimulationStatus.ARCHIVED.value},
    SimulationStatus.RUNNING.value: {SimulationStatus.COMPLETED.value, SimulationStatus.FAILED.value, SimulationStatus.CANCELLED.value},
    SimulationStatus.COMPLETED.value: {SimulationStatus.RUNNING.value, SimulationStatus.ARCHIVED.value, SimulationStatus.READY.value},
    SimulationStatus.FAILED.value: {SimulationStatus.RUNNING.value, SimulationStatus.ARCHIVED.value, SimulationStatus.READY.value},
    SimulationStatus.CANCELLED.value: {SimulationStatus.RUNNING.value, SimulationStatus.ARCHIVED.value, SimulationStatus.READY.value},
    SimulationStatus.ARCHIVED.value: set(),
}

ALLOWED_RUN_TRANSITIONS: Dict[str, Set[str]] = {
    "queued": {"running", "cancelled"},
    "running": {"completed", "failed", "cancelled"},
    "completed": set(),
    "failed": set(),
    "cancelled": set(),
}


class SimulationLifecycle:
    """Manages validated state transitions."""

    @classmethod
    def validate_simulation_transition(cls, current_status: str, target_status: str) -> None:
        if current_status == target_status:
            return
        allowed = ALLOWED_SIMULATION_TRANSITIONS.get(current_status, set())
        if target_status not in allowed:
            raise SimulationLifecycleError(
                current_status=current_status,
                target_status=target_status,
                reason=f"Transition from '{current_status}' to '{target_status}' is disallowed.",
            )

    @classmethod
    def validate_run_transition(cls, current_status: str, target_status: str) -> None:
        if current_status == target_status:
            return
        allowed = ALLOWED_RUN_TRANSITIONS.get(current_status, set())
        if target_status not in allowed:
            raise SimulationLifecycleError(
                current_status=current_status,
                target_status=target_status,
                reason=f"Run transition from '{current_status}' to '{target_status}' is disallowed.",
            )
