"""
Vision Analysis and Image Understanding Service for Step 30: Multimodal AI.
Directs vision reasoning through the centralized AI Gateway.
Supports explicit fallback to structured text descriptions when downstream models lack vision.
"""
import base64
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.app.core.logging import logger
from backend.app.services.ai_gateway.gateway import default_ai_gateway, AIGateway
from backend.app.services.ai_gateway.requests import GatewayRequest
from backend.app.services.models.capabilities import ModelCapability


class VisionAnalysisResult(BaseModel):
    summary: str
    analysis: str
    visual_evidence: List[Dict[str, Any]] = Field(default_factory=list)
    model_used: Optional[str] = None
    fallback_used: bool = False
    fallback_details: Optional[Dict[str, Any]] = None


class VisionService:
    """
    Coordinates image and screenshot understanding via the centralized AI Gateway.
    Never bypasses the AI Gateway or uses direct hardcoded commercial APIs.
    """

    def __init__(self, gateway: Optional[AIGateway] = None):
        self.gateway = gateway or default_ai_gateway

    async def analyze_image(
        self,
        image_bytes: bytes,
        mime_type: str,
        instruction: str = "Analyze this image, describe its core visual elements, and highlight key details.",
        artifact_id: Optional[str] = None,
        workspace_id: Optional[str] = None,
        model_preference: Optional[str] = None,
    ) -> VisionAnalysisResult:
        """
        Executes vision analysis through the AI Gateway.
        Translates raw image bytes into normalized GatewayRequest multimodal messages.
        """
        b64_data = base64.b64encode(image_bytes).decode("utf-8")
        data_url = f"data:{mime_type};base64,{b64_data}"

        content_parts = [
            {"type": "text", "text": instruction},
            {
                "type": "image",
                "artifact_id": str(artifact_id) if artifact_id else "ephemeral_image",
                "image_url": data_url,
                "mime_type": mime_type,
            },
        ]

        messages = [
            {
                "role": "user",
                "content": content_parts,
            }
        ]

        # Target a model that advertises vision capability
        target_model = model_preference or "auto"
        request = GatewayRequest(
            model=target_model,
            messages=messages,
            workspace_id=workspace_id,
            metadata={
                "task_type": "vision_analysis",
                "required_capabilities": [ModelCapability.VISION.value],
            },
        )

        try:
            resp = await self.gateway.execute(request)
            text_out = resp.content or ""

            # Record visual evidence grounded in this analysis
            evidence = [
                {
                    "artifact_id": str(artifact_id) if artifact_id else None,
                    "media_type": "image",
                    "source_text": text_out[:300],
                }
            ]

            return VisionAnalysisResult(
                summary=text_out[:200] if len(text_out) > 200 else text_out,
                analysis=text_out,
                visual_evidence=evidence,
                model_used=resp.model,
                fallback_used=False,
            )
        except Exception as e:
            logger.warning(f"[VisionService] Primary vision request failed or unsupported: {e}. Executing controlled fallback.")
            return await self._fallback_description(instruction, artifact_id, str(e))

    async def _fallback_description(
        self,
        instruction: str,
        artifact_id: Optional[str],
        error_reason: str,
    ) -> VisionAnalysisResult:
        """
        Explicit structured description fallback when the model or provider cannot ingest images.
        Clearly tags the result as a generated fallback description.
        """
        fallback_text = (
            f"[Structured Image Description Fallback]\n"
            f"The original image (artifact: {artifact_id or 'unknown'}) could not be inspected directly "
            f"by the requested vision model ({error_reason}).\n"
            f"Context retained: {instruction}"
        )
        return VisionAnalysisResult(
            summary="Image description generated via fallback mechanism.",
            analysis=fallback_text,
            visual_evidence=[],
            model_used="fallback-description-generator",
            fallback_used=True,
            fallback_details={"reason": error_reason, "artifact_id": artifact_id},
        )
