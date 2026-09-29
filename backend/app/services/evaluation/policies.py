from typing import Optional
from pydantic import BaseModel, Field

from backend.app.config import settings
from backend.app.services.evaluation.schemas import EvaluationMode


class EvaluationPolicy(BaseModel):
    """
    Configurable policy defining which evaluators run, verification strictness,
    warning tolerance, and revision limits.
    """
    mode: EvaluationMode = Field(default=EvaluationMode.STANDARD)
    enable_grounding: bool = Field(default=True)
    enable_completeness: bool = Field(default=True)
    enable_citation: bool = Field(default=True)
    enable_format: bool = Field(default=True)
    enable_safety: bool = Field(default=True)
    strict_mode: bool = Field(default=False)
    require_grounding_if_context: bool = Field(default=True)
    require_citation_if_sources: bool = Field(default=True)
    allow_warning_completion: bool = Field(default=True)
    auto_revise_on_fail: bool = Field(default=True)
    max_revision_attempts: int = Field(default=settings.MAX_REVISION_ATTEMPTS, ge=0, le=3)

    @classmethod
    def from_mode(
        cls,
        mode: Optional[str] = None,
        strict: bool = False,
        max_revisions: Optional[int] = None,
    ) -> "EvaluationPolicy":
        """
        Factory creating policy corresponding to mode string.
        """
        raw_mode = (mode or settings.EVALUATION_DEFAULT_MODE or "standard").lower().strip()
        revisions = max_revisions if max_revisions is not None else settings.MAX_REVISION_ATTEMPTS

        if raw_mode == EvaluationMode.OFF.value:
            return cls(
                mode=EvaluationMode.OFF,
                enable_grounding=False,
                enable_completeness=False,
                enable_citation=False,
                enable_format=False,
                enable_safety=False,
                strict_mode=False,
                allow_warning_completion=True,
                auto_revise_on_fail=False,
                max_revision_attempts=0,
            )

        elif raw_mode == EvaluationMode.BASIC.value:
            return cls(
                mode=EvaluationMode.BASIC,
                enable_grounding=False,
                enable_completeness=False,
                enable_citation=False,
                enable_format=True,
                enable_safety=True,
                strict_mode=strict,
                allow_warning_completion=not strict,
                auto_revise_on_fail=True,
                max_revision_attempts=revisions,
            )

        elif raw_mode == EvaluationMode.STRICT.value or strict:
            return cls(
                mode=EvaluationMode.STRICT,
                enable_grounding=True,
                enable_completeness=True,
                enable_citation=True,
                enable_format=True,
                enable_safety=True,
                strict_mode=True,
                require_grounding_if_context=True,
                require_citation_if_sources=True,
                allow_warning_completion=False,
                auto_revise_on_fail=True,
                max_revision_attempts=revisions,
            )

        else:  # Standard
            return cls(
                mode=EvaluationMode.STANDARD,
                enable_grounding=True,
                enable_completeness=True,
                enable_citation=True,
                enable_format=True,
                enable_safety=True,
                strict_mode=False,
                require_grounding_if_context=True,
                require_citation_if_sources=True,
                allow_warning_completion=True,
                auto_revise_on_fail=True,
                max_revision_attempts=revisions,
            )


def get_evaluation_policy(
    mode: Optional[str] = None,
    strict: bool = False,
    max_revisions: Optional[int] = None,
) -> EvaluationPolicy:
    """Convenience helper to obtain configured EvaluationPolicy."""
    return EvaluationPolicy.from_mode(mode=mode, strict=strict, max_revisions=max_revisions)

