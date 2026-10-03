import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.db.models.run import Run
from backend.app.db.models.task import Task
from backend.app.db.models.project import Project
from backend.app.db.models.workflow import WorkflowRun, Workflow
from backend.app.services.replay.schemas import ExecutionSnapshot
from backend.app.services.replay.sanitizer import sanitize_replay_snapshot
from backend.app.services.replay.errors import ReplayNotFoundError


class ReplaySnapshotService:
    """
    Creates deterministic, clean, sanitized execution snapshots from historical
    Runs and WorkflowRuns for safe replay and debugging.
    """

    @classmethod
    async def create_snapshot_from_run(cls, run: Run, session: AsyncSession) -> ExecutionSnapshot:
        """Constructs an ExecutionSnapshot from a single task Run."""
        # Load task and project to resolve workspace_id
        task_obj: Optional[Task] = run.task
        if task_obj is None:
            task_res = await session.execute(select(Task).where(Task.id == run.task_id))
            task_obj = task_res.scalar_one_or_none()

        if task_obj is None:
            raise ReplayNotFoundError(f"Associated Task {run.task_id} not found for run {run.id}")

        project_id = str(task_obj.project_id) if task_obj.project_id else None
        workspace_id = getattr(task_obj, "workspace_id", None)
        if not workspace_id and task_obj.project_id:
            proj_res = await session.execute(select(Project).where(Project.id == task_obj.project_id))
            proj = proj_res.scalar_one_or_none()
            if proj:
                workspace_id = str(proj.workspace_id)

        input_snap = run.input_snapshot or {}

        # Safe Task configuration
        task_config = {
            "title": task_obj.title,
            "instructions": task_obj.instructions or task_obj.description or "",
            "context_text": task_obj.context_text,
            "status": task_obj.status,
            "model_mode": getattr(task_obj, "model_mode", None),
            "preferred_model": getattr(task_obj, "preferred_model", None),
        }

        # Safe Model configuration
        model_config = {
            "model_name": run.model_name or run.final_model,
            "model_provider": run.model_provider,
            "routing_policy": run.model_routing_policy,
            "selection_reason": run.model_selection_reason,
            "fallback_attempts": run.fallback_attempts,
            "temperature": input_snap.get("temperature", 0.2),
        }

        # Safe Retrieval configuration
        retrieval_config = {
            "retrieval_enabled": run.retrieval_enabled,
            "retrieval_mode": run.retrieval_mode,
            "retrieval_strategy": run.retrieval_strategy,
            "retrieval_scope": run.retrieval_scope,
            "retrieval_top_k": run.retrieval_top_k,
            "retrieval_confidence": run.retrieval_confidence,
            "retrieval_reason": run.retrieval_reason,
            "sources": [
                {
                    "title": s.get("title"),
                    "source_type": s.get("source_type"),
                    "id": s.get("id"),
                    "score": s.get("score"),
                }
                for s in (run.retrieval_sources or [])
                if isinstance(s, dict)
            ],
        }

        # Safe Tool configuration
        tool_config = {
            "tools_used": run.tools_used or [],
            "tool_call_count": run.tool_call_count or 0,
            "tool_executions": [
                {
                    "tool": t.get("tool") or t.get("tool_name"),
                    "status": t.get("status"),
                    "duration_ms": t.get("duration_ms"),
                }
                for t in (run.tool_executions or [])
                if isinstance(t, dict)
            ],
        }

        # Safe Connector configuration
        connector_config = {
            "connectors": input_snap.get("connectors", []),
            "has_external_connector": bool(input_snap.get("connectors")),
        }

        # Safe Memory configuration
        memory_config = {
            "memory_mode": input_snap.get("memory_mode", "auto"),
            "memory_results_count": input_snap.get("memory_results_count", 0),
        }

        # Safe Evaluation configuration
        evaluation_config = {
            "evaluation_mode": run.evaluation_mode or getattr(task_obj, "evaluation_mode", "standard"),
            "evaluation_status": run.evaluation_status,
            "evaluation_attempts": run.evaluation_attempts,
            "revision_attempts": run.revision_attempts,
            "evaluation_result": run.evaluation_result,
        }

        # Safe Context metadata
        context_metadata = {
            "context_item_count": run.context_item_count,
            "estimated_context_tokens": run.estimated_context_tokens,
            "context_truncated": run.context_truncated,
            "context_sources": run.context_sources,
        }

        # Safe Trace metadata
        trace_meta = {
            "input_tokens": run.input_tokens,
            "output_tokens": run.output_tokens,
            "total_tokens": run.total_tokens,
            "latency_ms": run.latency_ms,
            "estimated_cost": run.estimated_cost,
            "started_at": run.started_at.isoformat() if run.started_at else None,
            "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        }

        # Safe Prompt configuration (Step 28)
        prompt_config = input_snap.get("prompt_configuration")
        if not prompt_config and (input_snap.get("prompt_id") or input_snap.get("prompt_key")):
            prompt_config = {
                "prompt_id": input_snap.get("prompt_id"),
                "prompt_key": input_snap.get("prompt_key"),
                "prompt_version_id": input_snap.get("prompt_version_id"),
                "prompt_version_number": input_snap.get("prompt_version_number"),
                "prompt_environment": input_snap.get("prompt_environment"),
                "prompt_content_hash": input_snap.get("prompt_content_hash"),
            }

        # Safe Knowledge Graph configuration (Step 29)
        graph_config = input_snap.get("graph_configuration")
        if not graph_config and (input_snap.get("graph_entities") or input_snap.get("graph_context") or input_snap.get("graph_entity_ids")):
            graph_config = {
                "entity_ids": input_snap.get("graph_entity_ids", []),
                "relationship_ids": input_snap.get("graph_relationship_ids", []),
                "source_references": input_snap.get("graph_source_references", []),
                "traversal_config": input_snap.get("graph_traversal_config", {"max_hops": 1}),
                "snapshot_hash": input_snap.get("graph_snapshot_hash"),
            }

        # Safe Multimodal Artifact configuration (Step 30)
        artifact_config = input_snap.get("artifact_configuration")
        if not artifact_config and (input_snap.get("artifacts") or input_snap.get("artifact_ids")):
            artifact_config = {
                "artifact_ids": input_snap.get("artifact_ids", []),
                "content_hashes": input_snap.get("artifact_content_hashes", {}),
                "selected_parts": input_snap.get("selected_artifact_parts", []),
                "media_preprocessing_config": input_snap.get("media_preprocessing_config", {}),
                "model_capability_requirements": input_snap.get("model_capability_requirements", []),
                "fallback_path": input_snap.get("fallback_path"),
            }

        # Raw snapshot dictionary
        raw_snapshot = {
            "snapshot_version": "1.0",
            "run_id": str(run.id),
            "workflow_run_id": str(input_snap.get("workflow_run_id")) if input_snap.get("workflow_run_id") else None,
            "task_id": str(task_obj.id),
            "workspace_id": str(workspace_id or uuid.uuid4()),
            "project_id": project_id,
            "task_configuration": task_config,
            "execution_requirements": (
                run.execution_requirements
                if isinstance(getattr(run, "execution_requirements", None), dict)
                else (input_snap.get("execution_requirements") if isinstance(input_snap.get("execution_requirements"), dict) else {})
            ),
            "model_configuration": model_config,
            "retrieval_configuration": retrieval_config,
            "tool_configuration": tool_config,
            "connector_configuration": connector_config,
            "memory_configuration": memory_config,
            "evaluation_configuration": evaluation_config,
            "workflow_version": None,
            "relevant_context_metadata": context_metadata,
            "prompt_configuration": prompt_config,
            "graph_configuration": graph_config,
            "artifact_configuration": artifact_config,
            "trace_metadata": trace_meta,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        # Sanitize thoroughly
        sanitized_dict = sanitize_replay_snapshot(raw_snapshot)
        return ExecutionSnapshot.model_validate(sanitized_dict)

    @classmethod
    async def create_snapshot_from_workflow_run(
        cls,
        workflow_run: WorkflowRun,
        session: AsyncSession,
    ) -> ExecutionSnapshot:
        """Constructs an ExecutionSnapshot from a WorkflowRun."""
        workflow_obj = workflow_run.workflow
        if workflow_obj is None:
            wf_res = await session.execute(select(Workflow).where(Workflow.id == workflow_run.workflow_id))
            workflow_obj = wf_res.scalar_one_or_none()

        raw_snapshot = {
            "snapshot_version": "1.0",
            "run_id": str(workflow_run.id),
            "workflow_run_id": str(workflow_run.id),
            "task_id": str(workflow_run.workflow_id),
            "workspace_id": str(workflow_run.workspace_id),
            "project_id": str(workflow_run.project_id) if workflow_run.project_id else None,
            "task_configuration": {
                "workflow_title": workflow_obj.name if workflow_obj else "Workflow",
                "input_data": workflow_run.input_data,
            },
            "execution_requirements": {
                "execution_mode": "workflow",
                "workflow_version": workflow_run.workflow_version,
            },
            "model_configuration": {},
            "retrieval_configuration": {},
            "tool_configuration": {},
            "connector_configuration": {},
            "memory_configuration": {},
            "evaluation_configuration": {},
            "workflow_version": workflow_run.workflow_version,
            "relevant_context_metadata": {
                "execution_state": workflow_run.execution_state,
            },
            "prompt_configuration": (
                workflow_run.input_data.get("prompt_configuration")
                if isinstance(workflow_run.input_data, dict) and workflow_run.input_data.get("prompt_configuration")
                else None
            ),
            "trace_metadata": {
                "duration_ms": workflow_run.duration_ms,
                "started_at": workflow_run.started_at.isoformat() if workflow_run.started_at else None,
                "completed_at": workflow_run.completed_at.isoformat() if workflow_run.completed_at else None,
            },
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        sanitized_dict = sanitize_replay_snapshot(raw_snapshot)
        return ExecutionSnapshot.model_validate(sanitized_dict)
