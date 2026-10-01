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
    TokenUsage,
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
    Execute standard LLM generation through the unified AI Gateway runtime.
    Validates request against schema, enforces policies and limits,
    and returns normalized content and token metrics.
    """
    logger.info(
        f"[LLMRoute] Received generation request for model '{request.model}' "
        f"from user {user.id} with {len(request.messages)} message(s)."
    )
    from backend.app.services.ai_gateway import GatewayRequest, default_ai_gateway

    gw_req = GatewayRequest(
        model=request.model,
        messages=[{"role": m.role, "content": m.content} for m in request.messages],
        temperature=request.temperature,
        max_tokens=request.max_tokens,
        metadata={"user_id": str(user.id)},
    )
    res = await default_ai_gateway.execute(gw_req)
    return LLMGenerateResponse(
        content=res.content,
        model=res.model,
        provider=res.provider,
        finish_reason=res.finish_reason,
        usage=TokenUsage(
            input_tokens=res.usage.input_tokens,
            output_tokens=res.usage.output_tokens,
            total_tokens=res.usage.total_tokens,
        ),
    )


@router.post("/generate/stream")
async def generate_completion_stream(
    request: LLMGenerateRequest,
    user: User = Depends(get_current_user),
    factory: LLMProviderFactory = Depends(get_llm_factory),
):
    """
    Execute streaming LLM generation via Server-Sent Events (SSE) through AI Gateway.
    Yields JSON event payloads followed by a terminal [DONE] event.
    """
    logger.info(
        f"[LLMRoute] Received streaming generation request for model '{request.model}'."
    )
    from backend.app.services.ai_gateway import GatewayRequest, default_ai_gateway

    gw_req = GatewayRequest(
        model=request.model,
        messages=[{"role": m.role, "content": m.content} for m in request.messages],
        temperature=request.temperature,
        max_tokens=request.max_tokens,
        stream=True,
        metadata={"user_id": str(user.id)},
    )

    async def sse_event_stream() -> AsyncIterator[str]:
        try:
            async for event in default_ai_gateway.execute_stream(gw_req):
                if event.get("type") == "delta":
                    chunk = LLMStreamChunk(
                        content=event.get("content", ""),
                        model=request.model,
                        is_finished=False,
                    )
                    yield f"data: {json.dumps(chunk.model_dump(mode='json'))}\n\n"
                elif event.get("type") == "completed":
                    chunk = LLMStreamChunk(
                        content="",
                        model=request.model,
                        is_finished=True,
                        finish_reason=event.get("finish_reason", "stop"),
                    )
                    yield f"data: {json.dumps(chunk.model_dump(mode='json'))}\n\n"
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
