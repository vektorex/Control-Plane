"""
Circuit breaker implementation for Step 35: AI Reliability, Resilience & Chaos Engineering Layer.
Protects AI providers, connectors, tools, notifications, and external storage from cascading saturation.
Does NOT wrap internal PostgreSQL transactions to avoid hiding database failures.
"""
from datetime import datetime, timezone
import threading
from typing import Any, Dict, Optional, Tuple

from backend.app.services.reliability.exceptions import CircuitOpenError


class CircuitBreaker:
    """
    In-process and database-synced state machine for circuit breakers:
    States:
      - closed: Normal traffic flows through. Failures increment failure count.
      - open: All calls fail fast with CircuitOpenError without hitting the dependency.
      - half_open: Limited probe calls allowed to test whether the dependency has recovered.
    """

    def __init__(
        self,
        component_name: str,
        failure_threshold: int = 5,
        recovery_timeout_seconds: float = 30.0,
        half_open_success_threshold: int = 2,
    ):
        self.component_name = component_name
        self.failure_threshold = failure_threshold
        self.recovery_timeout_seconds = recovery_timeout_seconds
        self.half_open_success_threshold = half_open_success_threshold

        self._state = "closed"
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[datetime] = None
        self._opened_at: Optional[datetime] = None
        self._lock = threading.Lock()

    @property
    def state(self) -> str:
        with self._lock:
            self._evaluate_state()
            return self._state

    def _evaluate_state(self) -> None:
        """Transitions from open to half_open if recovery timeout has elapsed."""
        now = datetime.now(timezone.utc)
        if self._state == "open" and self._opened_at:
            elapsed = (now - self._opened_at).total_seconds()
            if elapsed >= self.recovery_timeout_seconds:
                self._state = "half_open"
                self._success_count = 0

    def check_call_allowed(self) -> None:
        """
        Validates whether a call is allowed. If open, raises CircuitOpenError.
        """
        with self._lock:
            self._evaluate_state()
            if self._state == "open":
                now = datetime.now(timezone.utc)
                remaining = self.recovery_timeout_seconds - (
                    (now - self._opened_at).total_seconds() if self._opened_at else 0
                )
                raise CircuitOpenError(
                    f"Circuit breaker for '{self.component_name}' is OPEN. Fast-failing request.",
                    details={
                        "component": self.component_name,
                        "state": "open",
                        "cooldown_remaining_seconds": max(0.0, remaining),
                    },
                )

    def record_success(self) -> None:
        """Records a successful call and handles half-open recovery."""
        with self._lock:
            if self._state == "half_open":
                self._success_count += 1
                if self._success_count >= self.half_open_success_threshold:
                    # Successfully recovered
                    self._state = "closed"
                    self._failure_count = 0
                    self._success_count = 0
                    self._opened_at = None
            elif self._state == "closed":
                self._failure_count = 0

    def record_failure(self) -> None:
        """Records a dependency failure, tripping the circuit if threshold exceeded."""
        with self._lock:
            now = datetime.now(timezone.utc)
            self._last_failure_time = now

            if self._state == "half_open":
                # Immediately trip back to open on failure during probe
                self._state = "open"
                self._opened_at = now
            elif self._state == "closed":
                self._failure_count += 1
                if self._failure_count >= self.failure_threshold:
                    self._state = "open"
                    self._opened_at = now

    def reset(self) -> None:
        """Manually forces the circuit breaker back to closed state."""
        with self._lock:
            self._state = "closed"
            self._failure_count = 0
            self._success_count = 0
            self._opened_at = None
            self._last_failure_time = None

    def get_status(self) -> Dict[str, Any]:
        """Returns circuit state snapshot."""
        with self._lock:
            self._evaluate_state()
            now = datetime.now(timezone.utc)
            remaining = 0.0
            if self._state == "open" and self._opened_at:
                elapsed = (now - self._opened_at).total_seconds()
                remaining = max(0.0, self.recovery_timeout_seconds - elapsed)

            return {
                "component": self.component_name,
                "state": self._state,
                "failure_count": self._failure_count,
                "failure_threshold": self.failure_threshold,
                "last_failure_at": self._last_failure_time.isoformat() if self._last_failure_time else None,
                "cooldown_remaining_seconds": round(remaining, 2) if self._state == "open" else None,
            }


class CircuitBreakerRegistry:
    """Singleton registry tracking circuit breakers across all external services."""
    _breakers: Dict[str, CircuitBreaker] = {}
    _lock = threading.Lock()

    @classmethod
    def get_breaker(
        cls,
        component_name: str,
        failure_threshold: int = 5,
        recovery_timeout_seconds: float = 30.0,
    ) -> CircuitBreaker:
        with cls._lock:
            if component_name not in cls._breakers:
                cls._breakers[component_name] = CircuitBreaker(
                    component_name=component_name,
                    failure_threshold=failure_threshold,
                    recovery_timeout_seconds=recovery_timeout_seconds,
                )
            return cls._breakers[component_name]

    @classmethod
    def get_all_statuses(cls) -> Dict[str, Dict[str, Any]]:
        with cls._lock:
            return {k: v.get_status() for k, v in cls._breakers.items()}
