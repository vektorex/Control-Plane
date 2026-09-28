from typing import Optional
from pydantic import BaseModel, Field


class FailurePolicy(BaseModel):
    """
    Configuration governing failure tolerance and continuation behavior across plan steps.
    """
    retrieval_required: bool = Field(
        default=False,
        description="If True, failure of any retrieval step immediately aborts execution.",
    )
    web_search_required: bool = Field(
        default=False,
        description="If True, failure of web search tool immediately aborts execution.",
    )
    continue_on_optional_failure: bool = Field(
        default=True,
        description="If True, execution continues with available context when an optional step fails.",
    )
    strict_mode: bool = Field(
        default=False,
        description="If True, any step failure causes execution to abort regardless of step requirement flags.",
    )
    max_retries: int = Field(
        default=0,
        ge=0,
        le=3,
        description="Maximum automatic retries per step before marking as failed.",
    )


def resolve_task_failure_policy(
    retrieval_required: bool = False,
    web_search_required: bool = False,
    strict_mode: bool = False,
) -> FailurePolicy:
    """
    Constructs a deterministic FailurePolicy based on task settings.
    """
    return FailurePolicy(
        retrieval_required=retrieval_required,
        web_search_required=web_search_required,
        continue_on_optional_failure=not strict_mode,
        strict_mode=strict_mode,
    )
