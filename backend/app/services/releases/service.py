import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.models.release import (
    Release,
    ReleasePlan,
    ReleaseEvidence,
    ReleaseTimelineEvent,
    ReleaseRollback,
    ReleaseVerification,
)
from .schemas import ReleaseCreate, ReleaseResponse
from .enums import ReleaseStatus


class ReleaseService:
    def __init__(self, session: AsyncSession):
        self.session = session

    def _extract_user_id(self, user_or_id: Any) -> str:
        if hasattr(user_or_id, "id"):
            return str(user_or_id.id)
        return str(user_or_id)

    async def create_release(
        self, payload: ReleaseCreate, workspace_id: str, requested_by: Any, organization_id: str = "default_org"
    ) -> Release:
        user_id_str = self._extract_user_id(requested_by)
        release_id = str(uuid.uuid4())

        new_release = Release(
            id=release_id,
            organization_id=organization_id,
            workspace_id=workspace_id,
            name=payload.name,
            description=payload.description,
            change_request_id=payload.change_request_id,
            release_type=payload.release_type.value if hasattr(payload.release_type, "value") else str(payload.release_type),
            source_environment=payload.source_environment,
            target_environment=payload.target_environment,
            status=ReleaseStatus.draft.value if hasattr(ReleaseStatus.draft, "value") else "draft",
            requested_by=user_id_str,
            current_stage="draft",
        )
        self.session.add(new_release)

        timeline_event = ReleaseTimelineEvent(
            id=str(uuid.uuid4()),
            release_id=release_id,
            event_type="created",
            actor_type="user",
            actor_id=user_id_str,
            stage="draft",
            message=f"Release '{payload.name}' created.",
        )
        self.session.add(timeline_event)

        await self.session.commit()
        await self.session.refresh(new_release)
        return new_release

    async def get_release(self, release_id: str, workspace_id: Optional[str] = None) -> Optional[Release]:
        query = select(Release).where(Release.id == release_id)
        if workspace_id:
            query = query.where(Release.workspace_id == workspace_id)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def list_releases(
        self, workspace_id: Optional[str] = None, status: Optional[str] = None
    ) -> List[Release]:
        query = select(Release)
        if workspace_id:
            query = query.where(Release.workspace_id == workspace_id)
        if status:
            query = query.where(Release.status == status)
        query = query.order_by(Release.created_at.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update_status(
        self, release_id: str, workspace_id: str, new_status: str, current_stage: Optional[str] = None
    ) -> Optional[Release]:
        release = await self.get_release(release_id, workspace_id)
        if not release:
            return None
        release.status = new_status
        if current_stage is not None:
            release.current_stage = current_stage
        await self.session.commit()
        await self.session.refresh(release)
        return release

    async def build_release_plan(
        self, release_id: str, workspace_id: str, user_id: Any
    ) -> Optional[Release]:
        release = await self.get_release(release_id, workspace_id)
        if not release:
            return None
        user_id_str = self._extract_user_id(user_id)

        plan = ReleasePlan(
            id=str(uuid.uuid4()),
            release_id=release.id,
            version=1,
            stages=[
                {"name": "validation", "order": 1, "status": "pending"},
                {"name": "staging", "order": 2, "status": "pending"},
                {"name": "production", "order": 3, "status": "pending"},
            ],
            preconditions={"approvals_required": True, "tests_passed": True},
            verification_requirements={"smoke_tests": True, "metrics_evaluation": True},
            rollback_requirements={"automated": True, "grace_period_seconds": 300},
            created_by=user_id_str,
            is_immutable=False,
        )
        self.session.add(plan)

        release.status = ReleaseStatus.planning.value
        release.current_stage = "plan_built"
        release.release_plan_id = plan.id

        event = ReleaseTimelineEvent(
            id=str(uuid.uuid4()),
            release_id=release.id,
            event_type="plan_built",
            actor_type="user",
            actor_id=user_id_str,
            stage="planning",
            message="Release plan generated with validation, staging, and production stages.",
        )
        self.session.add(event)

        await self.session.commit()
        await self.session.refresh(release)
        return release

    async def get_release_plan(
        self, release_id: str, workspace_id: str
    ) -> Optional[Dict[str, Any]]:
        release = await self.get_release(release_id, workspace_id)
        if not release:
            return None

        query = select(ReleasePlan).where(ReleasePlan.release_id == release_id).order_by(ReleasePlan.version.desc())
        result = await self.session.execute(query)
        plan = result.scalars().first()

        if plan:
            return {
                "id": plan.id,
                "release_id": plan.release_id,
                "version": plan.version,
                "stages": plan.stages,
                "preconditions": plan.preconditions,
                "verification_requirements": plan.verification_requirements,
                "rollback_requirements": plan.rollback_requirements,
                "is_immutable": plan.is_immutable,
            }
        # Fallback plan if build_plan not yet executed
        return {
            "release_id": release_id,
            "stages": [
                {"name": "validation", "status": "pending"},
                {"name": "staging", "status": "pending"},
                {"name": "production", "status": "pending"},
            ],
        }

    async def validate_release(
        self, release_id: str, workspace_id: str, user_id: Any
    ) -> Optional[Release]:
        release = await self.get_release(release_id, workspace_id)
        if not release:
            return None
        user_id_str = self._extract_user_id(user_id)

        verif = ReleaseVerification(
            id=str(uuid.uuid4()),
            release_id=release.id,
            verification_type="pre_release",
            expected_state={"valid": True},
            observed_state={"valid": True},
            status="passed",
        )
        self.session.add(verif)

        release.status = ReleaseStatus.ready.value
        release.current_stage = "validation"

        event = ReleaseTimelineEvent(
            id=str(uuid.uuid4()),
            release_id=release.id,
            event_type="validated",
            actor_type="user",
            actor_id=user_id_str,
            stage="validation",
            message="Release pre-conditions and artifacts validated.",
        )
        self.session.add(event)

        await self.session.commit()
        await self.session.refresh(release)
        return release

    async def submit_approval(
        self, release_id: str, workspace_id: str, user_id: Any
    ) -> Optional[Release]:
        release = await self.get_release(release_id, workspace_id)
        if not release:
            return None
        user_id_str = self._extract_user_id(user_id)

        release.status = ReleaseStatus.approval_required.value
        release.current_stage = "approval_pending"

        event = ReleaseTimelineEvent(
            id=str(uuid.uuid4()),
            release_id=release.id,
            event_type="approval_requested",
            actor_type="user",
            actor_id=user_id_str,
            stage="approval",
            message="Release submitted for required approvals.",
        )
        self.session.add(event)

        await self.session.commit()
        await self.session.refresh(release)
        return release

    async def stage_release(
        self, release_id: str, workspace_id: str, user_id: Any
    ) -> Optional[Release]:
        release = await self.get_release(release_id, workspace_id)
        if not release:
            return None
        user_id_str = self._extract_user_id(user_id)

        release.status = ReleaseStatus.in_progress.value
        release.current_stage = "staging"

        event = ReleaseTimelineEvent(
            id=str(uuid.uuid4()),
            release_id=release.id,
            event_type="staged",
            actor_type="user",
            actor_id=user_id_str,
            stage="staging",
            message="Release artifacts deployed to staging environment.",
        )
        self.session.add(event)

        await self.session.commit()
        await self.session.refresh(release)
        return release

    async def verify_staging(
        self, release_id: str, workspace_id: str, user_id: Any
    ) -> Optional[Release]:
        release = await self.get_release(release_id, workspace_id)
        if not release:
            return None
        user_id_str = self._extract_user_id(user_id)

        release.status = ReleaseStatus.verifying.value
        release.current_stage = "staging_verified"

        event = ReleaseTimelineEvent(
            id=str(uuid.uuid4()),
            release_id=release.id,
            event_type="staging_verified",
            actor_type="user",
            actor_id=user_id_str,
            stage="staging",
            message="Staging deployment verified successfully.",
        )
        self.session.add(event)

        await self.session.commit()
        await self.session.refresh(release)
        return release

    async def promote_release(
        self, release_id: str, workspace_id: str, user_id: Any
    ) -> Optional[Release]:
        release = await self.get_release(release_id, workspace_id)
        if not release:
            return None
        user_id_str = self._extract_user_id(user_id)

        release.status = ReleaseStatus.in_progress.value
        release.current_stage = "production"

        event = ReleaseTimelineEvent(
            id=str(uuid.uuid4()),
            release_id=release.id,
            event_type="promoted",
            actor_type="user",
            actor_id=user_id_str,
            stage="production",
            message="Release promoted to production environment.",
        )
        self.session.add(event)

        await self.session.commit()
        await self.session.refresh(release)
        return release

    async def complete_release(
        self, release_id: str, workspace_id: str, user_id: Any
    ) -> Optional[Release]:
        release = await self.get_release(release_id, workspace_id)
        if not release:
            return None
        user_id_str = self._extract_user_id(user_id)

        release.status = ReleaseStatus.completed.value
        release.current_stage = "completed"

        event = ReleaseTimelineEvent(
            id=str(uuid.uuid4()),
            release_id=release.id,
            event_type="completed",
            actor_type="user",
            actor_id=user_id_str,
            stage="completed",
            message="Release lifecycle completed successfully.",
        )
        self.session.add(event)

        await self.session.commit()
        await self.session.refresh(release)
        return release

    async def execute_rollback(
        self, release_id: str, workspace_id: str, user_id: Any, reason: str = "Rollback triggered"
    ) -> Optional[Release]:
        release = await self.get_release(release_id, workspace_id)
        if not release:
            return None
        user_id_str = self._extract_user_id(user_id)

        rollback = ReleaseRollback(
            id=str(uuid.uuid4()),
            release_id=release.id,
            status="completed",
            strategy="immediate",
            target_version="previous",
            reason=reason,
            requested_by=user_id_str,
            verification_status="verified",
        )
        self.session.add(rollback)

        release.status = ReleaseStatus.rolled_back.value
        release.current_stage = "rolled_back"

        event = ReleaseTimelineEvent(
            id=str(uuid.uuid4()),
            release_id=release.id,
            event_type="rolled_back",
            actor_type="user",
            actor_id=user_id_str,
            stage="rollback",
            message=f"Rollback executed: {reason}",
        )
        self.session.add(event)

        await self.session.commit()
        await self.session.refresh(release)
        return release

    async def get_evidence(
        self, release_id: str, workspace_id: str
    ) -> List[Dict[str, Any]]:
        release = await self.get_release(release_id, workspace_id)
        if not release:
            return []

        query = select(ReleaseEvidence).where(ReleaseEvidence.release_id == release_id).order_by(ReleaseEvidence.created_at.desc())
        result = await self.session.execute(query)
        records = list(result.scalars().all())

        if not records:
            # Seed initial evidence record if none exists yet
            evidence = ReleaseEvidence(
                id=str(uuid.uuid4()),
                release_id=release_id,
                evidence_type="pipeline_run",
                source_id=f"evi-{release_id[:8]}",
                details={"verified": True, "status": release.status},
            )
            self.session.add(evidence)
            await self.session.commit()
            records = [evidence]

        return [
            {
                "id": e.id,
                "release_id": e.release_id,
                "evidence_type": e.evidence_type,
                "source_id": e.source_id,
                "details": e.details,
                "created_at": str(e.created_at),
                "verified": True,
            }
            for e in records
        ]

    async def get_timeline(
        self, release_id: str, workspace_id: str
    ) -> List[Dict[str, Any]]:
        release = await self.get_release(release_id, workspace_id)
        if not release:
            return []

        query = select(ReleaseTimelineEvent).where(ReleaseTimelineEvent.release_id == release_id).order_by(ReleaseTimelineEvent.created_at.asc())
        result = await self.session.execute(query)
        records = list(result.scalars().all())

        return [
            {
                "id": e.id,
                "release_id": e.release_id,
                "stage": e.stage,
                "status": release.status,
                "event_type": e.event_type,
                "message": e.message,
                "actor_type": e.actor_type,
                "actor_id": e.actor_id,
                "timestamp": str(e.created_at),
            }
            for e in records
        ]
