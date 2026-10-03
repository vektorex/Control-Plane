import json
import logging
import time
from typing import Any, Dict, List
from pydantic import BaseModel, Field

from backend.app.services.evaluation.base import LLMEvaluator
from backend.app.services.evaluation.policies import EvaluationPolicy
from backend.app.services.evaluation.schemas import (
    CheckResult,
    CheckType,
    EvaluationContext,
    EvaluationFindingItem,
    FindingStatus,
)

logger = logging.getLogger("evaluation.completeness")


class CompletenessLLMOutput(BaseModel):
    status: str = Field(..., description="'passed' | 'warning' | 'failed'")
    confidence: float = Field(default=0.9, ge=0.0, le=1.0)
    missing_requirements: List[str] = Field(default_factory=list, description="Explicit requested points that were not addressed")
    addressed_requirements: List[str] = Field(default_factory=list, description="Explicit requested points successfully addressed")
    explanation: str = Field(default="")


class CompletenessEvaluator(LLMEvaluator):
    """
    CompletenessEvaluator determines whether the output addressed all observable,
    explicit task requirements without relying on unstated or hidden assumptions.
    """
    check_type = CheckType.COMPLETENESS

    COMPLETENESS_SYSTEM_PROMPT = """You are an objective Completeness Evaluator in an AI Work Layer.
Your task is to determine whether the candidate response has fulfilled the explicit directives and requirements stated in the user's task.

### STRICT RULES:
1. Evaluate ONLY observable requirements stated in the Task Directives and Required Sections.
2. Do NOT evaluate subjective preferences, stylistic choices, or unstated hidden criteria.
3. If all explicit task questions/sections/aspects are addressed, set "status": "passed" and "missing_requirements": [].
4. If most requirements are fulfilled but a minor non-critical requested detail or comparison point was omitted, set "status": "warning" and list the missing item.
5. If the response completely misses major requested sections, answers a different question, or leaves critical requirements unfulfilled, set "status": "failed".
6. Output MUST strictly conform to the JSON schema below.

### OUTPUT JSON SCHEMA:
{
  "status": "passed" | "warning" | "failed",
  "confidence": 0.95,
  "missing_requirements": ["requested comparison point 1"],
  "addressed_requirements": ["addressed item 1", "addressed item 2"],
  "explanation": "Clear summary of completeness evaluation"
}
"""

    async def evaluate(
        self,
        ctx: EvaluationContext,
        policy: EvaluationPolicy,
    ) -> CheckResult:
        start_time = time.perf_counter()

        # 1. Deterministic Fast-Fail Check: Empty or whitespace output
        clean_output = (ctx.output_text or "").strip()
        if not clean_output:
            elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            finding = EvaluationFindingItem(
                check_type=CheckType.COMPLETENESS,
                status=FindingStatus.FAILED,
                confidence=1.0,
                description="Response is empty or contains only whitespace.",
                evidence_ids=[],
                metadata={"empty_response": True},
            )
            return CheckResult(
                type=CheckType.COMPLETENESS,
                status=FindingStatus.FAILED,
                confidence=1.0,
                description="Task response is empty.",
                issues=["Task response is empty."],
                findings=[finding],
                metadata={"missing_requirements": ["Non-empty task output"]},
                duration_ms=elapsed_ms,
            )

        # 2. Check required sections deterministically if specified
        missing_sections = []
        if ctx.required_sections:
            for sec in ctx.required_sections:
                sec_lower = sec.lower().strip()
                if sec_lower not in clean_output.lower():
                    missing_sections.append(f"Required section missing: '{sec}'")

        # 3. LLM semantic check for task instruction coverage
        user_prompt = (
            f"=== TASK DIRECTIVES ===\n"
            f"Title: {ctx.task_title}\n"
            f"Instructions: {ctx.task_instructions or ctx.task_title}\n"
        )
        if ctx.required_sections:
            user_prompt += f"Explicit Required Sections: {json.dumps(ctx.required_sections)}\n"

        user_prompt += (
            f"\n=== CANDIDATE ANSWER TO EVALUATE ===\n"
            f"{ctx.output_text}\n\n"
            f"Evaluate whether the candidate answer covers all explicit task directives."
        )

        # Resolve managed evaluator prompt if available
        system_prompt = self.COMPLETENESS_SYSTEM_PROMPT
        try:
            from backend.app.services.prompts.resolver import default_prompt_resolver
            from backend.app.services.prompts.constants import PromptEnvironment
            res_result = await default_prompt_resolver.resolve_by_key(
                prompt_key="evaluation.completeness",
                environment=PromptEnvironment.PRODUCTION.value,
            )
            if res_result and res_result.version and res_result.version.content:
                system_prompt = res_result.version.content
        except Exception:
            pass

        try:
            llm_result: CompletenessLLMOutput = await self._call_structured_llm(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                response_model=CompletenessLLMOutput,
                temperature=0.0,
            )

            all_missing = list(set(llm_result.missing_requirements + missing_sections))
            status_str = llm_result.status.lower().strip()

            if missing_sections and status_str == "passed":
                status_str = "warning"

            if not all_missing and status_str == "passed":
                f_status = FindingStatus.PASSED
            elif status_str == "warning" or (all_missing and not policy.strict_mode):
                f_status = FindingStatus.WARNING
            else:
                f_status = FindingStatus.FAILED

            findings = []
            for miss in all_missing:
                findings.append(
                    EvaluationFindingItem(
                        check_type=CheckType.COMPLETENESS,
                        status=f_status,
                        confidence=llm_result.confidence,
                        description=f"Missing requirement: {miss}",
                        evidence_ids=[],
                        metadata={"missing_item": miss},
                    )
                )

            desc = llm_result.explanation or (
                "All explicit task requirements are fully addressed."
                if f_status == FindingStatus.PASSED
                else f"Missing {len(all_missing)} requested requirement(s)."
            )

            elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            return CheckResult(
                type=CheckType.COMPLETENESS,
                status=f_status,
                confidence=llm_result.confidence,
                description=desc,
                issues=all_missing,
                findings=findings,
                metadata={
                    "missing_requirements": all_missing,
                    "addressed_requirements": llm_result.addressed_requirements,
                },
                duration_ms=elapsed_ms,
            )

        except Exception as err:
            logger.warning(f"CompletenessEvaluator failed with error: {err}. Returning fallback.")
            elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            return CheckResult(
                type=CheckType.COMPLETENESS,
                status=FindingStatus.WARNING,
                confidence=0.5,
                description=f"Completeness evaluation encountered an error: {err}",
                issues=[f"Evaluator error: {err}"],
                findings=[],
                metadata={"error": str(err)},
                duration_ms=elapsed_ms,
            )
