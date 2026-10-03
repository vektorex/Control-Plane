"""
Freshness and Stale-While-Revalidate Engine for Step 31: Semantic Cache.
"""
from datetime import datetime, timezone
from typing import Optional, Tuple

from backend.app.services.cache.constants import (
    CACHE_DEFAULT_TTL_SECONDS,
    CACHE_RELAXED_TTL_SECONDS,
    CACHE_STRICT_TTL_SECONDS,
    FreshnessPolicy,
    STALE_REVALIDATE_GRACE_PERIOD_SECONDS,
)
from backend.app.services.cache.models import CacheEntry


class FreshnessService:
    """
    Evaluates expiration, time-to-live policies, and stale-while-revalidate eligibility.
    """

    @classmethod
    def calculate_ttl(
        cls,
        freshness_policy: FreshnessPolicy = FreshnessPolicy.NORMAL,
        custom_ttl: Optional[int] = None,
        is_security_sensitive: bool = False,
    ) -> int:
        """
        Calculates time-to-live in seconds according to freshness policy and sensitivity.
        """
        if is_security_sensitive:
            return CACHE_STRICT_TTL_SECONDS

        if custom_ttl and custom_ttl > 0:
            return custom_ttl

        if freshness_policy == FreshnessPolicy.STRICT:
            return CACHE_STRICT_TTL_SECONDS
        elif freshness_policy == FreshnessPolicy.RELAXED:
            return CACHE_RELAXED_TTL_SECONDS
        return CACHE_DEFAULT_TTL_SECONDS

    @classmethod
    def evaluate_entry_freshness(
        cls,
        entry: CacheEntry,
        stale_while_revalidate_enabled: bool = True,
        is_security_or_approval: bool = False,
    ) -> Tuple[bool, bool, str]:
        """
        Evaluates whether an entry is fresh, stale-while-revalidate eligible, or expired.
        Returns (is_fresh, can_stale_revalidate, reason).
        """
        now = datetime.now(timezone.utc)
        expires_at = entry.expires_at

        # Ensure timezone-awareness
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        # 1. Active & within expiration window
        if now <= expires_at:
            return True, False, "Entry is fully fresh."

        # 2. Past expiration: check stale-while-revalidate grace period
        if is_security_or_approval:
            return False, False, "Entry is expired. Stale reuse is forbidden for sensitive operations."

        if not stale_while_revalidate_enabled:
            return False, False, "Entry is expired and stale-while-revalidate is disabled."

        seconds_past = (now - expires_at).total_seconds()
        if seconds_past <= STALE_REVALIDATE_GRACE_PERIOD_SECONDS:
            return False, True, f"Entry is slightly stale ({int(seconds_past)}s past expiry). Eligible for stale-while-revalidate."

        return False, False, f"Entry expired {int(seconds_past)}s ago, exceeding grace period."

    @classmethod
    def is_fresh(
        cls,
        entry: CacheEntry,
        allow_stale_while_revalidate: bool = True,
        is_security_sensitive: bool = False,
    ) -> Tuple[bool, bool]:
        """
        Convenience evaluator returning (is_fresh, allow_swr).
        """
        fresh, swr, _ = cls.evaluate_entry_freshness(
            entry=entry,
            stale_while_revalidate_enabled=allow_stale_while_revalidate,
            is_security_or_approval=is_security_sensitive,
        )
        return fresh, swr
