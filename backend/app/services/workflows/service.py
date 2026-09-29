"""
High-level Workflow service managing workflow CRUD, versioning, publishing, template installation, and run orchestration.
"""
import re
import uuid
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.models.user import User
from backend.app.db.models.workflow import Workflow, WorkflowRun, WorkflowStep, WorkflowVersion
from backend.app.repositories.workflow import WorkflowRepository
from backend.app.services.llm.factory import LLMProviderFactory
from backend.app.services.workflows.errors import (
    WorkflowNotFoundError,
    WorkflowValidationError,
    WorkflowVersionError,
)
from backend.app.services.workflows.executor import WorkflowExecutor
from backend.app.services.workflows.schemas import (
    StepType,
    WorkflowCreateRequest,
    WorkflowDefinition,
    WorkflowDefinitionUpdateRequest,
    WorkflowListResponse,
    WorkflowResponse,
    WorkflowRunListResponse,
    WorkflowRunRequest,
    WorkflowRunResponse,
    WorkflowStatus,
    WorkflowStepDefinition,
    WorkflowStepResponse,
    WorkflowStepRunResult,
    WorkflowTemplateResponse,
    WorkflowUpdateRequest,
    WorkflowValidationResponse,
)
from backend.app.services.workflows.templates import WorkflowTemplateRegistry
from backend.app.services.workflows.validator import WorkflowValidator


class WorkflowService:
    """
    Core business service for managing and executing AI Workflows.
    """

    def __init__(self, session: AsyncSession, llm_factory: Optional[LLMProviderFactory] = None):
        self.session = session
        self.repo = WorkflowRepository(session)
        self.executor = WorkflowExecutor(session, llm_factory=llm_factory)

    async def create_workflow(
        self,
        workspace_id: uuid.UUID,
        request: WorkflowCreateRequest,
        user: User,
    ) -> WorkflowResponse:
        slug = request.slug or self._slugify(request.name)

        workflow = await self.repo.create_workflow(
            workspace_id=workspace_id,
            name=request.name,
            slug=slug,
            description=request.description,
            project_id=request.project_id,
            status=WorkflowStatus.DRAFT.value,
            version=1,
            input_schema=request.input_schema or {},
            output_schema=request.output_schema,
            configuration=request.configuration or {},
            created_by=user.id,
        )

        wf_id = workflow.id
        if request.steps:
            step_dicts = [s.model_dump(mode="json") for s in request.steps]
            await self.repo.replace_steps(wf_id, step_dicts)

        await self.session.commit()
        return await self.get_workflow(wf_id, workspace_id)

    async def get_workflow(
        self,
        workflow_id: uuid.UUID,
        workspace_id: uuid.UUID,
    ) -> WorkflowResponse:
        wf = await self.repo.get_workflow_by_id_or_raise(workflow_id, workspace_id)
        runs_list, total_runs = await self.repo.list_runs(workspace_id, workflow_id=workflow_id, limit=1)
        latest_status = runs_list[0].status if runs_list else None

        resp = WorkflowResponse.model_validate(wf)
        resp.runs_count = total_runs
        resp.latest_run_status = latest_status
        return resp

    async def list_workflows(
        self,
        workspace_id: uuid.UUID,
        project_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> WorkflowListResponse:
        workflows, total = await self.repo.list_workflows(
            workspace_id=workspace_id,
            project_id=project_id,
            status=status,
            limit=limit,
            offset=offset,
        )

        res_items: List[WorkflowResponse] = []
        for wf in workflows:
            res_items.append(WorkflowResponse.model_validate(wf))

        return WorkflowListResponse(workflows=res_items, total=total)

    async def update_workflow(
        self,
        workflow_id: uuid.UUID,
        workspace_id: uuid.UUID,
        request: WorkflowUpdateRequest,
        user: User,
    ) -> WorkflowResponse:
        wf = await self.repo.get_workflow_by_id_or_raise(workflow_id, workspace_id)
        wf_id = wf.id

        if request.name is not None:
            wf.name = request.name
        if request.description is not None:
            wf.description = request.description
        if request.project_id is not None:
            wf.project_id = request.project_id
        if request.input_schema is not None:
            wf.input_schema = request.input_schema
        if request.output_schema is not None:
            wf.output_schema = request.output_schema
        if request.configuration is not None:
            wf.configuration = request.configuration
        if request.status is not None:
            wf.status = request.status.value

        await self.repo.update_workflow(wf)
        await self.session.commit()
        return await self.get_workflow(wf_id, workspace_id)

    async def delete_workflow(
        self,
        workflow_id: uuid.UUID,
        workspace_id: uuid.UUID,
    ) -> None:
        wf = await self.repo.get_workflow_by_id_or_raise(workflow_id, workspace_id)
        await self.repo.delete_workflow(wf)
        await self.session.commit()

    async def get_workflow_definition(
        self,
        workflow_id: uuid.UUID,
        workspace_id: uuid.UUID,
    ) -> WorkflowDefinition:
        wf = await self.repo.get_workflow_by_id_or_raise(workflow_id, workspace_id)
        steps_def: List[WorkflowStepDefinition] = []

        for st in wf.steps:
            steps_def.append(
                WorkflowStepDefinition(
                    id=st.name.lower().replace(" ", "_"),
                    name=st.name,
                    type=StepType(st.step_type),
                    description=st.description,
                    config=st.configuration or {},
                    enabled=st.enabled,
                )
            )

        return WorkflowDefinition(
            name=wf.name,
            description=wf.description,
            version=wf.version,
            input_schema=wf.input_schema or {},
            output_schema=wf.output_schema,
            configuration=wf.configuration or {},
            steps=steps_def,
        )

    async def update_workflow_definition(
        self,
        workflow_id: uuid.UUID,
        workspace_id: uuid.UUID,
        request: WorkflowDefinitionUpdateRequest,
        user: User,
    ) -> WorkflowResponse:
        wf = await self.repo.get_workflow_by_id_or_raise(workflow_id, workspace_id)
        wf_id = wf.id

        # If already published, bump version and revert status to draft
        if wf.status == WorkflowStatus.PUBLISHED.value:
            wf.version += 1
            wf.status = WorkflowStatus.DRAFT.value

        if request.input_schema is not None:
            wf.input_schema = request.input_schema
        if request.output_schema is not None:
            wf.output_schema = request.output_schema
        if request.configuration is not None:
            wf.configuration = request.configuration

        step_dicts = [s.model_dump(mode="json") for s in request.steps]
        await self.repo.replace_steps(wf_id, step_dicts)
        await self.repo.update_workflow(wf)
        await self.session.commit()

        return await self.get_workflow(wf_id, workspace_id)

    async def validate_workflow(
        self,
        workflow_id: uuid.UUID,
        workspace_id: uuid.UUID,
    ) -> WorkflowValidationResponse:
        definition = await self.get_workflow_definition(workflow_id, workspace_id)
        return WorkflowValidator.validate_workflow_definition(definition)

    async def publish_workflow(
        self,
        workflow_id: uuid.UUID,
        workspace_id: uuid.UUID,
        user: User,
    ) -> WorkflowResponse:
        wf = await self.repo.get_workflow_by_id_or_raise(workflow_id, workspace_id)
        wf_id = wf.id
        definition = await self.get_workflow_definition(wf_id, workspace_id)

        # Strict validation before publishing
        val_res = WorkflowValidator.validate_workflow_definition(definition)
        if not val_res.valid:
            error_msgs = [f"{iss.step_id or 'Workflow'}: {iss.message}" for iss in val_res.issues if iss.level == "error"]
            raise WorkflowValidationError(f"Cannot publish invalid workflow: {'; '.join(error_msgs)}")

        # Create immutable snapshot in WorkflowVersion
        await self.repo.create_version_snapshot(
            workflow_id=wf_id,
            version=wf.version,
            definition=definition.model_dump(mode="json"),
            created_by=user.id,
        )

        wf.status = WorkflowStatus.PUBLISHED.value
        await self.repo.update_workflow(wf)
        await self.session.commit()

        return await self.get_workflow(wf_id, workspace_id)

    async def duplicate_workflow(
        self,
        workflow_id: uuid.UUID,
        workspace_id: uuid.UUID,
        user: User,
    ) -> WorkflowResponse:
        original = await self.repo.get_workflow_by_id_or_raise(workflow_id, workspace_id)
        definition = await self.get_workflow_definition(workflow_id, workspace_id)

        new_name = f"{original.name} (Copy)"
        new_slug = self._slugify(f"{original.slug}-copy-{uuid.uuid4().hex[:4]}")

        dup = await self.repo.create_workflow(
            workspace_id=workspace_id,
            name=new_name,
            slug=new_slug,
            description=original.description,
            project_id=original.project_id,
            status=WorkflowStatus.DRAFT.value,
            version=1,
            input_schema=original.input_schema,
            output_schema=original.output_schema,
            configuration=original.configuration,
            created_by=user.id,
        )
        dup_id = dup.id

        step_dicts = [s.model_dump(mode="json") for s in definition.steps]
        await self.repo.replace_steps(dup_id, step_dicts)
        await self.session.commit()

        return await self.get_workflow(dup_id, workspace_id)

    async def install_template(
        self,
        template_id: str,
        workspace_id: uuid.UUID,
        user: User,
        project_id: Optional[uuid.UUID] = None,
    ) -> WorkflowResponse:
        tpl = WorkflowTemplateRegistry.get_template_by_id(template_id)
        if not tpl:
            raise WorkflowNotFoundError(f"Workflow template '{template_id}' not found.")

        definition = tpl.definition
        slug = self._slugify(f"{tpl.name}-{uuid.uuid4().hex[:6]}")

        wf = await self.repo.create_workflow(
            workspace_id=workspace_id,
            name=tpl.name,
            slug=slug,
            description=tpl.description,
            project_id=project_id,
            status=WorkflowStatus.DRAFT.value,
            version=1,
            input_schema=definition.input_schema,
            output_schema=definition.output_schema,
            configuration=definition.configuration,
            created_by=user.id,
        )
        wf_id = wf.id

        step_dicts = [s.model_dump(mode="json") for s in definition.steps]
        await self.repo.replace_steps(wf_id, step_dicts)
        await self.session.commit()

        return await self.get_workflow(wf_id, workspace_id)

    async def run_workflow(
        self,
        workflow_id: uuid.UUID,
        workspace_id: uuid.UUID,
        user: User,
        request: WorkflowRunRequest,
    ) -> WorkflowRunResponse:
        wf = await self.repo.get_workflow_by_id_or_raise(workflow_id, workspace_id)

        # 1. Validate runtime input
        validated_input = WorkflowValidator.validate_runtime_input(
            input_schema=wf.input_schema or {},
            runtime_input=request.input_data or {},
        )

        # 2. Resolve definition (from immutable version snapshot or current entity)
        target_version = request.version or wf.version
        version_snapshot = await self.repo.get_version(wf.id, target_version)

        if version_snapshot:
            definition = WorkflowDefinition.model_validate(version_snapshot.definition)
        else:
            definition = await self.get_workflow_definition(wf.id, workspace_id)

        # 3. Create initial pending WorkflowRun
        run = await self.repo.create_run(
            workflow_id=wf.id,
            workflow_version=target_version,
            workspace_id=workspace_id,
            project_id=request.project_id or wf.project_id,
            input_data=validated_input,
        )

        # 4. Execute Workflow
        run = await self.executor.execute_workflow(
            workflow=wf,
            run=run,
            definition=definition,
            user=user,
            input_data=validated_input,
        )

        return self._format_run_response(run, workflow_name=wf.name)

    async def get_workflow_run(
        self,
        run_id: uuid.UUID,
        workspace_id: uuid.UUID,
    ) -> WorkflowRunResponse:
        run = await self.repo.get_run_by_id(run_id, workspace_id)
        if not run:
            raise WorkflowNotFoundError(f"Workflow run '{run_id}' not found in workspace.")
        wf_name = run.workflow.name if run.workflow else None
        return self._format_run_response(run, workflow_name=wf_name)

    async def list_workflow_runs(
        self,
        workspace_id: uuid.UUID,
        workflow_id: Optional[uuid.UUID] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> WorkflowRunListResponse:
        runs, total = await self.repo.list_runs(
            workspace_id=workspace_id,
            workflow_id=workflow_id,
            limit=limit,
            offset=offset,
        )

        formatted = [self._format_run_response(r, workflow_name=r.workflow.name if r.workflow else None) for r in runs]
        return WorkflowRunListResponse(runs=formatted, total=total)

    def _format_run_response(self, run: WorkflowRun, workflow_name: Optional[str] = None) -> WorkflowRunResponse:
        step_results: List[WorkflowStepRunResult] = []
        exec_state = run.execution_state or {}
        raw_results = exec_state.get("step_outputs", {})

        for s_id, out_data in raw_results.items():
            step_results.append(
                WorkflowStepRunResult(
                    step_id=s_id,
                    step_name=s_id.replace("_", " ").title(),
                    step_type="generate",
                    status="completed",
                    output_summary=str(out_data)[:150],
                    output_data=out_data,
                )
            )

        resp = WorkflowRunResponse.model_validate(run)
        resp.workflow_name = workflow_name
        if step_results and not resp.step_results:
            resp.step_results = step_results
        return resp

    def _slugify(self, text: str) -> str:
        slug = re.sub(r"[^\w\s-]", "", text.lower()).strip()
        return re.sub(r"[-\s]+", "-", slug)
