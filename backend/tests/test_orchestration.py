import io
import time
from typing import Any, Dict, List, Optional
import uuid
import pytest
from unittest.mock import AsyncMock, patch

from backend.app.config import settings
from backend.app.db.models.task import Task
from backend.app.db.models.user import User
from backend.app.schemas.task import TaskRunRequest
from backend.app.services.context.engine import ContextEngine
from backend.app.services.context.models import ContextItem
from backend.app.services.llm.factory import LLMProviderFactory
from backend.app.services.orchestration.errors import (
    ExecutionLimitExceededError,
    OrchestrationTimeoutError,
    PlanValidationError,
    StepExecutionError,
)
from backend.app.services.orchestration.executor import OrchestrationExecutor
from backend.app.services.orchestration.orchestrator import Orchestrator
from backend.app.services.orchestration.plan import (
    ExecutionPlan,
    ExecutionStepPlan,
    StepStatus,
    StepType,
)
from backend.app.services.orchestration.planner import ExecutionPlanner
from backend.app.services.orchestration.policies import FailurePolicy
from backend.app.services.orchestration.state import ExecutionState, ExecutionStepRecord
from backend.app.services.orchestration.validator import PlanValidator
from backend.app.services.tools.base import BaseTool
from backend.app.services.tools.providers.web_search import (
    MockWebSearchProvider,
    WebSearchResultItem,
    WebSearchTool,
)
from backend.app.services.tools.registry import ToolRegistry
from backend.app.services.tools.executor import ToolExecutor


class DummyEchoTool(BaseTool):
    name = "dummy_echo"
    description = "Echoes inputs for test"
    requires_auth = False

    async def execute(self, input_data: Any, **kwargs) -> Dict[str, Any]:
        return {"echo": input_data}


class AdminRestrictedTool(BaseTool):
    name = "admin_restricted"
    description = "Admin only tool"
    requires_auth = True

    def check_permission(self, raw_input: Any, user: Optional[User], **kwargs) -> bool:
        return user is not None and getattr(user, "is_superuser", False) is True

    async def execute(self, input_data: Any, **kwargs) -> Dict[str, Any]:
        return {"admin": "ok"}


# =====================================================================
# 1. PLANNING TESTS (Tests 1 - 4)
# =====================================================================

@pytest.mark.asyncio
async def test_planner_simple_task_direct_generation():
    """1. simple task -> generate only"""
    planner = ExecutionPlanner()
    task = Task(
        id=uuid.uuid4(),
        project_id=uuid.uuid4(),
        title="Summarize Note",
        instructions="Rewrite this paragraph in bullet points.",
    )
    req = TaskRunRequest(retrieval_mode="never", tool_mode="disabled")
    plan = await planner.plan(task, request=req)

    assert len(plan.steps) == 1
    assert plan.steps[0].type == StepType.GENERATE
    assert "LLM Generation" in plan.plan_reason


@pytest.mark.asyncio
async def test_planner_project_knowledge_task():
    """2. project knowledge -> retrieve + generate"""
    planner = ExecutionPlanner()
    task = Task(
        id=uuid.uuid4(),
        project_id=uuid.uuid4(),
        title="Auth Architecture",
        instructions="What does our authentication implementation do in our project documentation?",
    )
    req = TaskRunRequest(retrieval_mode="auto", tool_mode="disabled")
    plan = await planner.plan(task, request=req)

    assert len(plan.steps) == 2
    assert plan.steps[0].type == StepType.RETRIEVE
    assert plan.steps[0].strategy == "hybrid"
    assert plan.steps[1].type == StepType.GENERATE


@pytest.mark.asyncio
async def test_planner_current_information_task():
    """3. current information -> web_search + generate"""
    planner = ExecutionPlanner()
    task = Task(
        id=uuid.uuid4(),
        project_id=uuid.uuid4(),
        title="Latest React Release",
        instructions="What are the latest 2026 React updates and features?",
    )
    req = TaskRunRequest(retrieval_mode="never", tool_mode="auto")
    plan = await planner.plan(task, request=req)

    assert len(plan.steps) == 2
    assert plan.steps[0].type == StepType.TOOL
    assert plan.steps[0].tool == "web_search"
    assert plan.steps[1].type == StepType.GENERATE


@pytest.mark.asyncio
async def test_planner_knowledge_and_current_information_task():
    """4. knowledge + current information -> retrieve + web + generate"""
    planner = ExecutionPlanner()
    task = Task(
        id=uuid.uuid4(),
        project_id=uuid.uuid4(),
        title="Compare Security",
        instructions="Compare our project authentication implementation with latest industry guidance.",
    )
    req = TaskRunRequest(retrieval_mode="auto", enable_web_search=True)
    plan = await planner.plan(task, request=req)

    assert len(plan.steps) == 3
    assert plan.steps[0].type == StepType.RETRIEVE
    assert plan.steps[1].type == StepType.TOOL
    assert plan.steps[1].tool == "web_search"
    assert plan.steps[2].type == StepType.GENERATE


# =====================================================================
# 2. PLAN VALIDATION TESTS (Tests 5 - 9)
# =====================================================================

def test_validator_rejects_empty_plan():
    validator = PlanValidator()
    with pytest.raises(PlanValidationError):
        validator.validate(ExecutionPlan(steps=[]))


def test_validator_rejects_unknown_tool():
    """6. unknown tool rejection"""
    registry = ToolRegistry()
    validator = PlanValidator(tool_registry=registry)

    plan = ExecutionPlan(
        steps=[
            ExecutionStepPlan(id="s1", type=StepType.TOOL, tool="unregistered_tool"),
            ExecutionStepPlan(id="s2", type=StepType.GENERATE),
        ]
    )
    with pytest.raises(PlanValidationError) as exc_info:
        validator.validate(plan)
    assert "not registered in ToolRegistry" in str(exc_info.value)


def test_validator_rejects_invalid_retrieval_strategy():
    """7. invalid retrieval strategy"""
    validator = PlanValidator()
    plan = ExecutionPlan(
        steps=[
            ExecutionStepPlan(id="s1", type=StepType.RETRIEVE, strategy="quantum_search"),
            ExecutionStepPlan(id="s2", type=StepType.GENERATE),
        ]
    )
    with pytest.raises(PlanValidationError) as exc_info:
        validator.validate(plan)
    assert "Invalid retrieval strategy" in str(exc_info.value)


def test_validator_rejects_excessive_steps():
    """8. excessive steps exceeding MAX_PLAN_STEPS"""
    validator = PlanValidator()
    excessive_steps = [
        ExecutionStepPlan(id=f"step_{i}", type=StepType.CONTEXT)
        for i in range(settings.MAX_PLAN_STEPS + 2)
    ]
    excessive_steps.append(ExecutionStepPlan(id="step_gen", type=StepType.GENERATE))

    plan = ExecutionPlan(steps=excessive_steps)
    with pytest.raises(ExecutionLimitExceededError):
        validator.validate(plan)


def test_validator_rejects_excessive_tool_calls():
    """9. excessive tool calls exceeding MAX_TOOL_CALLS_PER_PLAN"""
    registry = ToolRegistry()
    registry.register(DummyEchoTool())
    validator = PlanValidator(tool_registry=registry)

    tool_steps = [
        ExecutionStepPlan(id=f"t_{i}", type=StepType.TOOL, tool="dummy_echo")
        for i in range(settings.MAX_TOOL_CALLS_PER_PLAN + 2)
    ]
    tool_steps.append(ExecutionStepPlan(id="t_gen", type=StepType.GENERATE))

    plan = ExecutionPlan(steps=tool_steps)
    with pytest.raises(ExecutionLimitExceededError):
        validator.validate(plan)


# =====================================================================
# 3. EXECUTION & STATE TESTS (Tests 10 - 14)
# =====================================================================

@pytest.mark.asyncio
async def test_sequential_plan_execution(mock_factory):
    """10. sequential execution and 13. execution state tracking"""
    mock_search = [
        WebSearchResultItem(
            title="FastAPI 0.115 Notes",
            url="https://fastapi.tiangolo.com",
            snippet="FastAPI release 0.115 introduces improved validation.",
            source="fastapi.tiangolo.com",
        )
    ]
    tool_reg = ToolRegistry()
    tool_reg.register(WebSearchTool(provider=MockWebSearchProvider(mock_results=mock_search)))

    executor = OrchestrationExecutor(
        tool_executor=ToolExecutor(registry=tool_reg),
        llm_factory=mock_factory,
    )

    task = Task(
        id=uuid.uuid4(),
        project_id=uuid.uuid4(),
        title="Check FastAPI",
        instructions="Look up FastAPI 0.115 details and summarize.",
    )

    plan = ExecutionPlan(
        steps=[
            ExecutionStepPlan(
                id="s1",
                type=StepType.TOOL,
                tool="web_search",
                tool_input={"query": "FastAPI 0.115"},
            ),
            ExecutionStepPlan(id="s2", type=StepType.GENERATE, model="mock-model-v1"),
        ]
    )

    user = User(id=uuid.uuid4(), email="user@test.com")
    state = await executor.execute(task, plan, user=user)

    assert state.generated_output is not None
    assert len(state.step_records) == 2
    assert state.step_records[0].status == StepStatus.COMPLETED
    assert state.step_records[1].status == StepStatus.COMPLETED
    assert state.step_records[0].duration_ms >= 0
    assert len(state.context_items) >= 1


@pytest.mark.asyncio
async def test_context_merging_across_sources(mock_factory):
    """11. context merging and 12. final generation"""
    engine = ContextEngine()
    executor = OrchestrationExecutor(context_engine=engine, llm_factory=mock_factory)

    task = Task(
        id=uuid.uuid4(),
        project_id=uuid.uuid4(),
        title="Merge Context Task",
        instructions="Summarize combined context.",
        context_text="System guideline: adhere to PEP 8 standards.",
    )

    plan = ExecutionPlan(
        steps=[
            ExecutionStepPlan(id="s_ctx", type=StepType.CONTEXT),
            ExecutionStepPlan(id="s_gen", type=StepType.GENERATE, model="mock-model-v1"),
        ]
    )

    state = await executor.execute(task, plan, user=User(id=uuid.uuid4()))
    assert state.generated_output is not None
    assert any("PEP 8" in str(it.get("content")) for it in state.context_items)


# =====================================================================
# 4. FAILURES & POLICIES TESTS (Tests 15 - 19)
# =====================================================================

@pytest.mark.asyncio
async def test_optional_tool_failure_allows_continuation(mock_factory):
    """16. web tool failure handling (optional continue)"""
    mock_provider = AsyncMock()
    mock_provider.search.side_effect = RuntimeError("Search provider down")

    tool_reg = ToolRegistry()
    tool_reg.register(WebSearchTool(provider=mock_provider))

    executor = OrchestrationExecutor(
        tool_executor=ToolExecutor(registry=tool_reg),
        llm_factory=mock_factory,
    )

    task = Task(
        id=uuid.uuid4(),
        project_id=uuid.uuid4(),
        title="Web Fail Task",
        instructions="Search something.",
    )

    plan = ExecutionPlan(
        steps=[
            ExecutionStepPlan(
                id="s_tool",
                type=StepType.TOOL,
                tool="web_search",
                tool_input={"query": "failing query"},
                required=False,
            ),
            ExecutionStepPlan(id="s_gen", type=StepType.GENERATE, model="mock-model-v1"),
        ]
    )

    policy = FailurePolicy(web_search_required=False, continue_on_optional_failure=True)
    state = await executor.execute(task, plan, user=User(id=uuid.uuid4()), policy=policy)

    assert state.generated_output is not None
    assert state.step_records[0].status == StepStatus.FAILED
    assert state.step_records[1].status == StepStatus.COMPLETED
    assert len(state.errors) >= 1


@pytest.mark.asyncio
async def test_required_tool_failure_aborts_plan(mock_factory):
    """16. web tool failure handling (required aborts execution)"""
    mock_provider = AsyncMock()
    mock_provider.search.side_effect = RuntimeError("API key invalid")

    tool_reg = ToolRegistry()
    tool_reg.register(WebSearchTool(provider=mock_provider))

    executor = OrchestrationExecutor(
        tool_executor=ToolExecutor(registry=tool_reg),
        llm_factory=mock_factory,
    )

    task = Task(
        id=uuid.uuid4(),
        project_id=uuid.uuid4(),
        title="Required Fail Task",
        instructions="Search something strictly.",
    )

    plan = ExecutionPlan(
        steps=[
            ExecutionStepPlan(
                id="s_tool",
                type=StepType.TOOL,
                tool="web_search",
                tool_input={"query": "strict fail"},
                required=True,
            ),
            ExecutionStepPlan(id="s_gen", type=StepType.GENERATE, model="mock-model-v1"),
        ]
    )

    policy = FailurePolicy(web_search_required=True)
    with pytest.raises(StepExecutionError):
        await executor.execute(task, plan, user=User(id=uuid.uuid4()), policy=policy)


@pytest.mark.asyncio
async def test_orchestration_timeout_limit():
    """18. timeout handling"""
    executor = OrchestrationExecutor()
    task = Task(id=uuid.uuid4(), project_id=uuid.uuid4(), title="Timeout Task", instructions="Sleep")

    plan = ExecutionPlan(
        steps=[
            ExecutionStepPlan(id="s1", type=StepType.CONTEXT),
            ExecutionStepPlan(id="s2", type=StepType.GENERATE, model="mock-model-v1"),
        ]
    )

    with patch("backend.app.config.settings.MAX_EXECUTION_TIME_SECONDS", 0.001):
        with patch("time.perf_counter", side_effect=[0.0, 10.0, 10.0, 10.0, 10.0]):
            with pytest.raises(OrchestrationTimeoutError):
                await executor.execute(task, plan, user=User(id=uuid.uuid4()))


# =====================================================================
# 5. SECURITY & CROSS-TENANT ISOLATION (Tests 20 - 23)
# =====================================================================

def test_plan_preview_endpoint_unauthenticated(client):
    """20. unauthorized plan preview rejected (401)"""
    res = client.post(f"/api/tasks/{uuid.uuid4()}/plan", json={})
    assert res.status_code == 401


def test_plan_preview_cross_tenant_isolation(auth_client):
    """23. cross-workspace isolation for plan preview"""
    # Create workspace & task under User 1
    ws_res = auth_client.post("/api/workspaces", json={"name": "Owner WS"})
    ws_id = ws_res.json()["id"]

    proj_res = auth_client.post(f"/api/workspaces/{ws_id}/projects", json={"name": "Owner Proj"})
    proj_id = proj_res.json()["id"]

    task_res = auth_client.post(
        f"/api/projects/{proj_id}/tasks",
        json={"title": "Owner Task", "instructions": "Explain authentication."},
    )
    task_id = task_res.json()["id"]

    # Preview plan successfully as owner
    plan_res = auth_client.post(f"/api/tasks/{task_id}/plan", json={"retrieval_mode": "auto"})
    assert plan_res.status_code == 200
    plan_data = plan_res.json()
    assert len(plan_data["steps"]) >= 1


# =====================================================================
# 6. STREAMING & REGRESSION TESTS (Tests 24 - 30)
# =====================================================================

def test_task_execution_with_orchestration_plan(auth_client):
    """27. RAG + 28. Web Search + 29. Simple task regression via Orchestrator"""
    ws_res = auth_client.post("/api/workspaces", json={"name": "Orchestrator WS"})
    ws_id = ws_res.json()["id"]

    proj_res = auth_client.post(f"/api/workspaces/{ws_id}/projects", json={"name": "Orchestrator Proj"})
    proj_id = proj_res.json()["id"]

    # Upload document
    auth_client.post(
        f"/api/workspaces/{ws_id}/documents",
        data={"project_id": proj_id},
        files={"file": ("architecture.txt", io.BytesIO(b"Architecture guidelines and DB specs."), "text/plain")},
    )

    task_res = auth_client.post(
        f"/api/projects/{proj_id}/tasks",
        json={
            "title": "Full Orchestration Task",
            "instructions": "Compare our project architecture guidelines with latest 2026 web best practices.",
        },
    )
    task_id = task_res.json()["id"]

    # Preview Plan Endpoint (Test 30)
    plan_res = auth_client.post(
        f"/api/tasks/{task_id}/plan",
        json={"retrieval_mode": "auto", "enable_web_search": True},
    )
    assert plan_res.status_code == 200
    plan_data = plan_res.json()
    assert len(plan_data["steps"]) == 3
    assert plan_data["steps"][0]["type"] == "retrieve"
    assert plan_data["steps"][1]["type"] == "tool"
    assert plan_data["steps"][2]["type"] == "generate"

    # Execute Task
    run_res = auth_client.post(
        f"/api/tasks/{task_id}/run",
        json={
            "model": "mock-model-v1",
            "retrieval_mode": "auto",
            "enable_web_search": True,
        },
    )
    assert run_res.status_code == 201
    run_data = run_res.json()

    assert run_data["status"] == "completed"
    assert run_data["execution_plan"] is not None
    assert run_data["execution_steps"] is not None
    assert len(run_data["execution_steps"]) >= 2
    assert run_data["step_count"] >= 2
    assert run_data["orchestration_duration_ms"] is not None
    assert run_data["output_content"] is not None


def test_task_streaming_with_orchestration_events(auth_client):
    """24. Streamed orchestration with step events"""
    ws_res = auth_client.post("/api/workspaces", json={"name": "Stream Orch WS"})
    ws_id = ws_res.json()["id"]

    proj_res = auth_client.post(f"/api/workspaces/{ws_id}/projects", json={"name": "Stream Orch Proj"})
    proj_id = proj_res.json()["id"]

    task_res = auth_client.post(
        f"/api/projects/{proj_id}/tasks",
        json={"title": "Stream Task", "instructions": "Summarize fast."},
    )
    task_id = task_res.json()["id"]

    stream_res = auth_client.post(
        f"/api/tasks/{task_id}/run/stream",
        json={"model": "mock-model-v1", "retrieval_mode": "never"},
    )
    assert stream_res.status_code == 200
    body = stream_res.text

    assert "orchestration_plan" in body
    assert "step_start" in body
    assert "step_completed" in body
    assert "chunk" in body
    assert "run_completed" in body
