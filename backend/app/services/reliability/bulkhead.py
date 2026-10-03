"""
Bulkhead concurrency isolation engine for Step 35: AI Reliability, Resilience & Chaos Engineering Layer.
Constrains concurrent executions across sensitive subsystems to prevent worker saturation.
"""
import asyncio
from typing import Any, Dict, Optional

from backend.app.services.reliability.exceptions import BulkheadCapacityExceededError

# Default bounded concurrency slots per subsystem
DEFAULT_BULKHEAD_LIMITS: Dict[str, int] = {
    "ai_provider_calls": 50,
    "workflow_executions": 25,
    "connector_operations": 30,
    "document_processing": 15,
    "evaluation_experiments": 10,
    "replay_executions": 10,
    "data_exports": 5,
    "notification_deliveries": 40,
    "security_processing": 30,
    "chaos_experiments": 2,
}


class SubsystemBulkhead:
    """Bounded semaphore tracking active slots and queue rejections."""
    def __init__(self, name: str, max_concurrent: int):
        self.name = name
        self.max_concurrent = max_concurrent
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._active_count = 0

    @property
    def available_slots(self) -> int:
        return max(0, self.max_concurrent - self._active_count)

    @property
    def active_count(self) -> int:
        return self._active_count

    async def acquire(self, timeout_seconds: Optional[float] = 0.5) -> None:
        """
        Attempts to acquire a bulkhead execution slot. Fails fast with BulkheadCapacityExceededError
        if the subsystem is saturated.
        """
        try:
            if timeout_seconds is None or timeout_seconds <= 0:
                # Immediate non-blocking check
                if self._semaphore.locked():
                    raise BulkheadCapacityExceededError(
                        f"Bulkhead capacity exceeded for subsystem '{self.name}'. "
                        f"Limit: {self.max_concurrent}, Active: {self._active_count}.",
                        details={"subsystem": self.name, "limit": self.max_concurrent, "active": self._active_count},
                    )
                await self._semaphore.acquire()
            else:
                await asyncio.wait_for(self._semaphore.acquire(), timeout=timeout_seconds)
            self._active_count += 1
        except asyncio.TimeoutError:
            raise BulkheadCapacityExceededError(
                f"Bulkhead queue timeout ({timeout_seconds}s) exceeded for '{self.name}'.",
                details={"subsystem": self.name, "limit": self.max_concurrent, "active": self._active_count},
            )

    def release(self) -> None:
        """Releases an acquired execution slot."""
        if self._active_count > 0:
            self._active_count -= 1
            self._semaphore.release()


class BulkheadRegistry:
    """Registry coordinating concurrency isolation bulkheads across subsystems."""
    _bulkheads: Dict[str, SubsystemBulkhead] = {}

    @classmethod
    def get_bulkhead(cls, subsystem_name: str) -> SubsystemBulkhead:
        if subsystem_name not in cls._bulkheads:
            limit = DEFAULT_BULKHEAD_LIMITS.get(subsystem_name, 20)
            cls._bulkheads[subsystem_name] = SubsystemBulkhead(subsystem_name, limit)
        return cls._bulkheads[subsystem_name]

    @classmethod
    def get_capacity_metrics(cls) -> Dict[str, Dict[str, int]]:
        """Returns observable metrics of active capacity and limits per subsystem."""
        # Ensure default subsystems are populated
        for name, limit in DEFAULT_BULKHEAD_LIMITS.items():
            if name not in cls._bulkheads:
                cls._bulkheads[name] = SubsystemBulkhead(name, limit)

        metrics = {}
        for name, bh in cls._bulkheads.items():
            metrics[name] = {
                "max_concurrent": bh.max_concurrent,
                "active_slots": bh.active_count,
                "available_slots": bh.available_slots,
            }
        return metrics
