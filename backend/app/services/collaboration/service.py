"""
High-Level Facade Service for Step 39: Multi-User Collaboration & Real-Time Co-Execution.
Unites sessions, presence, threaded comments, annotations, assignments, locking, and co-execution.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.collaboration.activity import CollaborationActivityLogger
from backend.app.services.collaboration.annotations import CollaborationAnnotationService
from backend.app.services.collaboration.assignments import CollaborationAssignmentService
from backend.app.services.collaboration.co_execution import CoExecutionService
from backend.app.services.collaboration.collaborative_state import CollaborativeStateManager
from backend.app.services.collaboration.comments import CollaborationCommentService
from backend.app.services.collaboration.events import CollaborationEventBroadcaster
from backend.app.services.collaboration.locking import CollaborationLockManager
from backend.app.services.collaboration.models import (
    CoExecutionSession,
    CollaborationActivity,
    CollaborationAnnotation,
    CollaborationAssignment,
    CollaborationComment,
    CollaborationDecision,
    CollaborationLock,
    CollaborationParticipant,
    CollaborationSession,
    PresenceState,
)
from backend.app.services.collaboration.notifications import CollaborationNotificationService
from backend.app.services.collaboration.permissions import CollaborationPermissionEvaluator
from backend.app.services.collaboration.presence import PresenceManager
from backend.app.services.collaboration.repository import CollaborationRepository
from backend.app.services.collaboration.sessions import CollaborationSessionManager
from backend.app.services.collaboration.workspace import SharedWorkspaceService


class CollaborationService:
    """Unified Facade for all Collaboration Subsystems."""

    def __init__(self, session: AsyncSession):
        self.db = session
        self.repo = CollaborationRepository(session)
        self.sessions = CollaborationSessionManager(session)
        self.presence = PresenceManager(session)
        self.activity = CollaborationActivityLogger(session)
        self.comments = CollaborationCommentService(session)
        self.assignments = CollaborationAssignmentService(session)
        self.annotations = CollaborationAnnotationService(session)
        self.state_mgr = CollaborativeStateManager(session)
        self.locking = CollaborationLockManager(session)
        self.co_execution = CoExecutionService(session)
        self.broadcaster = CollaborationEventBroadcaster(session)
        self.notifications = CollaborationNotificationService(session)
        self.workspace = SharedWorkspaceService(session)

    # -------------------------------------------------------------------------
    # Sessions & Presence
    # -------------------------------------------------------------------------

    async def create_session(
        self,
        organization_id: str,
        workspace_id: str,
        resource_type: str,
        resource_id: str,
        created_by: str,
        project_id: Optional[str] = None,
        expires_at: Optional[datetime] = None,
    ) -> CollaborationSession:
        session = await self.sessions.create_session(
            organization_id=organization_id,
            workspace_id=workspace_id,
            resource_type=resource_type,
            resource_id=resource_id,
            created_by=created_by,
            project_id=project_id,
            expires_at=expires_at,
        )

        await self.activity.log_activity(
            session_id=session.id,
            actor_type="user",
            actor_id=created_by,
            activity_type="created",
            resource_type=resource_type,
            resource_id=resource_id,
            summary=f"Collaboration session created for {resource_type} '{resource_id}'.",
        )

        await self.broadcaster.emit_collaboration_event(
            event_type="collaboration.session.created",
            organization_id=organization_id,
            workspace_id=workspace_id,
            session_id=session.id,
            actor_id=created_by,
            payload={"resource_type": resource_type, "resource_id": resource_id},
        )
        return session

    async def get_session(
        self,
        session_id: str,
        user_organization_id: str,
        user_workspace_id: Optional[str] = None,
    ) -> CollaborationSession:
        session = await self.sessions.get_session(session_id)
        CollaborationPermissionEvaluator.verify_tenant_boundary(
            session, user_organization_id, user_workspace_id
        )
        return session

    async def join_session(
        self,
        session_id: str,
        user_id: str,
        user_organization_id: str,
        user_workspace_id: Optional[str] = None,
        role: str = "editor",
    ) -> CollaborationParticipant:
        session = await self.get_session(session_id, user_organization_id, user_workspace_id)
        participant = await self.sessions.join_session(session_id, user_id, role)

        await self.presence.record_heartbeat(session_id, user_id, status="active")

        await self.activity.log_activity(
            session_id=session.id,
            actor_type="user",
            actor_id=user_id,
            activity_type="joined",
            resource_type=session.resource_type,
            resource_id=session.resource_id,
            summary=f"User joined session as {role}.",
        )

        await self.broadcaster.emit_collaboration_event(
            event_type="collaboration.participant.joined",
            organization_id=session.organization_id,
            workspace_id=session.workspace_id,
            session_id=session.id,
            actor_id=user_id,
            payload={"role": role},
        )
        return participant

    async def leave_session(
        self,
        session_id: str,
        user_id: str,
        user_organization_id: str,
        user_workspace_id: Optional[str] = None,
    ) -> CollaborationParticipant:
        session = await self.get_session(session_id, user_organization_id, user_workspace_id)
        participant = await self.sessions.leave_session(session_id, user_id)

        await self.activity.log_activity(
            session_id=session.id,
            actor_type="user",
            actor_id=user_id,
            activity_type="left",
            resource_type=session.resource_type,
            resource_id=session.resource_id,
            summary="User left collaboration session.",
        )

        await self.broadcaster.emit_collaboration_event(
            event_type="collaboration.participant.left",
            organization_id=session.organization_id,
            workspace_id=session.workspace_id,
            session_id=session.id,
            actor_id=user_id,
        )
        return participant

    async def record_heartbeat(
        self,
        session_id: str,
        user_id: str,
        user_organization_id: str,
        user_workspace_id: Optional[str] = None,
        status: str = "active",
        cursor_context: Optional[Dict[str, Any]] = None,
        active_resource: Optional[str] = None,
    ) -> PresenceState:
        session = await self.get_session(session_id, user_organization_id, user_workspace_id)
        presence, status_changed = await self.presence.record_heartbeat(
            session_id=session_id,
            user_id=user_id,
            status=status,
            cursor_context=cursor_context,
            active_resource=active_resource,
        )

        # Only emit presence update when status changes to prevent event storm
        if status_changed:
            await self.broadcaster.emit_collaboration_event(
                event_type="collaboration.presence.updated",
                organization_id=session.organization_id,
                workspace_id=session.workspace_id,
                session_id=session.id,
                actor_id=user_id,
                payload={"status": status},
            )

        return presence

    # -------------------------------------------------------------------------
    # Comments & Annotations
    # -------------------------------------------------------------------------

    async def add_comment(
        self,
        session_id: str,
        author_id: str,
        user_organization_id: str,
        user_workspace_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        body: str = "",
        parent_comment_id: Optional[str] = None,
        author_type: str = "user",
    ) -> CollaborationComment:
        session = await self.get_session(session_id, user_organization_id, user_workspace_id)
        participant = await self.repo.get_participant(session_id, author_id)
        CollaborationPermissionEvaluator.check_action_allowed(participant, "session.comment")

        res_type = resource_type or session.resource_type
        res_id = resource_id or session.resource_id

        comment = await self.comments.add_comment(
            session_id=session_id,
            organization_id=session.organization_id,
            workspace_id=session.workspace_id,
            author_id=author_id,
            resource_type=res_type,
            resource_id=res_id,
            body=body,
            author_type=author_type,
            parent_comment_id=parent_comment_id,
        )

        await self.activity.log_activity(
            session_id=session.id,
            actor_type=author_type,
            actor_id=author_id,
            activity_type="commented",
            resource_type=res_type,
            resource_id=res_id,
            summary="Added comment to conversation.",
        )

        await self.broadcaster.emit_collaboration_event(
            event_type="collaboration.comment.created",
            organization_id=session.organization_id,
            workspace_id=session.workspace_id,
            session_id=session.id,
            actor_id=author_id,
            payload={"comment_id": comment.id, "resource_id": res_id},
        )

        # Notify mentions
        for m in getattr(comment, "mentions", []):
            await self.notifications.notify_mention(
                workspace_id=session.workspace_id,
                mentioned_user_id=m.mentioned_user_id,
                author_id=author_id,
                resource_type=res_type,
                resource_id=res_id,
                session_id=session.id,
            )

        return comment

    async def add_annotation(
        self,
        session_id: str,
        author_id: str,
        user_organization_id: str,
        user_workspace_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        annotation_type: str = "text",
        target: Optional[Dict[str, Any]] = None,
        content: str = "",
    ) -> CollaborationAnnotation:
        session = await self.get_session(session_id, user_organization_id, user_workspace_id)
        participant = await self.repo.get_participant(session_id, author_id)
        CollaborationPermissionEvaluator.check_action_allowed(participant, "session.annotate")

        res_type = resource_type or session.resource_type
        res_id = resource_id or session.resource_id

        annotation = await self.annotations.create_annotation(
            session_id=session_id,
            resource_type=res_type,
            resource_id=res_id,
            author_id=author_id,
            annotation_type=annotation_type,
            target=target or {},
            content=content,
        )

        await self.activity.log_activity(
            session_id=session.id,
            actor_type="user",
            actor_id=author_id,
            activity_type="annotated",
            resource_type=res_type,
            resource_id=res_id,
            summary=f"Added {annotation_type} annotation.",
        )

        await self.broadcaster.emit_collaboration_event(
            event_type="collaboration.annotation.created",
            organization_id=session.organization_id,
            workspace_id=session.workspace_id,
            session_id=session.id,
            actor_id=author_id,
            payload={"annotation_id": annotation.id, "type": annotation_type},
        )
        return annotation

    # -------------------------------------------------------------------------
    # Assignments & Decisions
    # -------------------------------------------------------------------------

    async def create_assignment(
        self,
        session_id: str,
        assigned_by: str,
        assigned_to: str,
        assignment_type: str,
        user_organization_id: str,
        user_workspace_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        due_at: Optional[datetime] = None,
    ) -> CollaborationAssignment:
        session = await self.get_session(session_id, user_organization_id, user_workspace_id)
        participant = await self.repo.get_participant(session_id, assigned_by)
        CollaborationPermissionEvaluator.check_action_allowed(participant, "session.assign")

        res_type = resource_type or session.resource_type
        res_id = resource_id or session.resource_id

        assignment = await self.assignments.create_assignment(
            session_id=session_id,
            resource_type=res_type,
            resource_id=res_id,
            assigned_to=assigned_to,
            assigned_by=assigned_by,
            assignment_type=assignment_type,
            due_at=due_at,
        )

        await self.activity.log_activity(
            session_id=session.id,
            actor_type="user",
            actor_id=assigned_by,
            activity_type="assigned",
            resource_type=res_type,
            resource_id=res_id,
            summary=f"Assigned {assignment_type} task to user '{assigned_to}'.",
        )

        await self.broadcaster.emit_collaboration_event(
            event_type="collaboration.assignment.created",
            organization_id=session.organization_id,
            workspace_id=session.workspace_id,
            session_id=session.id,
            actor_id=assigned_by,
            payload={"assignment_id": assignment.id, "assigned_to": assigned_to},
        )

        await self.notifications.notify_assignment(
            workspace_id=session.workspace_id,
            assigned_to=assigned_to,
            assigned_by=assigned_by,
            assignment_type=assignment_type,
            resource_type=res_type,
            resource_id=res_id,
            session_id=session.id,
        )

        return assignment

    async def record_decision(
        self,
        session_id: str,
        created_by: str,
        decision_type: str,
        decision_data: dict,
        user_organization_id: str,
        user_workspace_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        supersedes_id: Optional[str] = None,
    ) -> CollaborationDecision:
        session = await self.get_session(session_id, user_organization_id, user_workspace_id)
        participant = await self.repo.get_participant(session_id, created_by)
        CollaborationPermissionEvaluator.check_action_allowed(participant, "session.approve")

        res_type = resource_type or session.resource_type
        res_id = resource_id or session.resource_id

        decision = await self.sessions.record_decision(
            session_id=session_id,
            resource_type=res_type,
            resource_id=res_id,
            decision_type=decision_type,
            decision_data=decision_data,
            created_by=created_by,
            supersedes_id=supersedes_id,
        )

        await self.activity.log_activity(
            session_id=session.id,
            actor_type="user",
            actor_id=created_by,
            activity_type=decision_type if decision_type in ("approved", "rejected") else "reviewed",
            resource_type=res_type,
            resource_id=res_id,
            summary=f"Recorded collaborative decision: {decision_type}.",
        )

        await self.broadcaster.emit_collaboration_event(
            event_type="collaboration.decision.created",
            organization_id=session.organization_id,
            workspace_id=session.workspace_id,
            session_id=session.id,
            actor_id=created_by,
            payload={"decision_id": decision.id, "type": decision_type},
        )
        return decision

    # -------------------------------------------------------------------------
    # Query & Lifecycle Methods
    # -------------------------------------------------------------------------

    async def list_sessions(
        self,
        organization_id: str,
        workspace_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[CollaborationSession]:
        return await self.sessions.list_sessions(
            organization_id=organization_id,
            workspace_id=workspace_id,
            resource_type=resource_type,
            resource_id=resource_id,
            status=status,
            limit=limit,
            offset=offset,
        )

    async def update_session(
        self,
        session_id: str,
        status: Optional[str],
        user_organization_id: str,
        user_workspace_id: Optional[str] = None,
    ) -> CollaborationSession:
        session = await self.get_session(session_id, user_organization_id, user_workspace_id)
        if status:
            session.status = status
        await self.db.flush()
        return session

    async def close_session(
        self,
        session_id: str,
        closed_by: str,
        user_organization_id: str,
        user_workspace_id: Optional[str] = None,
    ) -> CollaborationSession:
        session = await self.get_session(session_id, user_organization_id, user_workspace_id)
        participant = await self.repo.get_participant(session_id, closed_by)
        CollaborationPermissionEvaluator.check_action_allowed(participant, "session.edit")

        closed = await self.sessions.close_session(session_id, closed_by)
        await self.activity.log_activity(
            session_id=session.id,
            actor_type="user",
            actor_id=closed_by,
            activity_type="closed",
            resource_type=session.resource_type,
            resource_id=session.resource_id,
            summary="Collaboration session closed.",
        )
        return closed

    async def list_participants(
        self,
        session_id: str,
        user_organization_id: str,
        user_workspace_id: Optional[str] = None,
    ) -> List[CollaborationParticipant]:
        await self.get_session(session_id, user_organization_id, user_workspace_id)
        return await self.repo.list_participants(session_id)

    async def list_activity(
        self,
        session_id: str,
        user_organization_id: str,
        user_workspace_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        activity_type: Optional[str] = None,
    ) -> List[CollaborationActivity]:
        await self.get_session(session_id, user_organization_id, user_workspace_id)
        return await self.activity.list_activity(
            session_id=session_id,
            limit=limit,
            offset=offset,
            activity_type=activity_type,
        )

    async def list_comments(
        self,
        session_id: str,
        user_organization_id: str,
        user_workspace_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        include_deleted: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> List[CollaborationComment]:
        await self.get_session(session_id, user_organization_id, user_workspace_id)
        return await self.comments.list_comments(
            session_id=session_id,
            resource_type=resource_type,
            resource_id=resource_id,
            include_deleted=include_deleted,
            limit=limit,
            offset=offset,
        )

    async def update_comment(
        self,
        comment_id: str,
        user_id: str,
        user_organization_id: str,
        user_workspace_id: Optional[str] = None,
        body: Optional[str] = None,
        status: Optional[str] = None,
    ) -> CollaborationComment:
        comment = await self.comments.get_comment(comment_id)
        session = await self.get_session(comment.session_id, user_organization_id, user_workspace_id)
        if comment.author_id != user_id:
            participant = await self.repo.get_participant(session.id, user_id)
            CollaborationPermissionEvaluator.check_action_allowed(participant, "session.edit")

        updated = await self.comments.update_comment(comment_id, body=body, status=status)
        await self.broadcaster.emit_collaboration_event(
            event_type="collaboration.comment.updated",
            organization_id=session.organization_id,
            workspace_id=session.workspace_id,
            session_id=session.id,
            actor_id=user_id,
            payload={"comment_id": comment_id},
        )
        return updated

    async def delete_comment(
        self,
        comment_id: str,
        user_id: str,
        user_organization_id: str,
        user_workspace_id: Optional[str] = None,
    ) -> CollaborationComment:
        comment = await self.comments.get_comment(comment_id)
        session = await self.get_session(comment.session_id, user_organization_id, user_workspace_id)
        if comment.author_id != user_id:
            participant = await self.repo.get_participant(session.id, user_id)
            CollaborationPermissionEvaluator.check_action_allowed(participant, "session.edit")

        deleted = await self.comments.soft_delete_comment(comment_id)
        await self.broadcaster.emit_collaboration_event(
            event_type="collaboration.comment.deleted",
            organization_id=session.organization_id,
            workspace_id=session.workspace_id,
            session_id=session.id,
            actor_id=user_id,
            payload={"comment_id": comment_id},
        )
        return deleted

    async def list_assignments(
        self,
        session_id: str,
        user_organization_id: str,
        user_workspace_id: Optional[str] = None,
        status: Optional[str] = None,
        assigned_to: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[CollaborationAssignment]:
        await self.get_session(session_id, user_organization_id, user_workspace_id)
        return await self.assignments.list_assignments(
            session_id=session_id,
            status=status,
            assigned_to=assigned_to,
            limit=limit,
            offset=offset,
        )

    async def update_assignment(
        self,
        assignment_id: str,
        user_id: str,
        user_organization_id: str,
        user_workspace_id: Optional[str] = None,
        status: Optional[str] = None,
        due_at: Optional[datetime] = None,
    ) -> CollaborationAssignment:
        assignment = await self.assignments.get_assignment(assignment_id)
        session = await self.get_session(assignment.session_id, user_organization_id, user_workspace_id)
        updated = await self.assignments.update_assignment(assignment_id, status=status, due_at=due_at)
        await self.broadcaster.emit_collaboration_event(
            event_type="collaboration.assignment.updated",
            organization_id=session.organization_id,
            workspace_id=session.workspace_id,
            session_id=session.id,
            actor_id=user_id,
            payload={"assignment_id": assignment_id, "status": status},
        )
        return updated

    async def list_annotations(
        self,
        session_id: str,
        user_organization_id: str,
        user_workspace_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        annotation_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[CollaborationAnnotation]:
        await self.get_session(session_id, user_organization_id, user_workspace_id)
        return await self.annotations.list_annotations(
            session_id=session_id,
            resource_type=resource_type,
            resource_id=resource_id,
            annotation_type=annotation_type,
            limit=limit,
            offset=offset,
        )

    async def update_annotation(
        self,
        annotation_id: str,
        user_id: str,
        user_organization_id: str,
        user_workspace_id: Optional[str] = None,
        content: Optional[str] = None,
        status: Optional[str] = None,
    ) -> CollaborationAnnotation:
        annotation = await self.annotations.get_annotation(annotation_id)
        session = await self.get_session(annotation.session_id, user_organization_id, user_workspace_id)
        updated = await self.annotations.update_annotation(annotation_id, content=content, status=status)
        await self.broadcaster.emit_collaboration_event(
            event_type="collaboration.annotation.updated",
            organization_id=session.organization_id,
            workspace_id=session.workspace_id,
            session_id=session.id,
            actor_id=user_id,
            payload={"annotation_id": annotation_id},
        )
        return updated

    async def list_decisions(
        self,
        session_id: str,
        user_organization_id: str,
        user_workspace_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[CollaborationDecision]:
        await self.get_session(session_id, user_organization_id, user_workspace_id)
        return await self.sessions.list_decisions(session_id=session_id, limit=limit)

    async def get_state(
        self,
        session_id: str,
        resource_type: str,
        resource_id: str,
        user_organization_id: str,
        user_workspace_id: Optional[str] = None,
    ):
        await self.get_session(session_id, user_organization_id, user_workspace_id)
        return await self.state_mgr.get_state(session_id, resource_type, resource_id)

    async def update_state(
        self,
        session_id: str,
        resource_type: str,
        resource_id: str,
        expected_version: int,
        new_state: Dict[str, Any],
        actor_id: str,
        user_organization_id: str,
        user_workspace_id: Optional[str] = None,
    ):
        session = await self.get_session(session_id, user_organization_id, user_workspace_id)
        participant = await self.repo.get_participant(session_id, actor_id)
        CollaborationPermissionEvaluator.check_action_allowed(participant, "session.edit")

        updated = await self.state_mgr.update_state(
            session_id=session_id,
            resource_type=resource_type,
            resource_id=resource_id,
            expected_version=expected_version,
            new_state=new_state,
            actor_id=actor_id,
        )
        await self.broadcaster.emit_collaboration_event(
            event_type="collaboration.resource.updated",
            organization_id=session.organization_id,
            workspace_id=session.workspace_id,
            session_id=session.id,
            actor_id=actor_id,
            payload={"resource_type": resource_type, "resource_id": resource_id, "version": updated.version},
        )
        return updated

    async def acquire_lock(
        self,
        session_id: str,
        resource_type: str,
        resource_id: str,
        user_id: str,
        user_organization_id: str,
        user_workspace_id: Optional[str] = None,
        ttl_seconds: int = 60,
    ) -> CollaborationLock:
        await self.get_session(session_id, user_organization_id, user_workspace_id)
        participant = await self.repo.get_participant(session_id, user_id)
        CollaborationPermissionEvaluator.check_action_allowed(participant, "session.edit")

        return await self.locking.acquire_lock(
            resource_type=resource_type,
            resource_id=resource_id,
            owner_id=user_id,
            ttl_seconds=ttl_seconds,
        )

    async def release_lock(
        self,
        session_id: str,
        resource_type: str,
        resource_id: str,
        user_id: str,
        user_organization_id: str,
        user_workspace_id: Optional[str] = None,
    ) -> bool:
        await self.get_session(session_id, user_organization_id, user_workspace_id)
        return await self.locking.release_lock(
            resource_type=resource_type,
            resource_id=resource_id,
            owner_id=user_id,
        )

    async def initiate_co_execution(
        self,
        session_id: str,
        user_id: str,
        user_organization_id: str,
        user_workspace_id: Optional[str] = None,
        mode: str = "human_assisted",
        task_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        inputs: Optional[Dict[str, Any]] = None,
        include_comments: bool = True,
        include_annotations: bool = True,
        comment_ids: Optional[List[str]] = None,
    ) -> CoExecutionSession:
        session = await self.get_session(session_id, user_organization_id, user_workspace_id)
        participant = await self.repo.get_participant(session_id, user_id)
        CollaborationPermissionEvaluator.check_action_allowed(participant, "session.execute")

        co_sess = await self.co_execution.initiate_co_execution(
            collaboration_session_id=session_id,
            initiated_by=user_id,
            mode=mode,
            task_id=task_id,
            workflow_id=workflow_id,
            inputs=inputs,
            include_comments=include_comments,
            include_annotations=include_annotations,
            comment_ids=comment_ids,
        )

        await self.activity.log_activity(
            session_id=session.id,
            actor_type="user",
            actor_id=user_id,
            activity_type="started_run",
            resource_type=session.resource_type,
            resource_id=session.resource_id,
            summary=f"Initiated AI co-execution run ({mode}).",
        )

        await self.broadcaster.emit_collaboration_event(
            event_type="collaboration.run.started",
            organization_id=session.organization_id,
            workspace_id=session.workspace_id,
            session_id=session.id,
            actor_id=user_id,
            payload={"run_id": co_sess.id, "mode": mode},
        )
        return co_sess

    async def pause_co_execution(
        self,
        co_session_id: str,
        user_id: str,
        user_organization_id: str,
        user_workspace_id: Optional[str] = None,
    ) -> CoExecutionSession:
        co_sess = await self.repo.get_co_execution(co_session_id)
        if not co_sess:
            from backend.app.services.collaboration.exceptions import CoExecutionError
            raise CoExecutionError(f"CoExecutionSession '{co_session_id}' not found.")

        session = await self.get_session(co_sess.collaboration_session_id, user_organization_id, user_workspace_id)
        participant = await self.repo.get_participant(session.id, user_id)
        CollaborationPermissionEvaluator.check_action_allowed(participant, "session.execute")

        paused = await self.co_execution.pause_execution(co_session_id, user_id)
        await self.broadcaster.emit_collaboration_event(
            event_type="collaboration.run.updated",
            organization_id=session.organization_id,
            workspace_id=session.workspace_id,
            session_id=session.id,
            actor_id=user_id,
            payload={"run_id": co_session_id, "status": "awaiting_input"},
        )
        return paused

    async def resume_co_execution(
        self,
        co_session_id: str,
        user_id: str,
        user_organization_id: str,
        user_workspace_id: Optional[str] = None,
    ) -> CoExecutionSession:
        co_sess = await self.repo.get_co_execution(co_session_id)
        if not co_sess:
            from backend.app.services.collaboration.exceptions import CoExecutionError
            raise CoExecutionError(f"CoExecutionSession '{co_session_id}' not found.")

        session = await self.get_session(co_sess.collaboration_session_id, user_organization_id, user_workspace_id)
        participant = await self.repo.get_participant(session.id, user_id)
        CollaborationPermissionEvaluator.check_action_allowed(participant, "session.execute")

        resumed = await self.co_execution.resume_execution(co_session_id, user_id)
        await self.broadcaster.emit_collaboration_event(
            event_type="collaboration.run.updated",
            organization_id=session.organization_id,
            workspace_id=session.workspace_id,
            session_id=session.id,
            actor_id=user_id,
            payload={"run_id": co_session_id, "status": "executing"},
        )
        return resumed

    async def cancel_co_execution(
        self,
        co_session_id: str,
        user_id: str,
        user_organization_id: str,
        user_workspace_id: Optional[str] = None,
    ) -> CoExecutionSession:
        co_sess = await self.repo.get_co_execution(co_session_id)
        if not co_sess:
            from backend.app.services.collaboration.exceptions import CoExecutionError
            raise CoExecutionError(f"CoExecutionSession '{co_session_id}' not found.")

        session = await self.get_session(co_sess.collaboration_session_id, user_organization_id, user_workspace_id)
        participant = await self.repo.get_participant(session.id, user_id)
        CollaborationPermissionEvaluator.check_action_allowed(participant, "session.execute")

        cancelled = await self.co_execution.cancel_execution(co_session_id, user_id)
        await self.broadcaster.emit_collaboration_event(
            event_type="collaboration.run.failed",
            organization_id=session.organization_id,
            workspace_id=session.workspace_id,
            session_id=session.id,
            actor_id=user_id,
            payload={"run_id": co_session_id, "status": "cancelled"},
        )
        return cancelled

