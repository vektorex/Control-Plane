"""
Security Incident Management Service for Step 34.
Coordinates incident lifecycle: creation, triage, assignment, investigation, resolution, and append-only timeline events.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.services.security.exceptions import SecurityIncidentNotFoundError
from backend.app.services.security.models import (
    IncidentSignal,
    IncidentTimelineEvent,
    SecurityIncident,
    SecuritySignal,
)
from backend.app.services.security.schemas import (
    SecurityIncidentCreate,
    SecurityIncidentUpdate,
)


class SecurityIncidentService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_incident(
        self,
        organization_id: str,
        data: SecurityIncidentCreate,
        created_by: Optional[str] = None,
    ) -> SecurityIncident:
        """
        Manually or programmatically creates a new SecurityIncident.
        """
        now = datetime.now(timezone.utc)
        incident = SecurityIncident(
            organization_id=organization_id,
            workspace_id=data.workspace_id,
            project_id=data.project_id,
            title=data.title,
            description=data.description,
            category=data.category,
            severity=data.severity,
            status="open",
            detected_at=now,
            first_seen_at=now,
            last_seen_at=now,
            assigned_to=data.assigned_to,
            metadata_payload=data.metadata,
            created_at=now,
        )
        self.session.add(incident)
        await self.session.flush()

        # Link any initial signals
        if data.signal_ids:
            for sid in set(data.signal_ids):
                link = IncidentSignal(
                    incident_id=incident.id,
                    signal_id=sid,
                    relationship="supporting",
                    created_at=now,
                )
                self.session.add(link)

        # Timeline event for creation
        tl = IncidentTimelineEvent(
            incident_id=incident.id,
            timestamp=now,
            event_type="incident_opened",
            source_type="user" if created_by else "system",
            source_id=created_by,
            actor_type="user" if created_by else "system",
            actor_id=created_by,
            summary=f"Incident opened with severity '{incident.severity}' and category '{incident.category}'",
            metadata_payload={"title": incident.title},
        )
        self.session.add(tl)
        await self.session.flush()
        return incident

    async def list_incidents(
        self,
        organization_id: str,
        workspace_id: Optional[str] = None,
        category: Optional[str] = None,
        severity: Optional[str] = None,
        status: Optional[str] = None,
        assigned_to: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[SecurityIncident]:
        """
        Lists tenant-scoped incidents with filters.
        """
        query = (
            select(SecurityIncident)
            .where(SecurityIncident.organization_id == organization_id)
            .options(selectinload(SecurityIncident.signals))
        )

        if workspace_id:
            query = query.where(SecurityIncident.workspace_id == workspace_id)
        if category:
            query = query.where(SecurityIncident.category == category)
        if severity:
            query = query.where(SecurityIncident.severity == severity)
        if status:
            query = query.where(SecurityIncident.status == status)
        if assigned_to:
            query = query.where(SecurityIncident.assigned_to == assigned_to)

        query = query.order_by(desc(SecurityIncident.last_seen_at)).limit(limit).offset(offset)
        res = await self.session.execute(query)
        return list(res.scalars().all())

    async def get_incident_by_id(
        self,
        incident_id: str,
        organization_id: str,
    ) -> SecurityIncident:
        """
        Fetches an incident by ID within the organization boundary.
        """
        query = (
            select(SecurityIncident)
            .where(
                SecurityIncident.id == incident_id,
                SecurityIncident.organization_id == organization_id,
            )
            .options(
                selectinload(SecurityIncident.signals).selectinload(IncidentSignal.signal),
                selectinload(SecurityIncident.timeline_events),
                selectinload(SecurityIncident.containment_actions),
            )
        )
        res = await self.session.execute(query)
        inc = res.scalar_one_or_none()
        if not inc:
            raise SecurityIncidentNotFoundError(f"Security incident '{incident_id}' not found.")
        return inc

    async def update_incident(
        self,
        incident_id: str,
        organization_id: str,
        data: SecurityIncidentUpdate,
        updated_by: Optional[str] = None,
    ) -> SecurityIncident:
        """
        Updates an existing incident and writes an append-only timeline record.
        """
        inc = await self.get_incident_by_id(incident_id, organization_id)
        now = datetime.now(timezone.utc)

        changes = []
        if data.title is not None and data.title != inc.title:
            changes.append(f"Title changed to '{data.title}'")
            inc.title = data.title
        if data.description is not None:
            inc.description = data.description
        if data.severity is not None and data.severity != inc.severity:
            changes.append(f"Severity adjusted from '{inc.severity}' to '{data.severity}'")
            inc.severity = data.severity
        if data.status is not None and data.status != inc.status:
            changes.append(f"Status transitioned from '{inc.status}' to '{data.status}'")
            inc.status = data.status
            if data.status == "resolved":
                inc.resolved_at = now
                inc.resolved_by = updated_by
                if data.resolution_summary:
                    inc.resolution_summary = data.resolution_summary
        if data.assigned_to is not None and data.assigned_to != inc.assigned_to:
            changes.append(f"Assigned to '{data.assigned_to}'")
            inc.assigned_to = data.assigned_to
        if data.metadata:
            meta = dict(inc.metadata_payload or {})
            meta.update(data.metadata)
            inc.metadata_payload = meta

        inc.updated_at = now

        if changes:
            tl = IncidentTimelineEvent(
                incident_id=inc.id,
                timestamp=now,
                event_type="incident_updated",
                source_type="user",
                source_id=updated_by,
                actor_type="user",
                actor_id=updated_by,
                summary="; ".join(changes),
                metadata_payload={"changes": changes},
            )
            self.session.add(tl)

        await self.session.flush()
        return inc

    async def add_timeline_event(
        self,
        incident_id: str,
        organization_id: str,
        event_type: str,
        summary: str,
        actor_id: Optional[str] = None,
        source_type: str = "system",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> IncidentTimelineEvent:
        """
        Appends an immutable timeline record to an incident.
        """
        inc = await self.get_incident_by_id(incident_id, organization_id)
        now = datetime.now(timezone.utc)
        tl = IncidentTimelineEvent(
            incident_id=inc.id,
            timestamp=now,
            event_type=event_type,
            source_type=source_type,
            actor_type="user" if actor_id else "system",
            actor_id=actor_id,
            summary=summary,
            metadata_payload=metadata or {},
        )
        self.session.add(tl)
        await self.session.flush()
        return tl
