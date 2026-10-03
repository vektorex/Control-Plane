"""
Data Export Engine for Step 33.
Generates sanitized, tenant-scoped compliance exports with manifest metadata.
Never includes credentials, passwords, or raw secrets.
"""
import csv
import io
import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.data_governance.evidence import ComplianceEvidenceService
from backend.app.services.data_governance.exceptions import ExportSanitizationError
from backend.app.services.data_governance.models import DataAsset, ExportRequest
from backend.app.services.data_governance.redaction import sanitize_payload
from backend.app.services.data_governance.schemas import ExportManifest, ExportRequestCreate
from backend.app.services.data_governance.validators import validate_export_scope


class DataExportEngine:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.evidence_service = ComplianceEvidenceService(session)

    async def create_export_request(
        self,
        organization_id: str,
        requested_by: str,
        data: ExportRequestCreate,
    ) -> ExportRequest:
        """
        Creates an export request after validating scope parameters.
        """
        validate_export_scope(data.scope_type, data.scope_id)

        now = datetime.now(timezone.utc)
        req = ExportRequest(
            organization_id=organization_id,
            workspace_id=data.workspace_id,
            requested_by=requested_by,
            scope_type=data.scope_type,
            scope_id=data.scope_id,
            format=data.format.lower(),
            status="requested",
            created_at=now,
        )
        self.session.add(req)
        await self.session.flush()
        await self.session.refresh(req)
        return req

    async def execute_export(
        self,
        request_id: str,
        organization_id: str,
    ) -> Tuple[ExportRequest, str]:
        """
        Gathers scoped assets, strictly sanitizes secrets, generates export data, and produces manifest.
        Returns (ExportRequest, serialized_export_data).
        """
        q = select(ExportRequest).where(
            ExportRequest.id == request_id,
            ExportRequest.organization_id == organization_id,
        )
        res = await self.session.execute(q)
        req = res.scalar_one_or_none()
        if not req:
            raise ExportSanitizationError(f"Export request '{request_id}' not found.")

        now = datetime.now(timezone.utc)
        req.status = "processing"
        req.started_at = now
        await self.session.flush()

        # Query scoped assets
        q_ast = select(DataAsset).where(
            DataAsset.organization_id == organization_id,
            DataAsset.status != "deleted",
        )
        if req.scope_type == "asset":
            q_ast = q_ast.where(DataAsset.id == req.scope_id)
        elif req.scope_type == "workspace":
            q_ast = q_ast.where(DataAsset.workspace_id == req.scope_id)
        elif req.scope_type == "project":
            q_ast = q_ast.where(DataAsset.project_id == req.scope_id)
        elif req.scope_type == "user":
            q_ast = q_ast.where(DataAsset.owner_id == req.scope_id)

        res_ast = await self.session.execute(q_ast)
        assets = res_ast.scalars().all()

        sanitized_asset_records = []
        for a in assets:
            record = {
                "asset_id": a.id,
                "name": a.name,
                "description": a.description,
                "asset_type": a.asset_type,
                "resource_type": a.resource_type,
                "resource_id": a.resource_id,
                "classification": a.data_classification,
                "owner_id": a.owner_id,
                "source_type": a.source_type,
                "storage_location": a.storage_location,
                "created_at": a.created_at.isoformat() if a.created_at else None,
                "updated_at": a.updated_at.isoformat() if a.updated_at else None,
            }
            # Strictly scrub credentials
            sanitized_asset_records.append(sanitize_payload(record))

        # Format output
        serialized_content = ""
        if req.format == "json":
            serialized_content = json.dumps(sanitized_asset_records, indent=2)
        elif req.format == "jsonl":
            serialized_content = "\n".join(json.dumps(r) for r in sanitized_asset_records)
        elif req.format == "csv":
            if sanitized_asset_records:
                output = io.StringIO()
                writer = csv.DictWriter(output, fieldnames=list(sanitized_asset_records[0].keys()))
                writer.writeheader()
                writer.writerows(sanitized_asset_records)
                serialized_content = output.getvalue()

        # Build Manifest
        manifest = ExportManifest(
            export_id=req.id,
            organization_id=organization_id,
            workspace_id=req.workspace_id,
            scope_type=req.scope_type,
            scope_id=req.scope_id,
            format=req.format,
            asset_count=len(sanitized_asset_records),
            assets=sanitized_asset_records,
            created_at=datetime.now(timezone.utc),
            sanitized=True,
            version="1.0",
        )

        req.status = "completed"
        req.completed_at = datetime.now(timezone.utc)
        req.expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        req.manifest = manifest.model_dump(mode="json")

        await self.session.flush()
        await self.session.refresh(req)

        # Record compliance evidence
        await self.evidence_service.record_evidence(
            organization_id=organization_id,
            workspace_id=req.workspace_id,
            evidence_type="export",
            subject_type=req.scope_type,
            subject_id=req.scope_id,
            action="execute_export",
            result="completed",
            actor_type="user",
            actor_id=req.requested_by,
            metadata={
                "export_id": req.id,
                "format": req.format,
                "asset_count": len(sanitized_asset_records),
                "expires_at": req.expires_at.isoformat(),
            },
        )

        return req, serialized_content

    async def list_exports(
        self,
        organization_id: str,
        workspace_id: Optional[str] = None,
    ) -> List[ExportRequest]:
        q = select(ExportRequest).where(ExportRequest.organization_id == organization_id)
        if workspace_id:
            q = q.where(ExportRequest.workspace_id == workspace_id)
        q = q.order_by(desc(ExportRequest.created_at))
        res = await self.session.execute(q)
        return list(res.scalars().all())
