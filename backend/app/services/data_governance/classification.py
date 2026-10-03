"""
Data Classification Engine for Step 33.
Manages deterministic classification, review workflows, and prevents unauthorized downgrades.
"""
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import desc, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.data_governance.evidence import ComplianceEvidenceService
from backend.app.services.data_governance.exceptions import DataAssetNotFoundError
from backend.app.services.data_governance.models import ClassificationRecord, DataAsset
from backend.app.services.data_governance.validators import validate_classification_transition


class DataClassificationService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.evidence_service = ComplianceEvidenceService(session)

    async def update_classification(
        self,
        asset_id: str,
        organization_id: str,
        target_classification: str,
        reason: str,
        detected_by: str = "manual",
        confidence: float = 1.0,
        actor_id: Optional[str] = None,
        is_admin: bool = False,
    ) -> ClassificationRecord:
        """
        Updates the data classification of an asset.
        Strictly enforces that automated classification cannot silently downgrade
        confidential or restricted data without authorized review.
        """
        # Fetch asset
        q = select(DataAsset).where(
            DataAsset.id == asset_id,
            DataAsset.organization_id == organization_id,
        )
        res = await self.session.execute(q)
        asset = res.scalar_one_or_none()
        if not asset:
            raise DataAssetNotFoundError(f"Data asset '{asset_id}' not found.")

        # Validate transition
        validate_classification_transition(
            current_classification=asset.data_classification,
            target_classification=target_classification,
            detected_by=detected_by,
            is_admin=is_admin,
        )

        now = datetime.now(timezone.utc)
        record = ClassificationRecord(
            asset_id=asset.id,
            classification=target_classification.lower(),
            reason=reason,
            detected_by=detected_by,
            confidence=confidence,
            created_at=now,
            updated_at=now,
            reviewed_by=actor_id if detected_by == "user_confirmed" else None,
            reviewed_at=now if detected_by == "user_confirmed" else None,
        )
        self.session.add(record)

        # Update asset classification
        asset.data_classification = target_classification.lower()
        asset.updated_at = now

        await self.session.flush()
        await self.session.refresh(record)

        # Record compliance evidence
        await self.evidence_service.record_evidence(
            organization_id=organization_id,
            workspace_id=asset.workspace_id,
            evidence_type="classification",
            subject_type="data_asset",
            subject_id=asset.id,
            action=f"classify:{target_classification.lower()}",
            result="success",
            actor_type="user" if actor_id else "system",
            actor_id=actor_id,
            metadata={
                "previous_classification": asset.data_classification,
                "new_classification": target_classification.lower(),
                "detected_by": detected_by,
                "reason": reason,
            },
        )

        return record

    async def list_classifications(
        self,
        asset_id: str,
        organization_id: str,
    ) -> List[ClassificationRecord]:
        """
        Lists chronological classification determinations for an asset.
        """
        q = (
            select(ClassificationRecord)
            .join(DataAsset, ClassificationRecord.asset_id == DataAsset.id)
            .where(
                ClassificationRecord.asset_id == asset_id,
                DataAsset.organization_id == organization_id,
            )
            .order_by(desc(ClassificationRecord.created_at))
        )
        res = await self.session.execute(q)
        return list(res.scalars().all())
