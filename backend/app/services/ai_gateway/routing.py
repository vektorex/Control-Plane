from typing import Any, Dict, List, Optional
from backend.app.core.logging import logger
from backend.app.services.ai_gateway.errors import (
    ModelNotFoundError,
    ModelNotAllowedError,
    CapabilityUnsupportedError,
)
from backend.app.services.ai_gateway.requests import GatewayRequest
from backend.app.services.models.base import ModelRequirements, ModelSelection
from backend.app.services.models.registry import default_model_registry
from backend.app.services.models.router import default_model_router, ModelRouter


class GatewayRouter:
    """
    Integrates AI Gateway requests with the existing ModelRouter.
    Ensures routing remains centralized without duplicating ranking logic.
    """

    def __init__(self, router: Optional[ModelRouter] = None):
        self._router = router or default_model_router

    def route_request(
        self,
        request: GatewayRequest,
        policy: Optional[Dict[str, Any]] = None,
    ) -> ModelSelection:
        """
        Route a GatewayRequest to the optimal or requested model and provider.
        If request.model is specified and not 'auto', performs validated manual selection.
        If 'auto', extracts ModelRequirements and invokes ModelRouter.route().
        """
        req_tools = bool(request.tools)
        req_stream = request.stream
        req_structured = bool(request.response_format)
        lat_pref = request.metadata.get("latency_preference", "balanced")
        cost_pref = request.metadata.get("cost_preference", "balanced")
        pref_prov = request.provider or request.metadata.get("preferred_provider")

        req_vision = bool(request.metadata.get("requires_vision")) or any(
            isinstance(m.get("content"), list)
            and any(isinstance(p, dict) and p.get("type") in ("image", "input_image") for p in m["content"])
            for m in request.messages
        )
        req_audio = bool(request.metadata.get("requires_audio")) or any(
            isinstance(m.get("content"), list)
            and any(isinstance(p, dict) and p.get("type") in ("audio", "audio_input") for p in m["content"])
            for m in request.messages
        )
        req_video = bool(request.metadata.get("requires_video")) or any(
            isinstance(m.get("content"), list)
            and any(isinstance(p, dict) and p.get("type") in ("video", "video_frame") for p in m["content"])
            for m in request.messages
        )
        req_multimodal = req_vision or req_audio or req_video or bool(request.metadata.get("requires_multimodal"))

        requirements = ModelRequirements(
            requires_tools=req_tools,
            requires_streaming=req_stream,
            requires_structured_output=req_structured,
            requires_vision=req_vision,
            requires_image_input=req_vision,
            requires_audio=req_audio,
            requires_video=req_video,
            requires_multimodal=req_multimodal,
            latency_preference=lat_pref,
            cost_preference=cost_pref,
            preferred_provider=pref_prov,
            preferred_model=request.model if request.model != "auto" else None,
        )

        # 1. Manual model selection
        if request.model and request.model != "auto":
            try:
                selection = self._router.validate_manual_selection(
                    model_id=request.model,
                    provider=request.provider,
                    requirements=requirements,
                )
                return selection
            except Exception as e:
                logger.warning(f"[GatewayRouter] Manual model validation failed: {e}")
                # If model is not registered, check if provider registry can handle it or raise
                raise ModelNotFoundError(f"Model selection '{request.model}' is invalid: {e}")

        # 2. Automatic routing
        selection = self._router.route(requirements=requirements)
        return selection
