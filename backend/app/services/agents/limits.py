"""
Execution and Budget Limits Enforcement for Step 40.
Prevents unbounded execution loops, runaway costs, and resource exhaustion.
"""
import time
from typing import Any, Dict, Optional
from backend.app.services.agents.errors import (
    AgentBudgetExhaustedError,
    AgentExecutionLimitExceededError,
)


class ExecutionLimitChecker:
    """Enforces execution boundaries for an active agent run."""

    def __init__(self, policy: Dict[str, Any], budget_policy: Optional[Dict[str, Any]] = None):
        self.max_steps = policy.get("max_steps", 15)
        self.max_iterations = policy.get("max_iterations", 10)
        self.max_delegations = policy.get("max_delegations", 3)
        self.max_runtime_seconds = policy.get("max_runtime_seconds", 300)
        self.max_tool_calls = policy.get("max_tool_calls", 20)
        self.max_connector_calls = policy.get("max_connector_calls", 10)
        self.max_cost = float(policy.get("max_cost", 5.0))
        if budget_policy and "max_budget_per_run" in budget_policy:
            self.max_cost = min(self.max_cost, float(budget_policy["max_budget_per_run"]))

        self.start_time = time.time()

    def check_step(self, current_steps: int) -> None:
        """Verifies step count is within bounds."""
        if current_steps >= self.max_steps:
            raise AgentExecutionLimitExceededError("max_steps", self.max_steps, current_steps)

    def check_tool_calls(self, current_calls: int) -> None:
        """Verifies tool call count is within bounds."""
        if current_calls >= self.max_tool_calls:
            raise AgentExecutionLimitExceededError("max_tool_calls", self.max_tool_calls, current_calls)

    def check_connector_calls(self, current_calls: int) -> None:
        """Verifies connector call count is within bounds."""
        if current_calls >= self.max_connector_calls:
            raise AgentExecutionLimitExceededError("max_connector_calls", self.max_connector_calls, current_calls)

    def check_delegations(self, current_delegations: int) -> None:
        """Verifies delegation count is within bounds."""
        if current_delegations >= self.max_delegations:
            raise AgentExecutionLimitExceededError("max_delegations", self.max_delegations, current_delegations)

    def check_runtime(self) -> None:
        """Verifies runtime has not exceeded timeout."""
        elapsed = time.time() - self.start_time
        if elapsed > self.max_runtime_seconds:
            raise AgentExecutionLimitExceededError("max_runtime_seconds", self.max_runtime_seconds, elapsed)

    def check_cost(self, run_id: str, current_spend: float) -> None:
        """Verifies current spend has not exceeded budget reservation."""
        if current_spend >= self.max_cost:
            raise AgentBudgetExhaustedError(run_id, self.max_cost, current_spend)
