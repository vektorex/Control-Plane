from typing import Any, Dict, Optional
from backend.app.db.models.run import Run
from backend.app.services.replay.schemas import FailureInsights

# Mapping normalized error codes or keywords to failure categories
CATEGORY_MAP = {
    "PROVIDER_TIMEOUT": ("provider", "Generation", "Verify AI provider availability or increase timeout setting."),
    "GATEWAY_TIMEOUT": ("provider", "Gateway Routing", "AI Gateway timed out connecting to model provider."),
    "PROVIDER_RATE_LIMIT": ("provider", "Gateway Routing", "Rate limited by upstream AI provider. Replay after cooldown or try another provider."),
    "PROVIDER_AUTH_ERROR": ("provider", "Gateway Routing", "Provider authentication failed. Verify provider configuration."),
    "ALL_FALLBACKS_FAILED": ("model", "Model Selection", "All candidate models failed. Replay with another compatible model or provider."),
    "MODEL_UNSUPPORTED": ("model", "Model Selection", "Requested model is unsupported or unauthorized in workspace policy."),
    "RETRIEVAL_ERROR": ("retrieval", "Knowledge Retrieval", "Knowledge retrieval failed. Check document store and vector indexes."),
    "TOOL_EXECUTION_ERROR": ("tool", "Tool Execution", "Tool execution failed. Verify tool parameters and connectivity."),
    "CONNECTOR_ERROR": ("connector", "Connector Integration", "External connector failed. Re-authenticate or verify connector permissions."),
    "WORKFLOW_ERROR": ("workflow", "Workflow Pipeline", "Workflow step execution failed. Check step inputs and bindings."),
    "EVALUATION_FAILED": ("evaluation", "Evaluation & Verification", "Verification evaluation failed strict criteria."),
    "AUTHORIZATION_REQUIRED": ("authorization", "Security Gating", "Operation requires authorization or human approval."),
    "FORBIDDEN": ("authorization", "Security Boundary", "Workspace permission denied."),
    "STEP_EXECUTION_ERROR": ("tool", "Step Execution", "Orchestration step failed. Review step error logs."),
    "SIDE_EFFECT_BLOCKED": ("authorization", "Safety Policy", "External write action blocked. Provide fresh human approval to execute live."),
}


class ErrorAnalysisService:
    """
    Factual failure classifier and diagnostic insight generator for execution runs.
    Uses normalized error codes, pipeline stages, and telemetry without subjective rankings.
    """

    @staticmethod
    def classify_failure(error_code: Optional[str], error_message: Optional[str] = None) -> str:
        """Classifies an error into a standardized failure category."""
        if not error_code and not error_message:
            return "unknown"

        code_upper = (error_code or "").upper()
        msg_upper = (error_message or "").upper()

        if code_upper in CATEGORY_MAP:
            return CATEGORY_MAP[code_upper][0]

        # Heuristic classification based on normalized prefixes / keywords
        if "TIMEOUT" in code_upper or "TIMEOUT" in msg_upper:
            return "timeout"
        if "PROVIDER" in code_upper:
            return "provider"
        if "MODEL" in code_upper:
            return "model"
        if "RETRIEV" in code_upper or "RETRIEV" in msg_upper:
            return "retrieval"
        if "TOOL" in code_upper or "TOOL" in msg_upper:
            return "tool"
        if "CONNECTOR" in code_upper or "GITHUB" in code_upper:
            return "connector"
        if "WORKFLOW" in code_upper:
            return "workflow"
        if "EVALUAT" in code_upper:
            return "evaluation"
        if "AUTH" in code_upper or "FORBIDDEN" in code_upper or "PERMISSION" in code_upper:
            return "authorization"
        if "VALIDAT" in code_upper or "CONFIG" in code_upper:
            return "configuration"

        return "unknown"

    @staticmethod
    def analyze_failure(run: Run) -> FailureInsights:
        """Alias for generate_insights, ensuring non-null FailureInsights."""
        insights = ErrorAnalysisService.generate_insights(run)
        if insights:
            return insights
        return FailureInsights(
            failure_code="RUN_FAILED",
            stage="Execution",
            provider=getattr(run, "model_provider", None),
            model=getattr(run, "model_name", None) or getattr(run, "final_model", None),
            retry_attempts=getattr(run, "repair_count", 0) or 0,
            fallback_attempts=getattr(run, "fallback_attempts", 0) or 0,
            duration_ms=getattr(run, "latency_ms", None),
            suggested_action="Review trace timeline and execution error logs.",
        )

    @staticmethod
    def generate_insights(run: Run) -> Optional[FailureInsights]:
        """Generates factual diagnostic failure insights for a failed Run."""
        status_val = run.status.value if hasattr(run.status, "value") else str(run.status or "")
        if status_val.lower() not in ("failed", "cancelled") and not run.error_message:
            return None

        # Extract normalized error info
        failed_step = run.failed_step or {}
        raw_msg = run.error_message or failed_step.get("error_message") or "Execution failed"
        raw_code = failed_step.get("error_code")

        if not raw_code:
            msg_upper = raw_msg.upper()
            if "TIMEOUT" in msg_upper:
                raw_code = "PROVIDER_TIMEOUT"
            elif "RATE" in msg_upper and "LIMIT" in msg_upper:
                raw_code = "PROVIDER_RATE_LIMIT"
            elif "AUTH" in msg_upper:
                raw_code = "PROVIDER_AUTH_ERROR"
            else:
                raw_code = "RUN_FAILED"

        category = ErrorAnalysisService.classify_failure(raw_code, raw_msg)
        stage = "Execution"
        suggested_action = "Review trace timeline and error logs."

        if raw_code.upper() in CATEGORY_MAP:
            _, stage, suggested_action = CATEGORY_MAP[raw_code.upper()]
        elif category == "timeout":
            stage = "Generation"
            suggested_action = "Execution timed out. Replay with another compatible model or increased timeout."
        elif category == "provider":
            stage = "Generation"
            suggested_action = "Replay with another compatible provider or check API quotas."
        elif category == "model":
            stage = "Model Selection"
            suggested_action = "Replay with another compatible model."
        elif category == "retrieval":
            stage = "Retrieval"
            suggested_action = "Verify document ingestion status or adjust retrieval strategy."
        elif category == "tool":
            stage = "Tool Execution"
            suggested_action = "Verify tool availability and input schema."
        elif category == "authorization":
            stage = "Safety & Approval"
            suggested_action = "Obtain fresh human approval for external actions."

        retry_count = getattr(run, "repair_count", 0) or 0
        fb_attempts = getattr(run, "fallback_attempts", 0) or 0

        return FailureInsights(
            failure_code=raw_code,
            stage=stage,
            provider=getattr(run, "model_provider", None),
            model=getattr(run, "model_name", None) or getattr(run, "final_model", None),
            retry_attempts=retry_count,
            fallback_attempts=fb_attempts,
            duration_ms=getattr(run, "latency_ms", None),
            suggested_action=suggested_action,
        )

