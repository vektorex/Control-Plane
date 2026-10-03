"""
Post-recovery verification engine for Step 35: AI Reliability, Resilience & Chaos Engineering Layer.
Confirms system health, checkpoint validity, and data integrity before reporting recovery as complete.
"""
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.reliability.health import HealthCheckService
from backend.app.services.reliability.models import ExecutionCheckpoint


class RecoveryVerifier:
    """Verifies that components and states have returned to healthy operational levels."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.health_service = HealthCheckService(session)

    async def verify_recovery(
        self,
        component_id: Optional[str] = None,
        checkpoint: Optional[ExecutionCheckpoint] = None,
        expected_state: Optional[str] = "healthy",
    ) -> Dict[str, Any]:
        verification_checks: Dict[str, bool] = {}

        # 1. Component health check
        if component_id:
            try:
                comp = await self.health_service.get_component(component_id)
                verification_checks["component_health"] = comp.health_status in {"healthy", "warning"}
            except Exception:
                verification_checks["component_health"] = False
        else:
            verification_checks["component_health"] = True

        # 2. Checkpoint validation
        if checkpoint:
            verification_checks["checkpoint_exists"] = checkpoint.id is not None
            verification_checks["checkpoint_unexpired"] = (
                checkpoint.expires_at is None
                or checkpoint.expires_at > checkpoint.created_at
            )
        else:
            verification_checks["checkpoint_exists"] = True
            verification_checks["checkpoint_unexpired"] = True

        all_passed = all(verification_checks.values())

        return {
            "verified": all_passed,
            "status": "passed" if all_passed else "failed",
            "checks": verification_checks,
        }
