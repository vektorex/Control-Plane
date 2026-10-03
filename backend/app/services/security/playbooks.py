"""
Security Playbooks Service for Step 34.
Manages automated and semi-automated incident response playbooks with strict allowlist verification.
No arbitrary code, shell commands, or arbitrary HTTP requests permitted.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.security.models import SecurityPlaybook
from backend.app.services.security.schemas import (
    PlaybookTestRequest,
    PlaybookTestResponse,
    SecurityPlaybookCreate,
    SecurityPlaybookUpdate,
)
from backend.app.services.security.validators import validate_playbook_actions


class SecurityPlaybookService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_playbook(
        self,
        organization_id: Optional[str],
        created_by: str,
        data: SecurityPlaybookCreate,
    ) -> SecurityPlaybook:
        """
        Creates a new security playbook after strict allowlist validation of planned actions.
        """
        validate_playbook_actions(data.actions)

        now = datetime.now(timezone.utc)
        pb = SecurityPlaybook(
            organization_id=organization_id,
            name=data.name,
            description=data.description,
            trigger_conditions=data.trigger_conditions,
            actions=data.actions,
            enabled=data.enabled,
            created_by=created_by,
            created_at=now,
            updated_at=now,
        )
        self.session.add(pb)
        await self.session.flush()
        return pb

    async def list_playbooks(
        self,
        organization_id: Optional[str] = None,
        enabled_only: bool = False,
    ) -> List[SecurityPlaybook]:
        """
        Lists tenant and system-level response playbooks.
        """
        query = select(SecurityPlaybook)
        if organization_id:
            query = query.where(
                (SecurityPlaybook.organization_id == organization_id)
                | (SecurityPlaybook.organization_id.is_(None))
            )
        if enabled_only:
            query = query.where(SecurityPlaybook.enabled.is_(True))

        query = query.order_by(desc(SecurityPlaybook.created_at))
        res = await self.session.execute(query)
        return list(res.scalars().all())

    async def get_playbook_by_id(
        self,
        playbook_id: str,
        organization_id: Optional[str] = None,
    ) -> Optional[SecurityPlaybook]:
        """
        Fetches a single playbook.
        """
        query = select(SecurityPlaybook).where(SecurityPlaybook.id == playbook_id)
        if organization_id:
            query = query.where(
                (SecurityPlaybook.organization_id == organization_id)
                | (SecurityPlaybook.organization_id.is_(None))
            )
        res = await self.session.execute(query)
        return res.scalar_one_or_none()

    async def update_playbook(
        self,
        playbook_id: str,
        organization_id: Optional[str],
        data: SecurityPlaybookUpdate,
    ) -> SecurityPlaybook:
        """
        Updates an existing playbook with action validation.
        """
        pb = await self.get_playbook_by_id(playbook_id, organization_id)
        if not pb:
            raise ValueError(f"Playbook '{playbook_id}' not found.")

        if data.actions is not None:
            validate_playbook_actions(data.actions)
            pb.actions = data.actions

        if data.name is not None:
            pb.name = data.name
        if data.description is not None:
            pb.description = data.description
        if data.trigger_conditions is not None:
            pb.trigger_conditions = data.trigger_conditions
        if data.enabled is not None:
            pb.enabled = data.enabled

        pb.updated_at = datetime.now(timezone.utc)
        await self.session.flush()
        return pb

    async def delete_playbook(
        self,
        playbook_id: str,
        organization_id: Optional[str],
    ) -> bool:
        """
        Deletes a tenant playbook.
        """
        pb = await self.get_playbook_by_id(playbook_id, organization_id)
        if not pb:
            return False
        await self.session.delete(pb)
        await self.session.flush()
        return True

    def test_playbook_match(
        self,
        playbook: SecurityPlaybook,
        req: PlaybookTestRequest,
    ) -> PlaybookTestResponse:
        """
        Simulates trigger conditions evaluation against test signal payload.
        """
        conds = playbook.trigger_conditions or {}
        matched = True
        reasons: List[str] = []

        if "signal_type" in conds:
            expected_type = conds["signal_type"]
            if expected_type != req.signal_type:
                matched = False
                reasons.append(f"Signal type '{req.signal_type}' did not match condition '{expected_type}'")
            else:
                reasons.append(f"Signal type matched '{expected_type}'")

        if "min_severity" in conds:
            sev_levels = {"info": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}
            req_level = sev_levels.get(req.severity, 0)
            exp_level = sev_levels.get(conds["min_severity"], 0)
            if req_level < exp_level:
                matched = False
                reasons.append(f"Severity '{req.severity}' is lower than required minimum '{conds['min_severity']}'")
            else:
                reasons.append(f"Severity '{req.severity}' satisfies minimum '{conds['min_severity']}'")

        planned_actions = []
        if matched:
            for act in playbook.actions:
                planned_actions.append(act.get("action") or act.get("type", "unknown"))

        return PlaybookTestResponse(
            matched=matched,
            reasons=reasons,
            planned_actions=planned_actions,
        )
