"""
Side-Effect Sandbox for Step 41: AI Agent Simulation.
Intercepts all potentially external or mutating operations and generates factual 'would execute' records.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid

from backend.app.core.logging import logger
from backend.app.services.simulation.safety import SimulationSafetyEnforcer


from dataclasses import dataclass, field


@dataclass
class InterceptedSideEffect:
    id: str
    run_id: str
    action: str
    actor: str
    target: str
    parameters: Dict[str, Any]
    policy_decision: str
    would_require_approval: bool
    simulated_result: Dict[str, Any]
    intercepted_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class SideEffectSandbox:
    """
    Guarantees zero external real-world side effects.
    Intercepts write/send/mutate actions and returns synthetic results while recording intended actions.
    """

    def __init__(self, run_id: str, workspace_id: str):
        self.run_id = run_id
        self.workspace_id = workspace_id
        self.recorded_side_effects: List[Dict[str, Any]] = []

    def intercept(
        self,
        intended_action: str,
        target: str,
        parameters: Dict[str, Any],
        actor: str = "agent",
        policy_decision: str = "blocked",
        would_require_approval: bool = False,
        synthetic_result: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Intercepts an action, records the 'would execute' record, and returns a synthetic safe result.
        """
        # Sanitize parameters so no secrets leak into simulation logs
        sanitized_params = SimulationSafetyEnforcer.sanitize_snapshot_data(parameters)

        simulated_res = synthetic_result or {
            "status": "simulated_success",
            "message": f"[SIMULATION] Action '{intended_action}' on '{target}' was intercepted by sandbox.",
            "would_execute": True,
            "mocked_id": f"sim_{uuid.uuid4().hex[:8]}",
        }

        record = {
            "id": str(uuid.uuid4()),
            "run_id": self.run_id,
            "intended_action": intended_action,
            "action": intended_action,
            "actor": actor,
            "target": target,
            "parameters": sanitized_params,
            "policy_decision": policy_decision,
            "would_require_approval": would_require_approval,
            "simulated_result": simulated_res,
            "intercepted_at": datetime.now(timezone.utc),
        }

        self.recorded_side_effects.append(record)
        logger.info(
            f"[SideEffectSandbox] Intercepted action: {intended_action} on {target} (actor: {actor}, decision: {policy_decision})"
        )

        return simulated_res

    async def record_side_effect(
        self,
        action: str,
        target: str,
        parameters: Dict[str, Any],
        actor_type: str = "agent",
        actor_id: str = "agent_1",
        policy_decision: str = "blocked",
        would_require_approval: bool = False,
        synthetic_result: Optional[Dict[str, Any]] = None,
    ) -> InterceptedSideEffect:
        """Asynchronously records an intercepted side effect and returns an InterceptedSideEffect instance."""
        res = self.intercept(
            intended_action=action,
            target=target,
            parameters=parameters,
            actor=f"{actor_type}:{actor_id}",
            policy_decision=policy_decision,
            would_require_approval=would_require_approval,
            synthetic_result=synthetic_result or {"status": "would_execute", "action": action, "target": target},
        )
        return InterceptedSideEffect(
            id=str(uuid.uuid4()),
            run_id=self.run_id,
            action=action,
            actor=f"{actor_type}:{actor_id}",
            target=target,
            parameters=parameters,
            policy_decision=policy_decision,
            would_require_approval=would_require_approval,
            simulated_result=res,
        )

    def get_intercepted_records(self) -> List[Dict[str, Any]]:
        """Returns all intercepted side effects for this run."""
        return list(self.recorded_side_effects)

    def get_intercepted_effects(self) -> List[InterceptedSideEffect]:
        """Returns strongly typed list of intercepted effects."""
        return [
            InterceptedSideEffect(
                id=r["id"],
                run_id=r["run_id"],
                action=r.get("action") or r.get("intended_action", ""),
                actor=r.get("actor", ""),
                target=r.get("target", ""),
                parameters=r.get("parameters", {}),
                policy_decision=r.get("policy_decision", ""),
                would_require_approval=r.get("would_require_approval", False),
                simulated_result=r.get("simulated_result", {}),
                intercepted_at=r.get("intercepted_at", datetime.now(timezone.utc)),
            )
            for r in self.recorded_side_effects
        ]

    def count(self) -> int:
        return len(self.recorded_side_effects)

