"""
Retention Policy Engine for Step 33.
Manages retention policy lifecycle, hierarchical resolution, and expiration detection.
"""
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.data_governance.exceptions import DataGovernanceError
from backend.app.services.data_governance.models import DataAsset, RetentionPolicy
from backend.app.services.data_governance.schemas import RetentionPolicyCreate, RetentionPolicyUpdate


class RetentionPolicyEngine:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_policy(
        self,
        organization_id: str,
        created_by: str,
        data: RetentionPolicyCreate,
    ) -> RetentionPolicy:
        """
        Creates a new retention policy for an organization or workspace.
        """
        now = datetime.now(timezone.utc)
        policy = RetentionPolicy(
            organization_id=organization_id,
            workspace_id=data.workspace_id,
            name=data.name,
            description=data.description,
            resource_type=data.resource_type,
            retention_days=data.retention_days,
            action=data.action,
            grace_period_days=data.grace_period_days,
            enabled=data.enabled,
            created_by=created_by,
            created_at=now,
            updated_at=now,
        )
        self.session.add(policy)
        await self.session.flush()
        await self.session.refresh(policy)
        return policy

    async def get_policy(self, policy_id: str, organization_id: str) -> Optional[RetentionPolicy]:
        q = select(RetentionPolicy).where(
            RetentionPolicy.id == policy_id,
            RetentionPolicy.organization_id == organization_id,
        )
        res = await self.session.execute(q)
        return res.scalar_one_or_none()

    async def list_policies(
        self,
        organization_id: str,
        workspace_id: Optional[str] = None,
        resource_type: Optional[str] = None,
    ) -> List[RetentionPolicy]:
        q = select(RetentionPolicy).where(RetentionPolicy.organization_id == organization_id)
        if workspace_id:
            q = q.where(RetentionPolicy.workspace_id == workspace_id)
        if resource_type:
            q = q.where(RetentionPolicy.resource_type == resource_type)
        q = q.order_by(desc(RetentionPolicy.created_at))
        res = await self.session.execute(q)
        return list(res.scalars().all())

    async def update_policy(
        self,
        policy_id: str,
        organization_id: str,
        data: RetentionPolicyUpdate,
    ) -> RetentionPolicy:
        policy = await self.get_policy(policy_id, organization_id)
        if not policy:
            raise DataGovernanceError(f"Retention policy '{policy_id}' not found.")

        if data.name is not None:
            policy.name = data.name
        if data.description is not None:
            policy.description = data.description
        if data.retention_days is not None:
            policy.retention_days = data.retention_days
        if data.action is not None:
            policy.action = data.action
        if data.grace_period_days is not None:
            policy.grace_period_days = data.grace_period_days
        if data.enabled is not None:
            policy.enabled = data.enabled

        policy.updated_at = datetime.now(timezone.utc)
        await self.session.flush()
        await self.session.refresh(policy)
        return policy

    async def delete_policy(self, policy_id: str, organization_id: str) -> bool:
        policy = await self.get_policy(policy_id, organization_id)
        if not policy:
            return False
        await self.session.delete(policy)
        await self.session.flush()
        return True

    async def resolve_policy_for_asset(
        self,
        asset: DataAsset,
    ) -> Optional[RetentionPolicy]:
        """
        Hierarchical policy resolution:
        1. Explicit policy assigned to asset via asset.retention_policy_id
        2. Workspace policy matching resource_type
        3. Organization policy matching resource_type
        """
        if asset.retention_policy_id:
            pol = await self.get_policy(asset.retention_policy_id, asset.organization_id)
            if pol and pol.enabled:
                return pol

        if asset.workspace_id:
            q_ws = select(RetentionPolicy).where(
                RetentionPolicy.organization_id == asset.organization_id,
                RetentionPolicy.workspace_id == asset.workspace_id,
                RetentionPolicy.resource_type == asset.resource_type,
                RetentionPolicy.enabled.is_(True),
            ).order_by(desc(RetentionPolicy.created_at)).limit(1)
            res_ws = await self.session.execute(q_ws)
            pol_ws = res_ws.scalar_one_or_none()
            if pol_ws:
                return pol_ws

        # Fallback to org level policy
        q_org = select(RetentionPolicy).where(
            RetentionPolicy.organization_id == asset.organization_id,
            RetentionPolicy.workspace_id.is_(None),
            RetentionPolicy.resource_type == asset.resource_type,
            RetentionPolicy.enabled.is_(True),
        ).order_by(desc(RetentionPolicy.created_at)).limit(1)
        res_org = await self.session.execute(q_org)
        return res_org.scalar_one_or_none()

    async def find_expired_assets(
        self,
        organization_id: str,
        workspace_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Scans active assets to identify which ones have exceeded their retention period.
        Returns list of dicts with asset and resolved policy action.
        """
        now = datetime.now(timezone.utc)
        q = select(DataAsset).where(
            DataAsset.organization_id == organization_id,
            DataAsset.status == "active",
        )
        if workspace_id:
            q = q.where(DataAsset.workspace_id == workspace_id)

        res = await self.session.execute(q)
        active_assets = res.scalars().all()

        expired = []
        for asset in active_assets:
            pol = await self.resolve_policy_for_asset(asset)
            if not pol or pol.retention_days is None:
                continue

            total_days = pol.retention_days + pol.grace_period_days
            expiry_date = asset.created_at + timedelta(days=total_days)

            if now >= expiry_date:
                expired.append({
                    "asset": asset,
                    "policy": pol,
                    "action": pol.action,
                    "expiry_date": expiry_date,
                })
                if len(expired) >= limit:
                    break

        return expired
