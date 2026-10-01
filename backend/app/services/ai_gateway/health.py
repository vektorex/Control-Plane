import time
from typing import Any, Dict, Optional
from backend.app.core.logging import logger
from backend.app.services.ai_gateway.errors import CircuitOpenError


class CircuitBreaker:
    """
    In-memory Circuit Breaker for provider/model fault isolation.
    Opens circuit after consecutive failures exceeding threshold,
    diverting traffic to fallbacks until cooldown period expires.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        reset_seconds: float = 60.0,
    ):
        self.failure_threshold = failure_threshold
        self.reset_seconds = reset_seconds
        # key -> {"state": "closed", "failures": 0, "last_failure_time": 0.0}
        self._states: Dict[str, Dict[str, Any]] = {}

    def _get_entry(self, key: str) -> Dict[str, Any]:
        if key not in self._states:
            self._states[key] = {
                "state": "closed",
                "failures": 0,
                "last_failure_time": 0.0,
                "last_success_time": 0.0,
            }
        return self._states[key]

    def get_state(self, key: str) -> str:
        """Return current circuit state: 'closed', 'open', or 'half_open'."""
        entry = self._get_entry(key)
        state = entry["state"]

        if state == "open":
            now = time.time()
            if (now - entry["last_failure_time"]) >= self.reset_seconds:
                entry["state"] = "half_open"
                return "half_open"
        return entry["state"]

    def can_execute(self, key: str) -> bool:
        """Check if execution is allowed. Returns False if circuit is OPEN."""
        state = self.get_state(key)
        return state in ("closed", "half_open")

    def record_success(self, key: str) -> None:
        """Record a successful execution, resetting failure counters."""
        entry = self._get_entry(key)
        entry["state"] = "closed"
        entry["failures"] = 0
        entry["last_success_time"] = time.time()

    def record_failure(self, key: str) -> None:
        """Record an execution failure, opening circuit if threshold is reached."""
        entry = self._get_entry(key)
        now = time.time()
        entry["failures"] += 1
        entry["last_failure_time"] = now

        if entry["state"] == "half_open" or entry["failures"] >= self.failure_threshold:
            entry["state"] = "open"
            logger.warning(
                f"[CircuitBreaker] Circuit OPENED for '{key}' "
                f"after {entry['failures']} consecutive failures. Cooldown: {self.reset_seconds}s"
            )


class ModelHealthService:
    """
    Tracks operational health and reliability metrics for providers and models.
    Health is purely operational (availability, timeouts, latency) and NOT subjective ranking.
    """

    def __init__(self):
        self._metrics: Dict[str, Dict[str, Any]] = {}
        self.circuit_breaker = CircuitBreaker()

    def _get_metric_record(self, key: str) -> Dict[str, Any]:
        if key not in self._metrics:
            self._metrics[key] = {
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "timeout_count": 0,
                "total_latency_ms": 0.0,
                "last_success_at": None,
                "last_failure_at": None,
                "last_error": None,
            }
        return self._metrics[key]

    def record_request_start(self, provider: str, model: str) -> None:
        pass

    def record_request_success(self, provider: str, model: str, latency_ms: float) -> None:
        now = time.time()
        for key in (provider, f"{provider}/{model}"):
            m = self._get_metric_record(key)
            m["total_requests"] += 1
            m["successful_requests"] += 1
            m["total_latency_ms"] += latency_ms
            m["last_success_at"] = now
            self.circuit_breaker.record_success(key)

    def record_request_failure(
        self, provider: str, model: str, error_msg: str, is_timeout: bool = False
    ) -> None:
        now = time.time()
        for key in (provider, f"{provider}/{model}"):
            m = self._get_metric_record(key)
            m["total_requests"] += 1
            m["failed_requests"] += 1
            if is_timeout:
                m["timeout_count"] += 1
            m["last_failure_at"] = now
            m["last_error"] = error_msg[:200]
            self.circuit_breaker.record_failure(key)

    def get_health_status(self, provider: str, model: Optional[str] = None) -> Dict[str, Any]:
        """Compute operational health summary."""
        key = f"{provider}/{model}" if model else provider
        m = self._get_metric_record(key)
        cb_state = self.circuit_breaker.get_state(key)

        total = m["total_requests"]
        fails = m["failed_requests"]
        avg_lat = round(m["total_latency_ms"] / max(1, m["successful_requests"]), 2)

        if cb_state == "open":
            status = "unavailable"
        elif total > 5 and (fails / total) > 0.4:
            status = "degraded"
        elif total > 0:
            status = "healthy"
        else:
            status = "healthy"  # New or unprobed

        return {
            "target": key,
            "status": status,
            "circuit_state": cb_state,
            "total_requests": total,
            "failed_requests": fails,
            "timeout_count": m["timeout_count"],
            "average_latency_ms": avg_lat,
            "last_success_at": m["last_success_at"],
            "last_failure_at": m["last_failure_at"],
            "last_error": m["last_error"],
        }


default_health_service = ModelHealthService()
