"""
JobPolicyEngine: Security, validation, workspace isolation, and concurrency controls.
"""
import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.models.job import Job
from backend.app.services.jobs.constants import JobStatus, JobType
from backend.app.services.jobs.errors import (
    JobConcurrencyError,
    JobPermissionDeniedError,
    JobValidationError,
)


class JobPolicyEngine:
    """
    Enforces authorization, payload safety, and multi-tenant fairness on durable jobs.
    """

    FORBIDDEN_PAYLOAD_KEYS = [
        "__import__",
        "eval",
        "exec",
        "system",
        "popen",
        "subprocess",
        "lambda",
        "code",
        "function",
        "bytecode",
    ]

    FORBIDDEN_SECRET_KEYS = [
        "api_key",
        "secret_key",
        "client_secret",
        "private_key",
        "password",
        "access_token",
        "refresh_token",
    ]

    MAX_WORKSPACE_RUNNING_JOBS = 20

    @classmethod
    def validate_payload_safety(cls, job_type: str, payload: Dict[str, Any]) -> None:
        """
        Validates that job payload does not contain executable code, system commands, or unvetted scripts,
        and does NOT contain raw credentials or secrets.
        """
        if not isinstance(payload, dict):
            raise JobValidationError("Job payload must be a JSON object dictionary.")

        # Deep scan keys and values for malicious code injection and raw secret tokens
        def _scan(obj: Any) -> None:
            if isinstance(obj, dict):
                for k, v in obj.items():
                    k_lower = str(k).lower()
                    for forbidden in cls.FORBIDDEN_PAYLOAD_KEYS:
                        if forbidden in k_lower:
                            raise JobValidationError(
                                f"Forbidden token '{forbidden}' detected in job payload key: '{k}'."
                            )
                    for sec_key in cls.FORBIDDEN_SECRET_KEYS:
                        if sec_key == k_lower or f"_{sec_key}" in k_lower:
                            raise JobValidationError(
                                f"Raw secret key '{k}' detected in job payload. Store credentials in Secret Store."
                            )
                    _scan(v)
            elif isinstance(obj, list):
                for item in obj:
                    _scan(item)
            elif isinstance(obj, str):
                val_lower = obj.lower().strip()
                if val_lower.startswith("sk-") or val_lower.startswith("ghp_") or "bearer ey" in val_lower:
                    raise JobValidationError("Raw secret token detected in job payload.")

        _scan(payload)

    @classmethod
    async def check_workspace_concurrency(
        cls,
        session: AsyncSession,
        workspace_id: uuid.UUID,
    ) -> None:
        """
        Ensures a single workspace does not exceed maximum concurrent running jobs,
        guaranteeing multi-tenant fairness across the cluster.
        """
        stmt = (
            select(func.count(Job.id))
            .where(
                Job.workspace_id == workspace_id,
                Job.status == JobStatus.RUNNING.value,
            )
        )
        res = await session.execute(stmt)
        active_count = res.scalar() or 0

        if active_count >= cls.MAX_WORKSPACE_RUNNING_JOBS:
            raise JobConcurrencyError(
                f"Workspace has reached maximum concurrent active jobs ({active_count}/{cls.MAX_WORKSPACE_RUNNING_JOBS})."
            )

    @classmethod
    async def validate_parent_dependency(
        cls,
        session: AsyncSession,
        parent_job_id: Optional[uuid.UUID],
        workspace_id: uuid.UUID,
    ) -> None:
        """
        Validates that parent job belongs to the same workspace.
        """
        if not parent_job_id:
            return

        stmt = select(Job).where(Job.id == parent_job_id, Job.workspace_id == workspace_id)
        parent = (await session.execute(stmt)).scalar_one_or_none()
        if not parent:
            raise JobValidationError(f"Parent job '{parent_job_id}' does not exist in workspace.")
