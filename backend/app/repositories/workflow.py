"""
Workflow repository managing database interactions with strict workspace isolation.
"""
import uuid
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.db.models.workflow import Workflow, WorkflowRun, WorkflowStep, WorkflowVersion
from backend.app.services.workflows.errors import WorkflowNotFoundError


class WorkflowRepository:
    """
    Data access repository for Workflow entities and WorkflowRuns.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_workflow(
        self,
        workspace_id: uuid.UUID,
        name: str,
        slug: str,
        description: Optional[str] = None,
        project_id: Optional[uuid.UUID] = None,
        status: str = "draft",
        version: int = 1,
        input_schema: Optional[Dict[str, Any]] = None,
        output_schema: Optional[Dict[str, Any]] = None,
        configuration: Optional[Dict[str, Any]] = None,
        created_by: Optional[uuid.UUID] = None,
    ) -> Workflow:
        workflow = Workflow(
            workspace_id=workspace_id,
            project_id=project_id,
            name=name,
            slug=slug,
            description=description,
            status=status,
            version=version,
            input_schema=input_schema or {},
            output_schema=output_schema,
            configuration=configuration or {},
            created_by=created_by,
        )
        self.session.add(workflow)
        await self.session.flush()
        await self.session.refresh(workflow)
        return workflow

    async def get_workflow_by_id(
        self,
        workflow_id: uuid.UUID,
        workspace_id: uuid.UUID,
    ) -> Optional[Workflow]:
        stmt = (
            select(Workflow)
            .where(Workflow.id == workflow_id, Workflow.workspace_id == workspace_id)
            .execution_options(populate_existing=True)
            .options(
                selectinload(Workflow.steps),
                selectinload(Workflow.versions),
            )
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def get_workflow_by_id_or_raise(
        self,
        workflow_id: uuid.UUID,
        workspace_id: uuid.UUID,
    ) -> Workflow:
        wf = await self.get_workflow_by_id(workflow_id, workspace_id)
        if not wf:
            raise WorkflowNotFoundError(f"Workflow '{workflow_id}' not found in current workspace.")
        return wf

    async def list_workflows(
        self,
        workspace_id: uuid.UUID,
        project_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[Workflow], int]:
        query = select(Workflow).where(Workflow.workspace_id == workspace_id)
        count_query = select(func.count(Workflow.id)).where(Workflow.workspace_id == workspace_id)

        if project_id:
            query = query.where(Workflow.project_id == project_id)
            count_query = count_query.where(Workflow.project_id == project_id)

        if status:
            query = query.where(Workflow.status == status)
            count_query = count_query.where(Workflow.status == status)

        count_res = await self.session.execute(count_query)
        total = count_res.scalar_one() or 0

        query = (
            query.options(
                selectinload(Workflow.steps),
                selectinload(Workflow.runs),
            )
            .order_by(desc(Workflow.updated_at))
            .limit(limit)
            .offset(offset)
        )
        res = await self.session.execute(query)
        workflows = list(res.scalars().all())
        return workflows, total

    async def update_workflow(self, workflow: Workflow) -> Workflow:
        self.session.add(workflow)
        await self.session.flush()
        await self.session.refresh(workflow)
        return workflow

    async def delete_workflow(self, workflow: Workflow) -> None:
        await self.session.delete(workflow)
        await self.session.flush()

    async def replace_steps(
        self,
        workflow_id: uuid.UUID,
        step_definitions: List[Dict[str, Any]],
    ) -> List[WorkflowStep]:
        # Remove existing steps
        existing_stmt = select(WorkflowStep).where(WorkflowStep.workflow_id == workflow_id)
        existing_res = await self.session.execute(existing_stmt)
        for s in existing_res.scalars().all():
            await self.session.delete(s)
        await self.session.flush()

        # Add new steps in order
        new_steps: List[WorkflowStep] = []
        for order, step_def in enumerate(step_definitions, start=1):
            st = WorkflowStep(
                workflow_id=workflow_id,
                step_order=order,
                name=step_def.get("name", f"Step {order}"),
                description=step_def.get("description"),
                step_type=step_def.get("type", "generate") if isinstance(step_def.get("type"), str) else step_def.get("type").value,
                configuration=step_def.get("config", {}),
                enabled=step_def.get("enabled", True),
            )
            self.session.add(st)
            new_steps.append(st)

        await self.session.flush()
        self.session.expire_all()
        return new_steps

    async def create_version_snapshot(
        self,
        workflow_id: uuid.UUID,
        version: int,
        definition: Dict[str, Any],
        created_by: Optional[uuid.UUID] = None,
    ) -> WorkflowVersion:
        wv = WorkflowVersion(
            workflow_id=workflow_id,
            version=version,
            definition=definition,
            created_by=created_by,
        )
        self.session.add(wv)
        await self.session.flush()
        await self.session.refresh(wv)
        return wv

    async def get_version(
        self,
        workflow_id: uuid.UUID,
        version: int,
    ) -> Optional[WorkflowVersion]:
        stmt = select(WorkflowVersion).where(
            WorkflowVersion.workflow_id == workflow_id,
            WorkflowVersion.version == version,
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def create_run(
        self,
        workflow_id: uuid.UUID,
        workflow_version: int,
        workspace_id: uuid.UUID,
        project_id: Optional[uuid.UUID] = None,
        input_data: Optional[Dict[str, Any]] = None,
    ) -> WorkflowRun:
        run = WorkflowRun(
            workflow_id=workflow_id,
            workflow_version=workflow_version,
            workspace_id=workspace_id,
            project_id=project_id,
            status="pending",
            input_data=input_data or {},
            execution_state={},
        )
        self.session.add(run)
        await self.session.flush()
        await self.session.refresh(run)
        return run

    async def get_run_by_id(
        self,
        run_id: uuid.UUID,
        workspace_id: uuid.UUID,
    ) -> Optional[WorkflowRun]:
        stmt = (
            select(WorkflowRun)
            .where(WorkflowRun.id == run_id, WorkflowRun.workspace_id == workspace_id)
            .options(selectinload(WorkflowRun.workflow))
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def list_runs(
        self,
        workspace_id: uuid.UUID,
        workflow_id: Optional[uuid.UUID] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[WorkflowRun], int]:
        query = select(WorkflowRun).where(WorkflowRun.workspace_id == workspace_id)
        count_query = select(func.count(WorkflowRun.id)).where(WorkflowRun.workspace_id == workspace_id)

        if workflow_id:
            query = query.where(WorkflowRun.workflow_id == workflow_id)
            count_query = count_query.where(WorkflowRun.workflow_id == workflow_id)

        count_res = await self.session.execute(count_query)
        total = count_res.scalar_one() or 0

        query = (
            query.options(selectinload(WorkflowRun.workflow))
            .order_by(desc(WorkflowRun.created_at))
            .limit(limit)
            .offset(offset)
        )
        res = await self.session.execute(query)
        runs = list(res.scalars().all())
        return runs, total
