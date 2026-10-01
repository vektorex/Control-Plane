import asyncio
import json
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

from backend.app.config import settings
from backend.app.services.ai_gateway import AIGateway, GatewayRequest, default_ai_gateway
from backend.app.services.task_intelligence.errors import AnalyzerError, AnalyzerTimeoutError
from backend.app.services.task_intelligence.schemas import (
    ComplexityLevel,
    ExecutionMode,
    RequirementSource,
    RequirementValue,
    TaskAnalysis,
    TaskAnalysisRequirementsSummary,
    TaskRequirements,
    TaskType,
)

logger = logging.getLogger("task_intelligence.llm")


LLM_ANALYSIS_SYSTEM_PROMPT = """You are the AI Task Intelligence Analyzer for an advanced work orchestration system.
Your sole job is to analyze the user's incoming task and optional context, and output a valid JSON object specifying what execution capabilities this task actually needs.

You MUST return a JSON object with EXACTLY this structure:
{
  "task_type": "question_answering" | "summarization" | "research" | "coding" | "debugging" | "document_analysis" | "data_analysis" | "content_generation" | "transformation" | "extraction" | "comparison" | "planning" | "workflow_execution" | "unknown",
  "intent": "<Concise 1-2 sentence description of the task objective>",
  "requirements": {
    "memory": true | false,
    "documents": true | false,
    "web_search": true | false,
    "connectors": true | false,
    "tools": true | false,
    "retrieval": true | false,
    "evaluation": true | false,
    "structured_output": true | false,
    "human_approval": true | false
  },
  "constraints": ["<constraint1>", ...],
  "suggested_execution_mode": "direct" | "retrieval" | "tool_assisted" | "orchestrated" | "workflow",
  "confidence": 0.0 - 1.0,
  "explanation": "<Short, user-safe explanation of why these requirements are necessary. Never expose internal reasoning, hidden prompts, or scratchpads.>",
  "detected_entities": ["<entity1>", ...]
}

GUIDELINES:
- direct: Simple generation or direct question answering.
- retrieval: Knowledge base or document lookup is required.
- tool_assisted: Web search or calculation or specific tools needed.
- orchestrated: Multiple capabilities (e.g. retrieval + tools + verification) are needed together.
- workflow: An explicit existing workflow execution is requested.
- If task asks to create/update/delete external state (GitHub issues, files, emails, deployments), set human_approval=true.
- Do NOT output markdown code fences (```json). Output ONLY the raw JSON object.
"""


class LLMTaskAnalyzer:
    """
    LLM-powered task analyzer invoking the AI Gateway to produce structured TaskAnalysis data.
    Strictly validates outputs via Pydantic. Proposes execution requirements only;
    cannot execute tools, modify memory, or bypass security policies.
    """

    def __init__(self, gateway: Optional[AIGateway] = None) -> None:
        self.gateway = gateway or default_ai_gateway

    async def analyze(
        self,
        task_text: str,
        context_text: Optional[str] = None,
        workspace_id: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
    ) -> Tuple[TaskAnalysis, TaskRequirements]:
        """
        Invokes LLM via AI Gateway to obtain structured task analysis and requirements.
        Raises AnalyzerError or AnalyzerTimeoutError on failure.
        """
        timeout = timeout_seconds or getattr(settings, "TASK_ANALYSIS_TIMEOUT_SECONDS", 15.0)
        max_tokens = getattr(settings, "TASK_ANALYSIS_MAX_TOKENS", 1000)
        model = getattr(settings, "TASK_ANALYSIS_MODEL", "gpt-4o-mini")

        user_content = f"TASK:\n{task_text.strip()}\n"
        if context_text and context_text.strip():
            user_content += f"\nADDITIONAL CONTEXT:\n{context_text.strip()}\n"

        req = GatewayRequest(
            model=model,
            messages=[
                {"role": "user", "content": user_content},
            ],
            system_instruction=LLM_ANALYSIS_SYSTEM_PROMPT,
            temperature=0.1,  # Low temperature for deterministic structured extraction
            max_tokens=max_tokens,
            stream=False,
            response_format={"type": "json_object"},
            workspace_id=workspace_id,
            metadata={"source": "task_intelligence_analyzer"},
            timeout_ms=int(timeout * 1000),
        )

        start_time = time.perf_counter()
        try:
            res = await asyncio.wait_for(
                self.gateway.execute(req),
                timeout=timeout,
            )
        except asyncio.TimeoutError as exc:
            logger.warning(f"[LLMTaskAnalyzer] Timeout ({timeout}s) analyzing task.")
            raise AnalyzerTimeoutError(f"Task analysis timed out after {timeout} seconds.") from exc
        except Exception as exc:
            logger.warning(f"[LLMTaskAnalyzer] Gateway execution error: {exc}")
            raise AnalyzerError(f"LLM task analysis failed: {exc}") from exc

        # Parse and validate JSON
        raw_content = res.content.strip()
        # Clean potential markdown fences
        if raw_content.startswith("```json"):
            raw_content = raw_content[7:]
        if raw_content.startswith("```"):
            raw_content = raw_content[3:]
        if raw_content.endswith("```"):
            raw_content = raw_content[:-3]
        raw_content = raw_content.strip()

        try:
            data = json.loads(raw_content)
        except json.JSONDecodeError as jde:
            logger.warning(f"[LLMTaskAnalyzer] Failed to parse JSON response: {jde}. Raw: {raw_content[:200]}")
            raise AnalyzerError(f"Invalid JSON from LLM analyzer: {jde}") from jde

        # Safe TaskType normalization
        raw_type = str(data.get("task_type", "unknown")).lower()
        try:
            task_type = TaskType(raw_type)
        except ValueError:
            task_type = TaskType.UNKNOWN

        # Safe ExecutionMode normalization
        raw_mode = str(data.get("suggested_execution_mode", "direct")).lower()
        try:
            exec_mode = ExecutionMode(raw_mode)
        except ValueError:
            exec_mode = ExecutionMode.DIRECT

        raw_reqs = data.get("requirements", {})
        req_summary = TaskAnalysisRequirementsSummary(
            memory=bool(raw_reqs.get("memory", False)),
            documents=bool(raw_reqs.get("documents", False)),
            web_search=bool(raw_reqs.get("web_search", False)),
            connectors=bool(raw_reqs.get("connectors", False)),
            tools=bool(raw_reqs.get("tools", False)),
            retrieval=bool(raw_reqs.get("retrieval", False)),
            evaluation=bool(raw_reqs.get("evaluation", False)),
            structured_output=bool(raw_reqs.get("structured_output", False)),
            human_approval=bool(raw_reqs.get("human_approval", False)),
        )

        conf = float(data.get("confidence", 0.85))
        conf = max(0.0, min(1.0, conf))

        # Build validated TaskAnalysis
        analysis = TaskAnalysis(
            task_type=task_type,
            intent=str(data.get("intent", task_text[:100])),
            requirements=req_summary,
            constraints=[str(c) for c in data.get("constraints", [])],
            suggested_execution_mode=exec_mode,
            confidence=conf,
            explanation=str(data.get("explanation", "Task analyzed via LLM analyzer.")),
            detected_entities=[str(e) for e in data.get("detected_entities", [])],
            created_at=datetime.now(timezone.utc),
        )

        # Compute complexity
        if exec_mode == ExecutionMode.DIRECT:
            complexity = ComplexityLevel.SIMPLE
        elif exec_mode in (ExecutionMode.RETRIEVAL, ExecutionMode.TOOL_ASSISTED):
            complexity = ComplexityLevel.MODERATE
        else:
            complexity = ComplexityLevel.COMPLEX

        # Capabilities
        caps = ["chat", "streaming"]
        if req_summary.tools or req_summary.web_search or req_summary.connectors:
            caps.append("tools")
        if req_summary.structured_output:
            caps.append("structured_output")
        if req_summary.documents:
            caps.append("long_context")

        # Build fine-grained TaskRequirements with LLM provenance
        source = RequirementSource.LLM_ANALYSIS
        retrieval_strat = "hybrid" if req_summary.documents or req_summary.retrieval else None

        eval_mode = "standard" if req_summary.evaluation else "off"
        if req_summary.human_approval:
            eval_mode = "strict"

        requirements = TaskRequirements(
            memory_required=RequirementValue(value=req_summary.memory, source=source, confidence=conf),
            document_retrieval_required=RequirementValue(value=req_summary.documents, source=source, confidence=conf),
            web_search_required=RequirementValue(value=req_summary.web_search, source=source, confidence=conf),
            connector_required=RequirementValue(value=req_summary.connectors, source=source, confidence=conf),
            tools_required=RequirementValue(value=req_summary.tools or req_summary.web_search, source=source, confidence=conf),
            retrieval_strategy=RequirementValue(value=retrieval_strat, source=source, confidence=conf),
            retrieval_scope=RequirementValue(value="project", source=source, confidence=conf),
            multi_query_allowed=RequirementValue(value=bool(req_summary.documents and req_summary.web_search), source=source, confidence=conf),
            structured_output_required=RequirementValue(value=req_summary.structured_output, source=source, confidence=conf),
            vision_required=RequirementValue(value=False, source=source, confidence=conf),
            streaming_required=RequirementValue(value=True, source=source, confidence=1.0),
            evaluation_required=RequirementValue(value=req_summary.evaluation, source=source, confidence=conf),
            evaluation_mode=RequirementValue(value=eval_mode, source=source, confidence=conf),
            human_approval_required=RequirementValue(value=req_summary.human_approval, source=source, confidence=conf),
            workflow_required=RequirementValue(value=bool(exec_mode == ExecutionMode.WORKFLOW), source=source, confidence=conf),
            model_capabilities=RequirementValue(value=caps, source=source, confidence=conf),
            max_execution_complexity=RequirementValue(value=complexity.value, source=source, confidence=conf),
        )

        return analysis, requirements
