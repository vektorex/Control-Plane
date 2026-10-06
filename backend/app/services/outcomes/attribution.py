"""
Outcome Attribution and AI Attribution Analyzer for Step 43:
AI Outcome Intelligence & Work Impact Layer.
Ensures evidence-backed attribution and strict causal safeguards.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import json

from backend.app.core.logging import logger
from backend.app.services.ai_gateway import AIGateway, GatewayRequest, default_ai_gateway
from backend.app.services.outcomes.errors import CausalityClaimForbiddenError
from backend.app.services.outcomes.models import OutcomeAttribution
from backend.app.services.outcomes.policies import OutcomePolicyEngine
from backend.app.services.outcomes.registry import (
    AttributionConfidence,
    AttributionSource,
    AttributionType,
)


class DeterministicAttributionBuilder:
    """Builds factual, evidence-backed attribution objects."""

    @classmethod
    def build_attribution(
        cls,
        outcome_id: str,
        resource_type: str,
        resource_id: str,
        relationship: str = "contributes_to",
        evidence_ids: Optional[List[str]] = None,
        is_direct: bool = False,
    ) -> Dict[str, Any]:
        return {
            "outcome_id": outcome_id,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "relationship": relationship,
            "attribution_type": AttributionType.DIRECT if is_direct else AttributionType.CONTRIBUTING,
            "evidence_ids": evidence_ids or [],
            "source": AttributionSource.OBSERVED if is_direct else AttributionSource.DETERMINISTIC,
        }


class OutcomeAttributionAnalyzer:
    """
    Analyzes execution traces, evidence, artifacts, and decisions to propose attribution links.
    All AI-derived attributions are strictly labeled AI_GENERATED_ATTRIBUTION and never auto-verified.
    """

    def __init__(self, ai_gateway: Optional[AIGateway] = None):
        self.gateway = ai_gateway or default_ai_gateway

    @classmethod
    def label_ai_attribution(
        cls, suggested_type: str, explanation: str
    ) -> Dict[str, Any]:
        return {
            "attribution_type": suggested_type,
            "explanation": explanation,
            "source": AttributionSource.AI_GENERATED,
            "confidence": "estimated",
        }

    @staticmethod
    def build_deterministic_attribution(
        outcome_id: str,
        resource_type: str,
        resource_id: str,
        evidence_ids: List[str],
        explanation: str,
        attribution_type: str = AttributionType.CONTRIBUTING.value,
        has_causal_evidence: bool = False,
    ) -> OutcomeAttribution:
        """
        Creates a deterministic, evidence-backed attribution record.
        """
        OutcomePolicyEngine.validate_attribution_safety(
            attribution_type=attribution_type,
            attribution_source=AttributionSource.DETERMINISTIC.value,
            has_causal_evidence=has_causal_evidence,
            explanation=explanation,
        )

        return OutcomeAttribution(
            outcome_id=outcome_id,
            resource_type=resource_type,
            resource_id=resource_id,
            attribution_type=attribution_type,
            evidence_ids=evidence_ids or [],
            explanation=explanation,
            attribution_source=AttributionSource.DETERMINISTIC.value,
            attribution_confidence=AttributionConfidence.OBSERVED.value if has_causal_evidence else AttributionConfidence.INFERRED.value,
            created_at=datetime.now(timezone.utc),
        )

    async def analyze_contribution_with_ai(
        self,
        outcome_name: str,
        outcome_type: str,
        work_summary: Dict[str, Any],
        evidence_snippets: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Invokes AIGateway to suggest potential contributing factors, blockers, or dependencies.
        Labels results with AI_GENERATED_ATTRIBUTION and enforces non-causal language.
        """
        prompt = (
            f"Analyze work execution contributing to the intended outcome.\n"
            f"Outcome: {outcome_name} (type: {outcome_type})\n"
            f"Work context: {json.dumps(work_summary)}\n"
            f"Evidence records: {json.dumps(evidence_snippets)}\n\n"
            "Task: Identify which resources contributed or blocked the outcome.\n"
            "Constraints:\n"
            "1. NEVER use the word 'caused' or claim direct causation without deterministic proof.\n"
            "2. Label relationship as 'contributing', 'supporting', or 'blocking'.\n"
            "3. Return a JSON array of objects: [{'resource_type': str, 'resource_id': str, 'attribution_type': str, 'explanation': str}]."
        )

        suggestions: List[Dict[str, Any]] = []

        try:
            req = GatewayRequest(
                prompt=prompt,
                model_preference="fast",
                temperature=0.1,
                max_tokens=600,
            )
            response = await self.gateway.execute(req)
            raw_text = response.text or ""
            # Parse JSON from response
            import re
            json_match = re.search(r"\[.*\]", raw_text, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group(0))
                for item in parsed:
                    explanation = item.get("explanation", "").replace("caused", "contributed to")
                    att_type = item.get("attribution_type", "contributing")
                    if att_type == AttributionType.DIRECT.value:
                        att_type = AttributionType.CONTRIBUTING.value

                    suggestions.append({
                        "resource_type": item.get("resource_type", "Unknown"),
                        "resource_id": item.get("resource_id", "Unknown"),
                        "attribution_type": att_type,
                        "explanation": f"[AI Assisted] {explanation}",
                        "attribution_source": AttributionSource.AI_GENERATED_ATTRIBUTION.value,
                        "attribution_confidence": AttributionConfidence.INFERRED.value,
                    })
        except Exception as e:
            logger.warning(f"AI Gateway attribution analysis fallback triggered: {e}")
            # Fallback heuristic analysis without LLM
            if work_summary.get("resources"):
                for r in work_summary["resources"][:3]:
                    suggestions.append({
                        "resource_type": r.get("type", "Task"),
                        "resource_id": str(r.get("id", "")),
                        "attribution_type": AttributionType.CONTRIBUTING.value,
                        "explanation": f"Resource executed in context of outcome '{outcome_name}'.",
                        "attribution_source": AttributionSource.AI_GENERATED_ATTRIBUTION.value,
                        "attribution_confidence": AttributionConfidence.INFERRED.value,
                    })

        return suggestions
