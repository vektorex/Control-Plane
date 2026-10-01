import re
from typing import Dict, List, Optional, Set


class ConfidenceCalculator:
    """
    Evaluates confidence metrics for deterministic and hybrid task analysis.
    Prevents unnecessary LLM calls when deterministic signals are distinct and clear.
    """

    DEFAULT_THRESHOLD: float = 0.8

    @classmethod
    def evaluate_signal_confidence(
        cls,
        matched_signals: List[str],
        total_tokens: int,
        conflicting_signals: Optional[List[str]] = None,
    ) -> float:
        """
        Calculates confidence score based on signal strength and ambiguity.
        """
        if not matched_signals:
            return 0.4

        base_score = 0.75
        # Boost confidence for each distinct unambiguous pattern match
        bonus = min(0.20, len(matched_signals) * 0.10)
        score = base_score + bonus

        # Penalty if conflicting requirements detected
        if conflicting_signals:
            score -= min(0.35, len(conflicting_signals) * 0.15)

        return max(0.1, min(1.0, round(score, 2)))

    @classmethod
    def is_confidence_sufficient(
        cls,
        confidence: float,
        threshold: Optional[float] = None,
    ) -> bool:
        """
        Determines whether confidence meets the bar to safely skip LLM analysis.
        """
        limit = threshold if threshold is not None else cls.DEFAULT_THRESHOLD
        return confidence >= limit
