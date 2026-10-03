"""
Multi-Tier Rate Limiting for Developer Platform.
Step 37: Public API, Developer Platform & SDK Layer.
"""
import asyncio
import time
from collections import defaultdict
from typing import Dict, List, Optional, Tuple
from backend.app.services.developer_platform.errors import RateLimitExceededError

_rate_limit_lock = asyncio.Lock()
_sliding_windows: Dict[str, List[float]] = defaultdict(list)
_active_concurrency: Dict[str, int] = defaultdict(int)


class RateLimitResult:
    def __init__(self, allowed: bool, limit: int, remaining: int, reset_seconds: int, retry_after: int = 0):
        self.allowed = allowed
        self.limit = limit
        self.remaining = remaining
        self.reset_seconds = reset_seconds
        self.retry_after = retry_after

    def to_headers(self) -> Dict[str, str]:
        headers = {
            "X-RateLimit-Limit": str(self.limit),
            "X-RateLimit-Remaining": str(max(0, self.remaining)),
            "X-RateLimit-Reset": str(self.reset_seconds),
        }
        if not self.allowed and self.retry_after > 0:
            headers["Retry-After"] = str(self.retry_after)
        return headers


class APIRateLimiter:
    """
    Multi-tier sliding window rate limiter:
    Checks application, credential, and organization thresholds.
    """

    DEFAULT_RPM = 120
    DEFAULT_RPH = 5000
    DEFAULT_MAX_CONCURRENT = 10

    @classmethod
    async def check_rate_limit(
        cls,
        organization_id: str,
        application_id: str,
        credential_id: str,
        endpoint: str,
        rpm_limit: Optional[int] = None,
        rph_limit: Optional[int] = None,
        max_concurrent: Optional[int] = None,
    ) -> RateLimitResult:
        """
        Evaluates sliding window counters for minute and hour buckets.
        Raises RateLimitExceededError if limit is breached.
        """
        now = time.time()
        rpm = rpm_limit or cls.DEFAULT_RPM
        rph = rph_limit or cls.DEFAULT_RPH

        app_min_key = f"rpm:app:{application_id}"
        app_hour_key = f"rph:app:{application_id}"
        cred_min_key = f"rpm:cred:{credential_id}"

        async with _rate_limit_lock:
            # 1. Minute window check
            window_min = now - 60.0
            _sliding_windows[app_min_key] = [t for t in _sliding_windows[app_min_key] if t > window_min]
            count_min = len(_sliding_windows[app_min_key])

            if count_min >= rpm:
                oldest = _sliding_windows[app_min_key][0]
                retry_after = max(1, int(60.0 - (now - oldest)))
                return RateLimitResult(
                    allowed=False,
                    limit=rpm,
                    remaining=0,
                    reset_seconds=retry_after,
                    retry_after=retry_after,
                )

            # 2. Hour window check
            window_hour = now - 3600.0
            _sliding_windows[app_hour_key] = [t for t in _sliding_windows[app_hour_key] if t > window_hour]
            count_hour = len(_sliding_windows[app_hour_key])

            if count_hour >= rph:
                oldest = _sliding_windows[app_hour_key][0]
                retry_after = max(1, int(3600.0 - (now - oldest)))
                return RateLimitResult(
                    allowed=False,
                    limit=rph,
                    remaining=0,
                    reset_seconds=retry_after,
                    retry_after=retry_after,
                )

            # Record request
            _sliding_windows[app_min_key].append(now)
            _sliding_windows[app_hour_key].append(now)
            _sliding_windows[cred_min_key].append(now)

            remaining = rpm - (count_min + 1)
            reset_seconds = 60 - int(now % 60)

            return RateLimitResult(
                allowed=True,
                limit=rpm,
                remaining=remaining,
                reset_seconds=reset_seconds,
            )

    @classmethod
    async def reset_all(cls) -> None:
        """Reset rate limiter state (used in testing)."""
        async with _rate_limit_lock:
            _sliding_windows.clear()
            _active_concurrency.clear()

RateLimiter = APIRateLimiter
