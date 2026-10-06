"""
Deterministic Simulation Runner for Step 41: AI Agent Simulation.
Orchestrates sandboxed executions, fault injection, side-effect interception, and assertion evaluation.
"""
from datetime import datetime, timezone
import time
from typing import Any, Dict, List, Optional
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.logging import logger
from backend.app.services.events.constants import ActorType
from backend.app.services.simulation.adapters import (
    ArtifactSimulationAdapter,
    ConnectorSimulationAdapter,
    KnowledgeGraphSimulationAdapter,
    MemorySimulationAdapter,
    SimulationAgentRuntimeAdapter,
    ToolSimulationAdapter,
    WebSearchSimulationAdapter,
)
from backend.app.services.simulation.assertions import SimulationAssertionEngine
from backend.app.services.simulation.environment import SimulationEnvironmentManager
from backend.app.services.simulation.errors import (
    SimulationError,
    SimulationNotFoundError,
)
from backend.app.services.simulation.events import SimulationEventPublisher
from backend.app.services.simulation.faults import FaultEngine
from backend.app.services.simulation.models import (
    FaultInjection,
    Simulation,
    SimulationAssertion,
    SimulationRun,
    SimulationScenario,
    SimulationSideEffect,
    SimulationVersion,
)
from backend.app.services.simulation.safety import SimulationSafetyEnforcer
from backend.app.services.simulation.sandbox import SideEffectSandbox
from backend.app.services.simulation.scenario import SafeVariableResolver


class SimulationRunner:
    """
    Executes a governed simulation run with seed determinism and sandboxed side effects.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.event_publisher = SimulationEventPublisher(session)

    async def run_simulation(
        self,
        simulation: Simulation,
        version: SimulationVersion,
        user_id: str,
        scenario: Optional[SimulationScenario] = None,
        scenario_override: Optional[Dict[str, Any]] = None,
        seed: int = 42,
        target_version_id: Optional[str] = None,
        policy_overrides: Optional[Dict[str, Any]] = None,
        fault_overrides: Optional[Dict[str, Any]] = None,
        budget_limit: Optional[float] = None,
        suite_id: Optional[str] = None,
    ) -> SimulationRun:
        run_id = str(uuid.uuid4())
        start_time = time.time()
        start_dt = datetime.now(timezone.utc)

        # 1. Merge configuration and overrides
        merged_policy_overrides = dict(version.policy_overrides or {})
        if policy_overrides:
            merged_policy_overrides.update(policy_overrides)

        merged_fault_config = dict(version.fault_config or {})
        if fault_overrides:
            merged_fault_config.update(fault_overrides)
        if scenario and scenario.fault_configuration:
            merged_fault_config.update(scenario.fault_configuration)

        # 2. Build sandbox and fault engine
        sandbox = SideEffectSandbox(run_id=run_id, workspace_id=simulation.workspace_id)
        fault_engine = FaultEngine(fault_config=merged_fault_config, seed=seed)

        # 3. Build adapters
        tool_adapter = ToolSimulationAdapter(
            sandbox=sandbox,
            synthetic_responses=version.environment_config.get("synthetic_tool_responses", {}),
        )
        connector_adapter = ConnectorSimulationAdapter(
            sandbox=sandbox,
            snapshots=version.environment_config.get("connector_snapshots", {}),
            synthetic_data=version.environment_config.get("synthetic_connector_responses", {}),
        )
        memory_adapter = MemorySimulationAdapter(
            sandbox=sandbox,
            snapshot_memories=version.environment_config.get("synthetic_memory", []),
        )
        kg_adapter = KnowledgeGraphSimulationAdapter(
            sandbox=sandbox,
            graph_snapshot=version.environment_config.get("synthetic_knowledge_graph", {}),
        )
        artifact_adapter = ArtifactSimulationAdapter(
            sandbox=sandbox,
            artifacts_snapshot=version.environment_config.get("synthetic_artifacts", []),
        )
        web_search_adapter = WebSearchSimulationAdapter()

        # 4. Prepare scenario inputs and context
        input_data = {}
        context_data = {}
        if scenario:
            input_data = dict(scenario.input or {})
            context_data = dict(scenario.context or {})
        if scenario_override:
            input_data.update(scenario_override.get("input", {}))
            context_data.update(scenario_override.get("context", {}))

        # Safe variable resolution
        resolve_ctx = {
            "agent": {"id": simulation.target_id, "version": target_version_id or "latest"},
            "scenario": {"name": scenario.name if scenario else "direct_run"},
            "environment": {"seed": seed},
        }
        resolved_input = SafeVariableResolver.resolve(input_data, resolve_ctx)

        # Adversarial pattern check
        input_str = str(resolved_input)
        security_findings = SimulationSafetyEnforcer.check_adversarial_patterns(input_str)

        # 5. Initialize trace buffer
        trace_events = [
            {
                "sequence": 1,
                "timestamp": start_dt.isoformat(),
                "event_type": "simulation_started",
                "actor_type": ActorType.SYSTEM.value,
                "actor_id": "simulation_runner",
                "metadata": {"simulation_id": simulation.id, "seed": seed, "target_type": simulation.target_type},
            }
        ]

        # Emit simulation.started event
        await self.event_publisher.emit_run_event(
            event_type="simulation.started",
            workspace_id=simulation.workspace_id,
            run_id=run_id,
            simulation_id=simulation.id,
            payload={"target_id": simulation.target_id, "seed": seed},
            actor_id=user_id,
        )

        # 6. Check Fault: model_unavailable / model_timeout
        model_fault = fault_engine.should_inject_fault("model_unavailable", simulation.target_id)
        if not model_fault:
            model_fault = fault_engine.should_inject_fault("model_timeout", simulation.target_id)

        target_output: Dict[str, Any] = {}
        tokens = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        cost = 0.0
        policy_decisions: List[Dict[str, Any]] = []
        run_status = "completed"
        run_error = None

        if model_fault:
            run_status = "failed"
            run_error = f"Fault Injected: {model_fault['fault_type']} triggered for target {simulation.target_id}."
            target_output = {"error": run_error}
            trace_events.append({
                "sequence": 2,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "event_type": "simulation.fault.injected",
                "actor_type": ActorType.SYSTEM.value,
                "actor_id": "fault_engine",
                "metadata": model_fault,
            })
            await self.event_publisher.emit_run_event(
                event_type="simulation.fault.injected",
                workspace_id=simulation.workspace_id,
                run_id=run_id,
                simulation_id=simulation.id,
                payload=model_fault,
            )
        else:
            # 7. Execute Target via Simulation Adapter
            if simulation.target_type == "agent":
                agent_adapter = SimulationAgentRuntimeAdapter(
                    session=self.session,
                    sandbox=sandbox,
                    tool_adapter=tool_adapter,
                    connector_adapter=connector_adapter,
                    memory_adapter=memory_adapter,
                    kg_adapter=kg_adapter,
                    artifact_adapter=artifact_adapter,
                    web_search_adapter=web_search_adapter,
                )
                exec_res = await agent_adapter.execute_simulated_step(
                    agent_id=simulation.target_id,
                    workspace_id=simulation.workspace_id,
                    user_id=user_id,
                    input_data=resolved_input,
                    context_data=context_data,
                    version_id=target_version_id,
                    policy_overrides=merged_policy_overrides,
                    budget_override=budget_limit,
                    seed=seed,
                )
                target_output = exec_res.get("output", {})
                tokens = exec_res.get("tokens", tokens)
                cost = exec_res.get("cost", 0.0)
                policy_decisions = exec_res.get("policy_decisions", [])
                if exec_res.get("status") == "policy_denied":
                    run_status = "completed"  # Successfully simulated denial

            elif simulation.target_type == "agent_team":
                # Multi-agent team simulation
                target_output = {
                    "team_planning": "Simulated multi-agent team plan synthesized.",
                    "assignments": [{"agent": "researcher", "role": "gather"}, {"agent": "writer", "role": "synthesize"}],
                    "messages_count": 2,
                    "conflicts_detected": 0,
                    "synthesis": f"[SIMULATED TEAM OUTPUT] Processed input: {resolved_input}",
                }
                tokens = {"prompt_tokens": 250, "completion_tokens": 120, "total_tokens": 370}
                cost = 0.0008

            else:
                # Workflow / task / replay fallback
                target_output = {
                    "text": f"[SIMULATED {simulation.target_type.upper()}] Execution finished in sandbox.",
                    "input_received": resolved_input,
                }
                tokens = {"prompt_tokens": 50, "completion_tokens": 25, "total_tokens": 75}
                cost = 0.0001

        end_dt = datetime.now(timezone.utc)
        latency = round(time.time() - start_time, 4)

        # 8. Evaluate Assertions
        assertions_defs = list(version.assertions or [])
        if scenario and scenario.assertions:
            assertions_defs.extend(scenario.assertions)

        run_metrics = {
            "status": run_status,
            "output": target_output,
            "tool_calls": tool_adapter.recorded_calls,
            "connector_calls": connector_adapter.recorded_calls,
            "delegations": [],
            "side_effects": sandbox.get_intercepted_records(),
            "cost": cost,
            "latency": latency,
            "policy_decisions": policy_decisions,
            "security_findings": security_findings,
            "steps_executed": 1,
        }
        evaluated_assertions = SimulationAssertionEngine.evaluate_assertions(assertions_defs, run_metrics)

        # If any error-severity assertion failed, emit assertion.failed
        for ea in evaluated_assertions:
            if not ea["passed"]:
                await self.event_publisher.emit_run_event(
                    event_type="simulation.assertion.failed",
                    workspace_id=simulation.workspace_id,
                    run_id=run_id,
                    simulation_id=simulation.id,
                    payload={"assertion_type": ea["assertion_type"], "details": ea["details"]},
                )

        # Check side effects
        intercepted_side_effects = sandbox.get_intercepted_records()
        for se in intercepted_side_effects:
            await self.event_publisher.emit_run_event(
                event_type="simulation.side_effect.intercepted",
                workspace_id=simulation.workspace_id,
                run_id=run_id,
                simulation_id=simulation.id,
                payload={"intended_action": se["intended_action"], "target": se["target"]},
            )

        # 9. Create SimulationRun Model
        run_record = SimulationRun(
            id=run_id,
            simulation_id=simulation.id,
            simulation_version_id=version.id,
            scenario_id=scenario.id if scenario else None,
            suite_id=suite_id,
            seed=seed,
            status=run_status,
            target_type=simulation.target_type,
            target_id=simulation.target_id,
            target_version_id=target_version_id,
            policy_snapshot=merged_policy_overrides,
            fault_snapshot=merged_fault_config,
            output=target_output,
            assertion_results=evaluated_assertions,
            side_effects=intercepted_side_effects,
            events_count=len(trace_events) + len(intercepted_side_effects),
            tool_calls=tool_adapter.recorded_calls,
            connector_calls=connector_adapter.recorded_calls,
            delegations=[],
            tokens=tokens,
            cost=cost,
            latency=latency,
            started_at=start_dt,
            completed_at=end_dt,
            error=run_error,
            reproducibility_metadata={
                "seed": seed,
                "deterministic": True,
                "provider_notice": "External LLM providers may vary unless fixed seed temperature=0.0 is used.",
            },
            created_at=start_dt,
        )
        self.session.add(run_record)
        await self.session.flush()

        # Persist child assertion entities
        for ea in evaluated_assertions:
            assert_entity = SimulationAssertion(
                id=str(uuid.uuid4()),
                run_id=run_id,
                assertion_type=ea["assertion_type"],
                parameters=ea["parameters"],
                expected=ea["expected"],
                actual=ea["actual"],
                passed=ea["passed"],
                severity=ea["severity"],
                details=ea["details"],
                created_at=end_dt,
            )
            self.session.add(assert_entity)

        # Persist child side-effect entities
        for se in intercepted_side_effects:
            se_entity = SimulationSideEffect(
                id=str(uuid.uuid4()),
                run_id=run_id,
                intended_action=se["intended_action"],
                actor=se["actor"],
                target=se["target"],
                parameters=se["parameters"],
                policy_decision=se["policy_decision"],
                would_require_approval=se["would_require_approval"],
                simulated_result=se["simulated_result"],
                intercepted_at=se["intercepted_at"],
            )
            self.session.add(se_entity)

        # Persist fault injection records
        for fi in fault_engine.get_injected_records():
            fi_entity = FaultInjection(
                id=str(uuid.uuid4()),
                run_id=run_id,
                fault_type=fi["fault_type"],
                target=fi["target"],
                parameters=fi["parameters"],
                trigger_condition=fi["trigger_condition"],
                injected_at=fi["injected_at"],
                result=fi["result"],
            )
            self.session.add(fi_entity)

        # Emit completion event
        await self.event_publisher.emit_run_event(
            event_type="simulation.completed" if run_status == "completed" else "simulation.failed",
            workspace_id=simulation.workspace_id,
            run_id=run_id,
            simulation_id=simulation.id,
            payload={"status": run_status, "cost": cost, "latency": latency},
        )

        await self.session.commit()
        return run_record
