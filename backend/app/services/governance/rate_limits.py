"""
RateLimitService: request/model/connector/tool/workflow/delivery rate limit governance.
Reuses in-memory counters; no external rate-limit store introduced. Step 32.
"""
import asyncio
import time
from collections import defaultdict
from typing import Dict, Optional, Tuple

from backend.app.services.governance.constants import (
    GovernanceDecisionType,
    RATE_LIMIT_WINDOW_SECONDS,
)


# In-memory sliding window counter: key -> list of timestamps
_rate_counters: Dict[str, list] = defaultdict(list)
_lock = asyncio.Lock()


class RateLimitService:
    """
    Sliding-window rate limit service for governance.
    Supports: requests, model_calls, connector_calls, tool_calls, workflow_runs,
              external_deliveries.
    Keys are scoped to workspace to prevent cross-tenant leakage.
    """

    # Default limits (can be overridden via policy action_params)
    DEFAULT_LIMITS = {
        "requests": 200,         # per minute per workspace
        "model_calls": 100,      # per minute per workspace
        "connector_calls": 60,   # per minute per workspace
        "tool_calls": 120,       # per minute per workspace
        "workflow_runs": 30,     # per minute per workspace
        "external_deliveries": 30,  # per minute per workspace
    }

    @staticmethod
    async def check(
        workspace_id: str,
        category: str,
        limit: Optional[int] = None,
    ) -> Tuple[GovernanceDecisionType, list]:
        """
        Checks whether the workspace has exceeded the rate limit for the given category.
        Returns (decision, reasons).
        """
        effective_limit = limit or RateLimitService.DEFAULT_LIMITS.get(category, 200)
        key = f"{workspace_id}:{category}"
        now = time.monotonic()
        window_start = now - RATE_LIMIT_WINDOW_SECONDS

        async with _lock:
            # Purge expired timestamps
            _rate_counters[key] = [t for t in _rate_counters[key] if t > window_start]
            current_count = len(_rate_counters[key])

            if current_count >= effective_limit:
                return GovernanceDecisionType.DENY, [
                    f"Rate limit exceeded: {current_count}/{effective_limit} {category} per {RATE_LIMIT_WINDOW_SECONDS}s window"
                ]

            # Record this invocation
            _rate_counters[key].append(now)

        return GovernanceDecisionType.ALLOW, []

    @staticmethod
    async def current_count(workspace_id: str, category: str) -> int:
        key = f"{workspace_id}:{category}"
        now = time.monotonic()
        window_start = now - RATE_LIMIT_WINDOW_SECONDS
        async with _lock:
            _rate_counters[key] = [t for t in _rate_counters[key] if t > window_start]
            return len(_rate_counters[key])

    @staticmethod
    async def reset_for_workspace(workspace_id: str) -> None:
        """Used only in tests to reset rate counters for a specific workspace."""
        async with _lock:
            keys_to_clear = [k for k in _rate_counters if k.startswith(f"{workspace_id}:")]
            for k in keys_to_clear:
                del _rate_counters[k]
