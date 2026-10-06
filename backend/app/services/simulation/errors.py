"""
Domain exception hierarchy for Step 41: AI Agent Simulation, Sandbox & Scenario Testing Layer.
"""
from typing import Any, Optional
from fastapi import status
from backend.app.core.errors import AppError


class SimulationError(AppError):
    """Base exception for simulation layer."""
    code: str = "SIMULATION_ERROR"
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR


class SimulationNotFoundError(SimulationError):
    """Raised when simulation entity is not found."""
    code: str = "SIMULATION_NOT_FOUND"
    status_code: int = status.HTTP_404_NOT_FOUND

    def __init__(self, simulation_id: str):
        super().__init__(f"Simulation '{simulation_id}' not found.", {"simulation_id": simulation_id})


class SimulationVersionNotFoundError(SimulationError):
    """Raised when simulation version is not found."""
    code: str = "SIMULATION_VERSION_NOT_FOUND"
    status_code: int = status.HTTP_404_NOT_FOUND

    def __init__(self, simulation_id: str, version: Optional[int] = None, version_id: Optional[str] = None):
        msg = f"Simulation '{simulation_id}' version '{version or version_id}' not found."
        super().__init__(msg, {"simulation_id": simulation_id, "version": version, "version_id": version_id})


class SimulationVersionImmutableError(SimulationError):
    """Raised when attempting to modify a published immutable simulation version."""
    code: str = "SIMULATION_VERSION_IMMUTABLE"
    status_code: int = status.HTTP_409_CONFLICT

    def __init__(self, version_id: str):
        super().__init__(
            f"Simulation version '{version_id}' is published and immutable. Create a new draft version to modify configuration.",
            {"version_id": version_id},
        )


class SimulationScenarioNotFoundError(SimulationError):
    """Raised when scenario is not found."""
    code: str = "SIMULATION_SCENARIO_NOT_FOUND"
    status_code: int = status.HTTP_404_NOT_FOUND

    def __init__(self, scenario_id: str):
        super().__init__(f"Simulation scenario '{scenario_id}' not found.", {"scenario_id": scenario_id})


class SimulationSuiteNotFoundError(SimulationError):
    """Raised when simulation suite is not found."""
    code: str = "SIMULATION_SUITE_NOT_FOUND"
    status_code: int = status.HTTP_404_NOT_FOUND

    def __init__(self, suite_id: str):
        super().__init__(f"Simulation suite '{suite_id}' not found.", {"suite_id": suite_id})


class SimulationRunNotFoundError(SimulationError):
    """Raised when simulation run is not found."""
    code: str = "SIMULATION_RUN_NOT_FOUND"
    status_code: int = status.HTTP_404_NOT_FOUND

    def __init__(self, run_id: str):
        super().__init__(f"Simulation run '{run_id}' not found.", {"run_id": run_id})


class SideEffectSandboxViolationError(SimulationError):
    """Raised when an unapproved external side effect attempt bypasses sandbox boundaries."""
    code: str = "SIDE_EFFECT_SANDBOX_VIOLATION"
    status_code: int = status.HTTP_403_FORBIDDEN

    def __init__(self, operation: str, target: str, reason: str):
        super().__init__(
            f"Sandbox intercepted forbidden external operation '{operation}' on target '{target}': {reason}",
            {"operation": operation, "target": target, "reason": reason},
        )


class FaultInjectionConfigError(SimulationError):
    """Raised when a fault injection definition is malformed or invalid."""
    code: str = "FAULT_INJECTION_CONFIG_ERROR"
    status_code: int = 422

    def __init__(self, reason: str, details: Optional[Any] = None):
        super().__init__(f"Fault injection configuration error: {reason}", details)


class AssertionEvaluationError(SimulationError):
    """Raised when assertion engine fails to evaluate a test assertion."""
    code: str = "ASSERTION_EVALUATION_ERROR"
    status_code: int = status.HTTP_400_BAD_REQUEST

    def __init__(self, assertion_type: str, reason: str):
        super().__init__(f"Assertion evaluation error for '{assertion_type}': {reason}", {"assertion_type": assertion_type})


class SimulationLifecycleError(SimulationError):
    """Raised for invalid simulation state transitions."""
    code: str = "SIMULATION_LIFECYCLE_ERROR"
    status_code: int = status.HTTP_400_BAD_REQUEST

    def __init__(self, current_status: str, target_status: str, reason: str):
        super().__init__(
            f"Cannot transition simulation from '{current_status}' to '{target_status}': {reason}",
            {"current_status": current_status, "target_status": target_status},
        )


class SimulationValidationError(SimulationError):
    """Raised when input validation for scenario or simulation fails."""
    code: str = "SIMULATION_VALIDATION_ERROR"
    status_code: int = 422


class TenantIsolationError(SimulationError):
    """Raised when cross-tenant access is attempted during simulation."""
    code: str = "CROSS_TENANT_ACCESS_FORBIDDEN"
    status_code: int = status.HTTP_403_FORBIDDEN

    def __init__(self, message: str = "Cross-tenant access strictly forbidden in simulation sandbox."):
        super().__init__(message)


# Aliases for consistent naming across testing and adapter layers
SimulationSideEffectBlockedError = SideEffectSandboxViolationError
SimulationTenantViolationError = TenantIsolationError
SimulationFaultConfigError = FaultInjectionConfigError
SimulationAssertionFailedError = AssertionEvaluationError
SimulationExecutionError = SimulationError
SimulationSnapshotSanitizationError = SimulationValidationError
