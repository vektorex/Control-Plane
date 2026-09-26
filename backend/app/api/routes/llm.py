import json
from typing import AsyncIterator
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from backend.app.core.logging import logger
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
    factory: LLMProviderFactory = Depends(get_llm_factory),
) -> LLMGenerateResponse:
    """
    Execute standard LLM generation through the provider-agnostic abstraction layer.
    Validates request against schema, routes to the matching provider adapter,
    and returns normalized content and token metrics.
    """
    logger.info(
        f"[LLMRoute] Received generation request for model '{request.model}' "
        f"with {len(request.messages)} message(s)."
    )
    provider = factory.get_provider_for_model(request.model)
    return await provider.generate(request)


@router.post("/generate/stream")
async def generate_completion_stream(
    request: LLMGenerateRequest,
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
