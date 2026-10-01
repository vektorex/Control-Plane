import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.db.models.run import Run
from backend.app.db.models.task import Task
from backend.app.db.models.project import Project
from backend.app.db.models.user import User
from backend.app.services.replay.schemas import ReplayEligibility
from backend.app.services.tools.registry import get_tool_registry
from backend.app.services.ai_gateway.providers import default_provider_registry

# Operations recognized as potential external side effects
WRITE_OPERATIONS = {
    "send",
    "create",
    "update",
    "delete",
    "write",
    "mutate",
    "post",
    "patch",
    "publish",
    "execute",
    "trigger",
}

# External tools that perform mutating side effects
MUTATING_TOOLS = {
    "github_create_issue",
    "github_update_issue",
    "github_create_pull_request",
    "slack_send_message",
    "email_send",
    "database_write",
    "file_write",
    "memory_create",
    "memory_update",
    "memory_delete",
}


class ReplayPolicy:
    """
    Enforces replay safety invariants:
    - Replay defaults to safe DRY-RUN mode.
    - All external side effects default to disabled.
    - Destructive or write actions strictly require fresh HITL approval.
    - Historical approvals are never reused.
    - Workspace isolation is enforced.
    """

    @staticmethod
    def is_side_effect_operation(operation: str, tool_name: Optional[str] = None) -> bool:
        """Determines if a requested tool or operation causes external side effects."""
        if tool_name and tool_name.lower() in MUTATING_TOOLS:
            return True
        op_lower = operation.lower()
        return any(w in op_lower for w in WRITE_OPERATIONS)

    @staticmethod
    def should_block_side_effect(
        operation: str,
        tool_name: Optional[str] = None,
        dry_run: bool = True,
        has_fresh_approval: bool = False,
    ) -> bool:
        """
        Determines whether an operation must be intercepted and simulated.
        If dry_run is True, ALL side effects are blocked.
        If dry_run is False, side effects are only allowed if a FRESH HITL approval was explicitly obtained.
        """
        if not ReplayPolicy.is_side_effect_operation(operation, tool_name):
            return False

        # In dry run, always block
        if dry_run:
            return True

        # In live replay, block if no fresh approval
        return not has_fresh_approval

    @staticmethod
    def format_dry_run_simulation(operation: str, tool_name: Optional[str] = None, inputs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Produces a safe, simulated dry-run result without executing external mutations."""
        target = tool_name or operation
        return {
            "status": "simulated",
            "dry_run": True,
            "message": f"Would execute {target}",
            "simulated_operation": operation,
            "simulated_inputs": inputs or {},
            "side_effect_blocked": True,
            "fresh_approval_required": True,
            "simulation_notice": "External side effects are disabled by default during replay.",
        }


class ReplayEligibilityChecker:
    """
    Verifies that a historical execution has all required entities, permissions,
    models, and registered tools to be safely replayed.
    """

    @staticmethod
    async def check_run_eligibility(
        run: Run,
        session: AsyncSession,
        workspace_id: Optional[uuid.UUID] = None,
        user: Optional[User] = None,
    ) -> ReplayEligibility:
        """Evaluates whether a Run is eligible for replay."""
        warnings: List[str] = []

        # 1. Verify Task exists and resolves workspace boundary
        task_obj = run.task
        if task_obj is None:
            task_res = await session.execute(select(Task).where(Task.id == run.task_id))
            task_obj = task_res.scalar_one_or_none()

        if not task_obj:
            return ReplayEligibility(
                eligible=False,
                warnings=["The original task associated with this run has been deleted."],
            )

        # 2. Verify workspace isolation if workspace_id provided
        target_ws = workspace_id or getattr(run, "workspace_id", None)
        if target_ws and task_obj.project_id:
            proj_res = await session.execute(select(Project).where(Project.id == task_obj.project_id))
            proj = proj_res.scalar_one_or_none()
            if proj and str(proj.workspace_id) != str(target_ws):
                return ReplayEligibility(
                    eligible=False,
                    warnings=["Access denied: Run does not belong to the active workspace."],
                )

        # 3. Verify model availability
        target_model = run.model_name or run.final_model
        if target_model:
            model_found = False
            try:
                for prov in default_provider_registry.list():
                    for m in prov.get("models", []):
                        if m.get("model_id") == target_model:
                            model_found = True
                            break
                    if model_found:
                        break
            except Exception:
                model_found = True

            if not model_found:
                warnings.append(
                    f"The original model '{target_model}' is not registered with active providers. Replay will use fallback."
                )

        # 4. Verify tools availability
        if run.tools_used:
            registry = get_tool_registry()
            for t_name in run.tools_used:
                if not registry.has_tool(t_name):
                    warnings.append(f"Tool '{t_name}' used in original execution is no longer registered.")

        # 5. Verify snapshot viability
        if not run.input_snapshot and not task_obj.instructions and not task_obj.description:
            return ReplayEligibility(
                eligible=False,
                warnings=["Original run lacks sufficient input snapshot or task instructions to reproduce."],
            )

        return ReplayEligibility(
            eligible=True,
            warnings=warnings,
        )

    @staticmethod
    async def check_workflow_run_eligibility(
        workflow_run: Any,
        session: AsyncSession,
        workspace_id: Optional[uuid.UUID] = None,
        user: Optional[User] = None,
    ) -> ReplayEligibility:
        """Evaluates whether a WorkflowRun is eligible for replay."""
        warnings: List[str] = []

        if not workflow_run:
            return ReplayEligibility(
                eligible=False,
                warnings=["The specified workflow run does not exist."],
            )

        target_ws = workspace_id or getattr(workflow_run, "workspace_id", None)
        if target_ws and str(workflow_run.workspace_id) != str(target_ws):
            return ReplayEligibility(
                eligible=False,
                warnings=["Access denied: Workflow run does not belong to the active workspace."],
            )

        if not getattr(workflow_run, "workflow", None) and getattr(workflow_run, "workflow_id", None):
            from backend.app.db.models.workflow import Workflow
            wf_res = await session.execute(select(Workflow).where(Workflow.id == workflow_run.workflow_id))
            if not wf_res.scalar_one_or_none():
                return ReplayEligibility(
                    eligible=False,
                    warnings=["The original workflow definition has been deleted."],
                )

        return ReplayEligibility(
            eligible=True,
            warnings=warnings,
        )

