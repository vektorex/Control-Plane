"""
AI Agent Simulation, Sandbox & Scenario Testing Layer (Step 41).
Safe, deterministic simulation environment for testing agents, teams, workflows, and policies without real-world side effects.
"""
from backend.app.services.simulation.adapters import (
    ArtifactSimulationAdapter,
    ConnectorSimulationAdapter,
    KnowledgeGraphSimulationAdapter,
    MemorySimulationAdapter,
    SimulationAgentRuntimeAdapter,
    ToolSimulationAdapter,
    WebSearchSimulationAdapter,
)
from backend.app.services.simulation.artifacts import SimulationReportGenerator
from backend.app.services.simulation.assertions import SimulationAssertionEngine
from backend.app.services.simulation.comparator import SimulationComparator
from backend.app.services.simulation.environment import SimulationEnvironmentManager
from backend.app.services.simulation.errors import (
    AssertionEvaluationError,
    FaultInjectionConfigError,
    SideEffectSandboxViolationError,
    SimulationError,
    SimulationLifecycleError,
    SimulationNotFoundError,
    SimulationRunNotFoundError,
    SimulationScenarioNotFoundError,
    SimulationSuiteNotFoundError,
    SimulationValidationError,
    SimulationVersionImmutableError,
    SimulationVersionNotFoundError,
    TenantIsolationError,
)
from backend.app.services.simulation.events import SimulationEventPublisher
from backend.app.services.simulation.faults import FaultEngine
from backend.app.services.simulation.lifecycle import SimulationLifecycle
from backend.app.services.simulation.models import (
    FaultInjection,
    FaultProfile,
    Simulation,
    SimulationAssertion,
    SimulationComparison,
    SimulationEnvironment,
    SimulationRun,
    SimulationScenario,
    SimulationSideEffect,
    SimulationSuite,
    SimulationSuiteScenario,
    SimulationVersion,
)
from backend.app.services.simulation.policies import PolicySimulator
from backend.app.services.simulation.registry import SimulationRegistry
from backend.app.services.simulation.repository import SimulationRepository
from backend.app.services.simulation.runner import SimulationRunner
from backend.app.services.simulation.safety import SimulationSafetyEnforcer
from backend.app.services.simulation.sandbox import SideEffectSandbox
from backend.app.services.simulation.scenario import BUILTIN_SCENARIO_TEMPLATES, SafeVariableResolver
from backend.app.services.simulation.schemas import (
    ArtifactExecutionMode,
    ConnectorExecutionMode,
    EnvironmentMode,
    FaultDistributionMode,
    KnowledgeExecutionMode,
    MemoryExecutionMode,
    ScenarioType,
    SimulationComparisonRequest,
    SimulationComparisonResponse,
    SimulationCreate,
    SimulationDetailResponse,
    SimulationEnvironmentCreate,
    SimulationEnvironmentResponse,
    SimulationReportResponse,
    SimulationResponse,
    SimulationRunCreate,
    SimulationRunDetailResponse,
    SimulationRunResponse,
    SimulationScenarioCreate,
    SimulationScenarioResponse,
    SimulationScenarioUpdate,
    SimulationStatus,
    SimulationSuiteCreate,
    SimulationSuiteDetailResponse,
    SimulationSuiteResponse,
    SimulationSuiteRunRequest,
    SimulationSuiteRunResult,
    SimulationType,
    SimulationUpdate,
    SimulationVersionCreate,
    SimulationVersionResponse,
    TargetType,
    ToolExecutionMode,
    WebSearchExecutionMode,
)
from backend.app.services.simulation.service import SimulationService
from backend.app.services.simulation.validators import SimulationValidator

__all__ = [
    "Simulation",
    "SimulationVersion",
    "SimulationEnvironment",
    "SimulationScenario",
    "FaultProfile",
    "FaultInjection",
    "SimulationRun",
    "SimulationAssertion",
    "SimulationSideEffect",
    "SimulationSuite",
    "SimulationSuiteScenario",
    "SimulationComparison",
    "SimulationService",
    "SimulationRepository",
    "SimulationRunner",
    "SideEffectSandbox",
    "FaultEngine",
    "SimulationAssertionEngine",
    "SimulationComparator",
    "SimulationSafetyEnforcer",
    "SimulationEnvironmentManager",
    "PolicySimulator",
    "SafeVariableResolver",
    "SimulationRegistry",
    "SimulationEventPublisher",
    "SimulationReportGenerator",
    "SimulationLifecycle",
    "SimulationValidator",
    "ToolSimulationAdapter",
    "ConnectorSimulationAdapter",
    "WebSearchSimulationAdapter",
    "MemorySimulationAdapter",
    "KnowledgeGraphSimulationAdapter",
    "ArtifactSimulationAdapter",
    "SimulationAgentRuntimeAdapter",
    "BUILTIN_SCENARIO_TEMPLATES",
    "SimulationError",
    "SimulationNotFoundError",
    "SimulationVersionNotFoundError",
    "SimulationVersionImmutableError",
    "SimulationScenarioNotFoundError",
    "SimulationSuiteNotFoundError",
    "SimulationRunNotFoundError",
    "SideEffectSandboxViolationError",
    "FaultInjectionConfigError",
    "AssertionEvaluationError",
    "SimulationLifecycleError",
    "SimulationValidationError",
    "TenantIsolationError",
]
