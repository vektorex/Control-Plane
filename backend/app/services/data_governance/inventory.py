"""
Data Inventory Service for Step 33.
Maintains logical inventory of all platform data assets, PII findings, and access logs.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import desc, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.services.data_governance.exceptions import DataAssetNotFoundError
from backend.app.services.data_governance.models import (
    ClassificationRecord,
    DataAccessRecord,
    DataAsset,
    DataFinding,
)
from backend.app.services.data_governance.redaction import detect_findings
from backend.app.services.data_governance.schemas import DataAssetCreate, DataAssetUpdate


class DataInventoryService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def register_asset(
        self,
        organization_id: str,
        data: DataAssetCreate,
        sample_content: Optional[str] = None,
        detected_by: str = "system",
        confidence: float = 1.0,
    ) -> DataAsset:
        """
        Registers or updates a logical DataAsset in the inventory.
        Performs automatic deterministic PII/secret scanning on provided sample/initial content.
        """
        # Check if asset already exists by resource_type and resource_id
        q = select(DataAsset).where(
            DataAsset.organization_id == organization_id,
            DataAsset.resource_type == data.resource_type,
            DataAsset.resource_id == data.resource_id,
        ).options(selectinload(DataAsset.classifications), selectinload(DataAsset.findings))

        res = await self.session.execute(q)
        existing = res.scalar_one_or_none()

        now = datetime.now(timezone.utc)

        findings_list = []
        has_secrets = data.contains_secrets
        has_personal = data.contains_personal_data
        has_sensitive = data.contains_sensitive_data

        if sample_content:
            raw_findings = detect_findings(sample_content)
            for rf in raw_findings:
                if rf["is_secret"]:
                    has_secrets = True
                    has_sensitive = True
                if rf["is_personal_data"]:
                    has_personal = True
                    has_sensitive = True
                findings_list.append(rf)

        if existing:
            existing.name = data.name
            existing.description = data.description or existing.description
            existing.workspace_id = data.workspace_id or existing.workspace_id
            existing.project_id = data.project_id or existing.project_id
            existing.storage_location = data.storage_location or existing.storage_location
            existing.updated_at = now
            existing.contains_secrets = existing.contains_secrets or has_secrets
            existing.contains_personal_data = existing.contains_personal_data or has_personal
            existing.contains_sensitive_data = existing.contains_sensitive_data or has_sensitive

            asset = existing
        else:
            asset = DataAsset(
                organization_id=organization_id,
                workspace_id=data.workspace_id,
                project_id=data.project_id,
                asset_type=data.asset_type,
                resource_type=data.resource_type,
                resource_id=data.resource_id,
                name=data.name,
                description=data.description,
                data_classification=data.data_classification,
                owner_type=data.owner_type,
                owner_id=data.owner_id,
                source_type=data.source_type,
                source_id=data.source_id,
                storage_location=data.storage_location,
                contains_personal_data=has_personal,
                contains_sensitive_data=has_sensitive,
                contains_secrets=has_secrets,
                retention_policy_id=data.retention_policy_id,
                status="active",
                created_at=now,
                updated_at=now,
            )
            self.session.add(asset)
            await self.session.flush()

            # Record initial classification
            classification_rec = ClassificationRecord(
                asset_id=asset.id,
                classification=data.data_classification,
                reason=f"Initial registration via {detected_by}",
                detected_by=detected_by,
                confidence=confidence,
                created_at=now,
                updated_at=now,
            )
            self.session.add(classification_rec)

        # Add detected findings
        for f in findings_list:
            df = DataFinding(
                asset_id=asset.id,
                finding_type=f["finding_type"],
                location=f["location"],
                redaction_strategy=f["redaction_strategy"],
                confidence=f["confidence"],
                fingerprint=f["fingerprint"],
                preview=f["preview"],
                created_at=now,
            )
            self.session.add(df)

        await self.session.flush()
        await self.session.refresh(asset)
        return asset

    async def get_asset(
        self,
        asset_id: str,
        organization_id: str,
    ) -> DataAsset:
        """
        Retrieves a DataAsset ensuring tenant isolation.
        """
        q = (
            select(DataAsset)
            .where(DataAsset.id == asset_id, DataAsset.organization_id == organization_id)
            .options(
                selectinload(DataAsset.classifications),
                selectinload(DataAsset.findings),
            )
        )
        res = await self.session.execute(q)
        asset = res.scalar_one_or_none()
        if not asset:
            raise DataAssetNotFoundError(f"Data asset '{asset_id}' not found.")
        return asset

    async def list_assets(
        self,
        organization_id: str,
        workspace_id: Optional[str] = None,
        project_id: Optional[str] = None,
        asset_type: Optional[str] = None,
        resource_type: Optional[str] = None,
        classification: Optional[str] = None,
        status: Optional[str] = None,
        contains_secrets: Optional[bool] = None,
        contains_personal_data: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[DataAsset]:
        """
        Lists assets with filtering and pagination.
        """
        q = select(DataAsset).where(DataAsset.organization_id == organization_id)
        if workspace_id:
            q = q.where(DataAsset.workspace_id == workspace_id)
        if project_id:
            q = q.where(DataAsset.project_id == project_id)
        if asset_type:
            q = q.where(DataAsset.asset_type == asset_type)
        if resource_type:
            q = q.where(DataAsset.resource_type == resource_type)
        if classification:
            q = q.where(DataAsset.data_classification == classification)
        if status:
            q = q.where(DataAsset.status == status)
        if contains_secrets is not None:
            q = q.where(DataAsset.contains_secrets == contains_secrets)
        if contains_personal_data is not None:
            q = q.where(DataAsset.contains_personal_data == contains_personal_data)

        q = q.order_by(desc(DataAsset.created_at)).limit(limit).offset(offset)
        q = q.options(selectinload(DataAsset.classifications), selectinload(DataAsset.findings))

        res = await self.session.execute(q)
        return list(res.scalars().all())

    async def record_access(
        self,
        organization_id: str,
        asset_id: str,
        actor_id: str,
        action: str,
        result: str,
        actor_type: str = "user",
        workspace_id: Optional[str] = None,
        request_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> DataAccessRecord:
        """
        Audits meaningful application-level access to a data asset.
        """
        rec = DataAccessRecord(
            organization_id=organization_id,
            workspace_id=workspace_id,
            asset_id=asset_id,
            actor_type=actor_type,
            actor_id=actor_id,
            action=action,
            result=result,
            timestamp=datetime.now(timezone.utc),
            request_id=request_id,
            correlation_id=correlation_id,
        )
        self.session.add(rec)

        # Update last_accessed_at on the asset
        stmt = (
            update(DataAsset)
            .where(DataAsset.id == asset_id)
            .values(last_accessed_at=datetime.now(timezone.utc))
        )
        await self.session.execute(stmt)
        await self.session.flush()
        return rec

    async def list_access_history(
        self,
        asset_id: str,
        organization_id: str,
        limit: int = 50,
    ) -> List[DataAccessRecord]:
        """
        Retrieves the access audit history for an asset.
        """
        q = (
            select(DataAccessRecord)
            .where(
                DataAccessRecord.asset_id == asset_id,
                DataAccessRecord.organization_id == organization_id,
            )
            .order_by(desc(DataAccessRecord.timestamp))
            .limit(limit)
        )
        res = await self.session.execute(q)
        return list(res.scalars().all())
