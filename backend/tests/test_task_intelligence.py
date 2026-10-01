import asyncio
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from fastapi.testclient import TestClient

from backend.app.services.ai_gateway import GatewayRequest, GatewayResponse, GatewayUsage
from backend.app.services.task_intelligence import (
    ComplexityLevel,
    ExecutionMode,
    ExecutionPreviewResponse,
    ExecutionRequirements,
    ExecutionRequirementsValidator,
    HybridTaskAnalyzer,
    LLMTaskAnalyzer,
    PolicyViolationError,
    RequirementSource,
    RequirementValidationError,
    RuleBasedTaskAnalyzer,
    TaskAnalysis,
    TaskIntelligenceService,
    TaskRequirementResolver,
    TaskRequirements,
    TaskType,
    default_task_intelligence_service,
)
from backend.app.services.task_intelligence.errors import AnalyzerError, AnalyzerTimeoutError


# =============================================================================
# 1. Deterministic Analysis & Classification Tests
# =============================================================================

def test_deterministic_task_classification():
    analyzer = RuleBasedTaskAnalyzer()

    # Research
    analysis, reqs = analyzer.analyze("Research recent developments in quantum computing and find new information.")
    assert analysis.task_type == TaskType.RESEARCH

    # Coding
    analysis, reqs = analyzer.analyze("Write a python function to implement quicksort with tests.")
    assert analysis.task_type == TaskType.CODING

    # Debugging
    analysis, reqs = analyzer.analyze("Debug this traceback and fix the error: IndexError in list index out of range.")
    assert analysis.task_type == TaskType.DEBUGGING

    # Summarization
    analysis, reqs = analyzer.analyze("Summarize the key takeaways and provide a brief overview of this article.")
    assert analysis.task_type == TaskType.SUMMARIZATION

    # Extraction
    analysis, reqs = analyzer.analyze("Extract all email addresses and phone numbers from this text.")
    assert analysis.task_type == TaskType.EXTRACTION

    # Comparison
    analysis, reqs = analyzer.analyze("Compare the differences between PostgreSQL and MySQL in production.")
    assert analysis.task_type == TaskType.COMPARISON


def test_deterministic_retrieval_detection():
    analyzer = RuleBasedTaskAnalyzer()
    analysis, reqs = analyzer.analyze("Answer the question from my documents and reference the uploaded files.")
    assert analysis.requirements.documents is True
    assert analysis.requirements.retrieval is True
    assert reqs.document_retrieval_required.value is True
    assert reqs.document_retrieval_required.source == RequirementSource.DETERMINISTIC_RULE
    assert analysis.suggested_execution_mode == ExecutionMode.RETRIEVAL


def test_deterministic_web_search_detection():
    analyzer = RuleBasedTaskAnalyzer()
    analysis, reqs = analyzer.analyze("Search the web for today's breaking news and latest tech events.")
    assert analysis.requirements.web_search is True
    assert reqs.web_search_required.value is True
    assert analysis.suggested_execution_mode == ExecutionMode.TOOL_ASSISTED


def test_deterministic_connector_detection():
    analyzer = RuleBasedTaskAnalyzer()
    analysis, reqs = analyzer.analyze("Fetch open pull requests and list commits from my GitHub repository.")
    assert analysis.requirements.connectors is True
    assert reqs.connector_required.value is True
    assert analysis.suggested_execution_mode == ExecutionMode.TOOL_ASSISTED


def test_deterministic_structured_output_detection():
    analyzer = RuleBasedTaskAnalyzer()
    analysis, reqs = analyzer.analyze("List the top 5 programming languages and return JSON with schema.")
    assert analysis.requirements.structured_output is True
    assert reqs.structured_output_required.value is True


def test_deterministic_vision_detection():
    analyzer = RuleBasedTaskAnalyzer()
    analysis, reqs = analyzer.analyze("Look at this picture and analyze this image for defects.")
    assert reqs.vision_required.value is True
    assert "vision" in reqs.model_capabilities.value


def test_deterministic_memory_detection():
    analyzer = RuleBasedTaskAnalyzer()
    analysis, reqs = analyzer.analyze("Remember this preference and use my usual coding style for the solution.")
    assert analysis.requirements.memory is True
    assert reqs.memory_required.value is True


def test_deterministic_hitl_external_action_detection():
    analyzer = RuleBasedTaskAnalyzer()
    analysis, reqs = analyzer.analyze("Create a GitHub issue in the repository to report this security bug.")
    assert analysis.requirements.human_approval is True
    assert reqs.human_approval_required.value is True
    assert reqs.evaluation_mode.value == "strict"


def test_deterministic_orchestrated_mode_detection():
    analyzer = RuleBasedTaskAnalyzer()
    # Documents + Web Search = Orchestrated
    analysis, reqs = analyzer.analyze(
        "Search the web for recent papers and compare them with the findings from my documents."
    )
    assert analysis.requirements.web_search is True
    assert analysis.requirements.documents is True
    assert analysis.suggested_execution_mode == ExecutionMode.ORCHESTRATED


def test_complexity_classification():
    analyzer = RuleBasedTaskAnalyzer()

    # Simple: direct question
    analysis_simple, reqs_simple = analyzer.analyze("What is the capital of France?")
    assert reqs_simple.max_execution_complexity.value == ComplexityLevel.SIMPLE.value

    # Moderate: single retrieval or tool
    analysis_mod, reqs_mod = analyzer.analyze("Search the web for Python 3.13 features.")
    assert reqs_mod.max_execution_complexity.value == ComplexityLevel.MODERATE.value

    # Complex: retrieval + web search
    analysis_comp, reqs_comp = analyzer.analyze("Search the web and compare with my documents.")
    assert reqs_comp.max_execution_complexity.value == ComplexityLevel.COMPLEX.value


# =============================================================================
# 2. LLM Analyzer & Validation Tests
# =============================================================================

@pytest.mark.asyncio
async def test_llm_analyzer_structured_success():
    mock_gw = MagicMock()
    mock_response = GatewayResponse(
        request_id="req-123",
        provider="mock",
        model="gpt-4o-mini",
        content="""{
            "task_type": "research",
            "intent": "Research competitive landscape for AI agents.",
            "requirements": {
                "memory": false,
                "documents": true,
                "web_search": true,
                "connectors": false,
                "tools": true,
                "retrieval": true,
                "evaluation": true,
                "structured_output": false,
                "human_approval": false
            },
            "constraints": ["cite sources"],
            "suggested_execution_mode": "orchestrated",
            "confidence": 0.92,
            "explanation": "Requires multi-source research using documents and web search.",
            "detected_entities": ["AI agents", "competitive landscape"]
        }""",
        usage=GatewayUsage(input_tokens=50, output_tokens=50, total_tokens=100),
    )
    mock_gw.execute = AsyncMock(return_value=mock_response)

    analyzer = LLMTaskAnalyzer(gateway=mock_gw)
    analysis, reqs = await analyzer.analyze("Analyze the AI agents market.")

    assert analysis.task_type == TaskType.RESEARCH
    assert analysis.requirements.web_search is True
    assert analysis.requirements.documents is True
    assert analysis.suggested_execution_mode == ExecutionMode.ORCHESTRATED
    assert reqs.web_search_required.source == RequirementSource.LLM_ANALYSIS
    assert reqs.document_retrieval_required.source == RequirementSource.LLM_ANALYSIS


@pytest.mark.asyncio
async def test_llm_analyzer_invalid_json_raises():
    mock_gw = MagicMock()
    mock_response = GatewayResponse(
        request_id="req-err",
        provider="mock",
        model="gpt-4o-mini",
        content="This is not JSON at all.",
        usage=GatewayUsage(),
    )
    mock_gw.execute = AsyncMock(return_value=mock_response)

    analyzer = LLMTaskAnalyzer(gateway=mock_gw)
    with pytest.raises(AnalyzerError):
        await analyzer.analyze("Analyze this task.")


@pytest.mark.asyncio
async def test_llm_analyzer_timeout_raises():
    mock_gw = MagicMock()

    async def slow_execute(req):
        await asyncio.sleep(0.5)
        return GatewayResponse(request_id="1", provider="m", model="m", content="{}")

    mock_gw.execute = slow_execute

    analyzer = LLMTaskAnalyzer(gateway=mock_gw)
    with pytest.raises(AnalyzerTimeoutError):
        await analyzer.analyze("Task", timeout_seconds=0.05)


# =============================================================================
# 3. Hybrid Analyzer & Fallback Tests
# =============================================================================

@pytest.mark.asyncio
async def test_hybrid_confident_deterministic_skips_llm():
    mock_llm = MagicMock()
    mock_llm.analyze = AsyncMock()

    rule_analyzer = RuleBasedTaskAnalyzer()
    hybrid = HybridTaskAnalyzer(rule_analyzer=rule_analyzer, llm_analyzer=mock_llm)

    # Prompt with clear, strong signals
    analysis, reqs, fallback = await hybrid.analyze(
        task_text="Search the web for today's breaking news in technology.",
        mode="hybrid",
    )

    assert analysis.task_type == TaskType.RESEARCH
    assert reqs.web_search_required.value is True
    assert fallback is False
    # LLM analyze should NOT be called because deterministic confidence is >= 0.8
    assert mock_llm.analyze.call_count == 0


@pytest.mark.asyncio
async def test_hybrid_fallback_on_llm_failure():
    mock_llm = MagicMock()
    mock_llm.analyze = AsyncMock(side_effect=AnalyzerError("LLM Gateway outage"))

    rule_analyzer = RuleBasedTaskAnalyzer()
    hybrid = HybridTaskAnalyzer(rule_analyzer=rule_analyzer, llm_analyzer=mock_llm)

    # Ambiguous prompt that triggers LLM
    analysis, reqs, fallback = await hybrid.analyze(
        task_text="Help with some data.",
        mode="llm",
    )

    # Must seamlessly fall back to deterministic without crashing
    assert fallback is True
    assert analysis is not None
    assert reqs is not None


# =============================================================================
# 4. Requirement Merging & Policy Precedence Tests
# =============================================================================

def test_requirement_merging_user_override():
    rule_analyzer = RuleBasedTaskAnalyzer()
    analysis, det_reqs = rule_analyzer.analyze("Search the web for recent articles.")

    # Even though task asked for web search, user explicitly disables web search
    resolved = TaskRequirementResolver.merge_requirements(
        deterministic_reqs=det_reqs,
        llm_reqs=None,
        user_overrides={"enable_web_search": False},
    )

    assert resolved.web_search_required.value is False
    assert resolved.web_search_required.source == RequirementSource.USER


def test_requirement_merging_policy_override():
    rule_analyzer = RuleBasedTaskAnalyzer()
    analysis, det_reqs = rule_analyzer.analyze("Search the web for articles.")

    # User wanted web search, but workspace policy strictly disables it
    resolved = TaskRequirementResolver.merge_requirements(
        deterministic_reqs=det_reqs,
        llm_reqs=None,
        user_overrides={"enable_web_search": True},
        workspace_policy={"allow_web_search": False},
    )

    # Policy overrides user!
    assert resolved.web_search_required.value is False
    assert resolved.web_search_required.source == RequirementSource.POLICY


def test_model_suggestion_cannot_weaken_deterministic_rule():
    rule_analyzer = RuleBasedTaskAnalyzer()
    analysis, det_reqs = rule_analyzer.analyze("From my documents answer this question.")

    # Simulated LLM proposing documents=False
    llm_reqs = det_reqs.model_copy(deep=True)
    from backend.app.services.task_intelligence.schemas import RequirementValue
    llm_reqs.document_retrieval_required = RequirementValue(value=False, source=RequirementSource.LLM_ANALYSIS)

    merged = TaskRequirementResolver.merge_requirements(
        deterministic_reqs=det_reqs,
        llm_reqs=llm_reqs,
    )

    # LLM cannot downgrade deterministic detection to False
    assert merged.document_retrieval_required.value is True
    assert merged.document_retrieval_required.source == RequirementSource.DETERMINISTIC_RULE


# =============================================================================
# 5. Requirement Validation & Workspace Policy Tests
# =============================================================================

def test_validator_rejects_invalid_execution_mode():
    exec_reqs = ExecutionRequirements(
        execution_mode="invalid_alien_mode",
        task_type="research",
        complexity="moderate",
    )
    with pytest.raises(RequirementValidationError):
        ExecutionRequirementsValidator.validate(exec_reqs)


def test_validator_rejects_excessive_retrieval_top_k():
    exec_reqs = ExecutionRequirements(
        execution_mode="retrieval",
        task_type="research",
        complexity="moderate",
        retrieval={"enabled": True, "top_k": 999},  # exceeds limit 50
    )
    with pytest.raises(RequirementValidationError):
        ExecutionRequirementsValidator.validate(exec_reqs)


def test_validator_enforces_workspace_tool_policy():
    exec_reqs = ExecutionRequirements(
        execution_mode="tool_assisted",
        task_type="research",
        complexity="moderate",
        tools={"enabled": True, "web_search": True, "allowed_tools": ["web_search"]},
    )
    # Workspace blocks tools
    with pytest.raises(PolicyViolationError):
        ExecutionRequirementsValidator.validate(exec_reqs, workspace_policy={"allow_tools": False})


# =============================================================================
# 6. TaskIntelligenceService Facade Tests
# =============================================================================

@pytest.mark.asyncio
async def test_service_analyze_direct():
    service = TaskIntelligenceService()
    resp = await service.analyze("Explain quantum entanglement in simple terms.")
    assert resp.execution_mode == "direct"
    assert resp.complexity == "simple"
    assert resp.analysis.task_type in (TaskType.QUESTION_ANSWERING, TaskType.UNKNOWN)


@pytest.mark.asyncio
async def test_service_preview_execution():
    service = TaskIntelligenceService()
    preview = await service.preview_execution("From my documents and search the web, give me recent news.")
    assert isinstance(preview, ExecutionPreviewResponse)
    assert preview.execution_mode == "orchestrated"
    assert preview.retrieval["enabled"] is True
    assert preview.tools["web_search"] is True


# =============================================================================
# 7. Task Intelligence API Integration Tests
# =============================================================================

def test_api_task_analyze_endpoint(client: TestClient, user1_auth):
    resp = client.post(
        "/api/tasks/analyze",
        json={"task": "Search the web for the latest Python updates and return JSON.", "mode": "deterministic"},
        headers=user1_auth["headers"],
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "analysis" in data
    assert "requirements" in data
    assert data["execution_mode"] in ("tool_assisted", "orchestrated")
    assert data["analysis"]["requirements"]["web_search"] is True
    assert data["analysis"]["requirements"]["structured_output"] is True


def test_api_task_preview_execution_endpoint(client: TestClient, user1_auth):
    resp = client.post(
        "/api/tasks/preview-execution",
        json={"task": "From my documents answer what is our refund policy.", "mode": "deterministic"},
        headers=user1_auth["headers"],
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["execution_mode"] == "retrieval"
    assert data["retrieval"]["enabled"] is True
    assert "explanation" in data


def test_api_existing_task_preview(client: TestClient, user1_auth):
    # 1. Create Workspace & Project
    ws = client.post("/api/workspaces", json={"name": "TI WS"}, headers=user1_auth["headers"]).json()
    ws_id = ws["id"]
    proj = client.post(f"/api/workspaces/{ws_id}/projects", json={"name": "TI Project"}, headers=user1_auth["headers"]).json()
    p_id = proj["id"]

    # 2. Create task
    t_res = client.post(
        f"/api/projects/{p_id}/tasks",
        json={
            "title": "Analyze doc",
            "instructions": "From my documents review the contract clauses.",
        },
        headers=user1_auth["headers"],
    ).json()
    t_id = t_res["id"]

    # 3. Preview existing task
    prev_res = client.post(f"/api/tasks/{t_id}/preview-execution", headers=user1_auth["headers"])
    assert prev_res.status_code == 200
    p_data = prev_res.json()
    assert p_data["retrieval"]["enabled"] is True
    assert p_data["execution_mode"] == "retrieval"
