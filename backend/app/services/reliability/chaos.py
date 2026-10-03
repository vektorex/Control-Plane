"""
Chaos failure simulation engine for Step 35: AI Reliability, Resilience & Chaos Engineering Layer.
Provides deterministic, synthetic failure simulation hooks.
Strictly disallows arbitrary code, shell commands, or destructive side effects.
"""
import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from backend.app.services.reliability.exceptions import (
    ChaosExperimentAbortedError,
    InvalidChaosActionError,
)
from backend.app.services.reliability.validators import validate_chaos_action_allowlist


class ChaosFailureSimulator:
    """
    Executes safe, predefined failure simulations in test and sandbox environments.
    """

    @classmethod
    async def simulate_failure(
        cls,
        failure_type: str,
        target_type: str,
        target_id: str,
        duration_seconds: int = 5,
        abort_check: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Executes a controlled, bounded failure simulation.
        """
        validate_chaos_action_allowlist(failure_type)

        started_at = datetime.now(timezone.utc)
        simulated_logs: List[str] = [
            f"Starting chaos failure simulation: {failure_type} against {target_type}/{target_id}",
        ]

        if failure_type == "simulate_timeout":
            simulated_logs.append(f"Simulating timeout delay of {min(duration_seconds, 10)} seconds")
            await asyncio.sleep(min(duration_seconds, 10))
            simulated_logs.append("Synthetic timeout elapsed")

        elif failure_type == "simulate_provider_unavailable":
            simulated_logs.append(f"Synthetic provider outage injected for {target_id}")

        elif failure_type == "simulate_rate_limit":
            simulated_logs.append(f"Synthetic HTTP 429 RateLimit injected for {target_id}")

        elif failure_type == "simulate_connector_failure":
            simulated_logs.append(f"Synthetic connector error injected for {target_id}")

        elif failure_type == "simulate_tool_failure":
            simulated_logs.append(f"Synthetic tool execution error injected for {target_id}")

        elif failure_type == "simulate_cache_unavailable":
            simulated_logs.append("Synthetic semantic cache outage injected; cache bypassed safely")

        elif failure_type == "simulate_event_delay":
            simulated_logs.append(f"Synthetic event delay injected for {min(duration_seconds, 5)} seconds")
            await asyncio.sleep(min(duration_seconds, 5))

        elif failure_type == "simulate_job_failure":
            simulated_logs.append(f"Synthetic worker crash/lease expiry simulated for job {target_id}")

        elif failure_type == "simulate_notification_failure":
            simulated_logs.append(f"Synthetic notification delivery failure injected for {target_id}")

        elif failure_type == "simulate_retrieval_failure":
            simulated_logs.append("Synthetic vector retrieval degradation simulated")

        elif failure_type == "simulate_evaluation_failure":
            simulated_logs.append("Synthetic evaluator timeout simulated")

        completed_at = datetime.now(timezone.utc)
        simulated_logs.append("Chaos failure simulation completed safely without side effects")

        return {
            "failure_type": failure_type,
            "target": f"{target_type}/{target_id}",
            "started_at": started_at.isoformat(),
            "completed_at": completed_at.isoformat(),
            "elapsed_seconds": (completed_at - started_at).total_seconds(),
            "logs": simulated_logs,
        }
