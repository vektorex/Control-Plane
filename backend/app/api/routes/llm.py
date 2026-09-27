import json
from typing import AsyncIterator
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from backend.app.core.auth import get_current_user
from backend.app.core.logging import logger
from backend.app.db.models.user import User
from backend.app.schemas.llm import (
    LLMGenerateRequest,
    LLMGenerateResponse,
    LLMStreamChunk,
)
from backend.app.services.llm.factory import LLMProviderFactory, get_llm_factory

router = APIRouter(prefix="/llm", tags=["LLM Orchestration"])


@router.post("/generate", response_model=LLMGenerateResponse)
async def generate_completion(
    request: LLMGenerateRequest,
    user: User = Depends(get_current_user),
    factory: LLMProviderFactory = Depends(get_llm_factory),
) -> LLMGenerateResponse:
    """
    Execute standard LLM generation through the provider-agnostic abstraction layer.
    Validates request against schema, routes to the matching provider adapter,
    and returns normalized content and token metrics.
    """
    logger.info(
        f"[LLMRoute] Received generation request for model '{request.model}' "
        f"from user {user.id} with {len(request.messages)} message(s)."
    )
    provider = factory.get_provider_for_model(request.model)
    return await provider.generate(request)


@router.post("/generate/stream")
async def generate_completion_stream(
    request: LLMGenerateRequest,
    user: User = Depends(get_current_user),
    factory: LLMProviderFactory = Depends(get_llm_factory),
):

    """
    Execute streaming LLM generation via Server-Sent Events (SSE).
    Yields JSON event payloads followed by a terminal [DONE] event.
    """
    logger.info(
        f"[LLMRoute] Received streaming generation request for model '{request.model}'."
    )
    provider = factory.get_provider_for_model(request.model)

    async def sse_event_stream() -> AsyncIterator[str]:
        try:
            async for chunk in provider.generate_stream(request):
                payload = chunk.model_dump(mode="json")
                yield f"data: {json.dumps(payload)}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            logger.error(f"[LLMRoute] Streaming error: {str(e)}")
            error_payload = {
                "error": {
                    "code": getattr(e, "code", "STREAM_ERROR"),
                    "message": str(e),
                }
            }
            yield f"data: {json.dumps(error_payload)}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        sse_event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Content-Type": "text/event-stream; charset=utf-8",
        },
    )
