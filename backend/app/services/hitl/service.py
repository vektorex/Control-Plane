"""
Main Human-in-the-Loop (HITL) Service coordinating requests, decisions, policies, and execution resumption (Step 18).
"""
from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID
from sqlalchemy import select, and_, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.db.models.hitl import (
    ApprovalDecision,
    HumanAction,
    HumanInterventionRequest,
    WorkspaceApprovalPolicy,
)
from backend.app.db.models.user import User
from backend.app.db.models.workflow import WorkflowRun
from backend.app.services.hitl.approvals import ApprovalDecisionProcessor
from backend.app.services.hitl.errors import (
    HITLNotFoundError,
    HITLPermissionError,
    HITLStatusError,
)
from backend.app.services.hitl.executor import HITLExecutionCoordinator
from backend.app.services.hitl.requests import InterventionRequestManager
from backend.app.services.hitl.schemas import (
    ApprovalActionRequest,
    ApprovalDecisionType,
    InterventionAssignRequest,
    InterventionCreateRequest,
    InterventionStatus,
    WorkspaceApprovalPolicyUpdate,
)

logger = logging.getLogger(__name__)


class HITLService:
    """
    Core service managing human intervention requests, approval lifecycles, and policy evaluation.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    # =========================================================================
    # 1. Intervention Request Queries
    # =========================================================================

    async def list_requests(
        self,
        workspace_id: UUID,
        status: Optional[str] = None,
        assigned_to: Optional[UUID] = None,
        project_id: Optional[UUID] = None,
        priority: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[HumanInterventionRequest]:
        """
        Lists intervention requests within a workspace with optional filters.
        """
        now = datetime.now(timezone.utc)
        filters = [HumanInterventionRequest.workspace_id == workspace_id]

        if status:
            filters.append(HumanInterventionRequest.status == status)
        if assigned_to:
            filters.append(HumanInterventionRequest.assigned_to == assigned_to)
        if project_id:
            filters.append(HumanInterventionRequest.project_id == project_id)
        if priority:
            filters.append(HumanInterventionRequest.priority == priority)

        stmt = (
            select(HumanInterventionRequest)
            .options(
                selectinload(HumanInterventionRequest.decisions),
                selectinload(HumanInterventionRequest.assigned_user),
                selectinload(HumanInterventionRequest.requester_user),
            )
            .where(and_(*filters))
            .order_by(HumanInterventionRequest.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        res = await self.session.execute(stmt)
        requests = list(res.scalars().all())

        # Auto-expire any pending requests that passed expires_at
        expired_count = 0
        for req in requests:
            exp = req.expires_at
            if exp and exp.tzinfo is None:
                exp = exp.replace(tzinfo=timezone.utc)
            if req.status == InterventionStatus.PENDING.value and exp and now > exp:
                req.status = InterventionStatus.EXPIRED.value
                req.resolved_at = now
                expired_count += 1
        if expired_count > 0:
            await self.session.commit()

        return requests

    async def get_request(
        self,
        request_id: UUID,
        workspace_id: UUID,
    ) -> HumanInterventionRequest:
        """
        Retrieves a single intervention request with full context and decision history.
        """
        now = datetime.now(timezone.utc)
        stmt = (
            select(HumanInterventionRequest)
            .options(
                selectinload(HumanInterventionRequest.decisions),
                selectinload(HumanInterventionRequest.assigned_user),
                selectinload(HumanInterventionRequest.requester_user),
                selectinload(HumanInterventionRequest.workflow),
            )
            .where(
                and_(
                    HumanInterventionRequest.id == request_id,
                    HumanInterventionRequest.workspace_id == workspace_id,
                )
            )
        )
        res = await self.session.execute(stmt)
        req = res.scalars().first()
        if not req:
            raise HITLNotFoundError(str(request_id))

        # Check and handle expiration
        exp = req.expires_at
        if exp and exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        if req.status == InterventionStatus.PENDING.value and exp and now > exp:
            req.status = InterventionStatus.EXPIRED.value
            req.resolved_at = now
            await self.session.commit()

        return req

    # =========================================================================
    # 2. Decision Actions (Approve, Reject, Edit, Cancel, Assign)
    # =========================================================================

    async def approve_request(
        self,
        request_id: UUID,
        workspace_id: UUID,
        user: User,
        request_body: Optional[ApprovalActionRequest] = None,
    ) -> HumanInterventionRequest:
        """
        Approve an intervention request and automatically resume any paused workflow.
        """
        comment = request_body.comment if request_body else None
        intervention = await ApprovalDecisionProcessor.process_decision(
            session=self.session,
            intervention_id=request_id,
            workspace_id=workspace_id,
            user=user,
            decision=ApprovalDecisionType.APPROVE,
            comment=comment,
        )

        # If linked to a waiting workflow run, resume it
        if intervention.workflow_run_id:
            await HITLExecutionCoordinator.resume_workflow(
                session=self.session,
                workflow_run_id=intervention.workflow_run_id,
                workspace_id=workspace_id,
                user=user,
                intervention=intervention,
            )

        return await self.get_request(request_id, workspace_id)

    async def reject_request(
        self,
        request_id: UUID,
        workspace_id: UUID,
        user: User,
        request_body: Optional[ApprovalActionRequest] = None,
    ) -> HumanInterventionRequest:
        """
        Reject an intervention request and halt any paused workflow.
        """
        comment = request_body.comment if request_body else None
        intervention = await ApprovalDecisionProcessor.process_decision(
            session=self.session,
            intervention_id=request_id,
            workspace_id=workspace_id,
            user=user,
            decision=ApprovalDecisionType.REJECT,
            comment=comment,
        )

        if intervention.workflow_run_id:
            await HITLExecutionCoordinator.resume_workflow(
                session=self.session,
                workflow_run_id=intervention.workflow_run_id,
                workspace_id=workspace_id,
                user=user,
                intervention=intervention,
            )

        return await self.get_request(request_id, workspace_id)

    async def edit_request(
        self,
        request_id: UUID,
        workspace_id: UUID,
        user: User,
        request_body: ApprovalActionRequest,
    ) -> HumanInterventionRequest:
        """
        Edit the action input and approve execution with the edited payload.
        """
        intervention = await ApprovalDecisionProcessor.process_decision(
            session=self.session,
            intervention_id=request_id,
            workspace_id=workspace_id,
            user=user,
            decision=ApprovalDecisionType.EDIT,
            comment=request_body.comment,
            edited_data=request_body.edited_data,
        )

        if intervention.workflow_run_id:
            await HITLExecutionCoordinator.resume_workflow(
                session=self.session,
                workflow_run_id=intervention.workflow_run_id,
                workspace_id=workspace_id,
                user=user,
                intervention=intervention,
            )

        return await self.get_request(request_id, workspace_id)

    async def cancel_request(
        self,
        request_id: UUID,
        workspace_id: UUID,
        user: User,
        request_body: Optional[ApprovalActionRequest] = None,
    ) -> HumanInterventionRequest:
        """
        Cancel an intervention request.
        """
        comment = request_body.comment if request_body else None
        intervention = await ApprovalDecisionProcessor.process_decision(
            session=self.session,
            intervention_id=request_id,
            workspace_id=workspace_id,
            user=user,
            decision=ApprovalDecisionType.CANCEL,
            comment=comment,
        )

        if intervention.workflow_run_id:
            await HITLExecutionCoordinator.resume_workflow(
                session=self.session,
                workflow_run_id=intervention.workflow_run_id,
                workspace_id=workspace_id,
                user=user,
                intervention=intervention,
            )

        return await self.get_request(request_id, workspace_id)

    async def assign_request(
        self,
        request_id: UUID,
        workspace_id: UUID,
        user: User,
        assigned_to: UUID,
    ) -> HumanInterventionRequest:
        """
        Assign an intervention request to a specific user.
        """
        await ApprovalDecisionProcessor.assign_request(
            session=self.session,
            intervention_id=request_id,
            workspace_id=workspace_id,
            user=user,
            assigned_to=assigned_to,
        )
        return await self.get_request(request_id, workspace_id)

    # =========================================================================
    # 3. Workspace Approval Policy
    # =========================================================================

    async def get_or_create_policy(
        self,
        workspace_id: UUID,
    ) -> WorkspaceApprovalPolicy:
        """
        Retrieves or initializes the workspace approval policy.
        """
        stmt = select(WorkspaceApprovalPolicy).where(WorkspaceApprovalPolicy.workspace_id == workspace_id)
        res = await self.session.execute(stmt)
        policy = res.scalars().first()
        if not policy:
            policy = WorkspaceApprovalPolicy(
                workspace_id=workspace_id,
                require_tool_approval=False,
                require_connector_write_approval=True,
                require_destructive_approval=True,
                require_external_action_approval=True,
                require_evaluation_failure_review=False,
                created_at=datetime.now(timezone.utc),
            )
            self.session.add(policy)
            await self.session.commit()
            await self.session.refresh(policy)
        return policy

    async def update_policy(
        self,
        workspace_id: UUID,
        update_data: WorkspaceApprovalPolicyUpdate,
    ) -> WorkspaceApprovalPolicy:
        """
        Updates workspace approval policy preferences.
        Note: require_destructive_approval cannot be disabled.
        """
        policy = await self.get_or_create_policy(workspace_id)

        if update_data.require_tool_approval is not None:
            policy.require_tool_approval = update_data.require_tool_approval
        if update_data.require_connector_write_approval is not None:
            policy.require_connector_write_approval = update_data.require_connector_write_approval
        if update_data.require_external_action_approval is not None:
            policy.require_external_action_approval = update_data.require_external_action_approval
        if update_data.require_evaluation_failure_review is not None:
            policy.require_evaluation_failure_review = update_data.require_evaluation_failure_review
        if update_data.max_auto_cost is not None:
            policy.max_auto_cost = update_data.max_auto_cost

        # Mandatory invariant: destructive operations strictly remain True
        policy.require_destructive_approval = True
        policy.updated_at = datetime.now(timezone.utc)

        await self.session.commit()
        await self.session.refresh(policy)
        return policy
