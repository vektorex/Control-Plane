import asyncio
import time
import uuid
from typing import Any, AsyncIterator, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.logging import logger
from backend.app.services.ai_gateway.adapters import ModelProviderAdapter
from backend.app.services.ai_gateway.errors import (
    AllFallbacksFailedError,
    CircuitOpenError,
    GatewayError,
    ModelNotFoundError,
    ModelTimeoutError,
    ProviderTimeoutError,
    ProviderUnavailableError,
)
from backend.app.services.ai_gateway.fallback import FallbackEngine, MAX_MODEL_FALLBACKS
from backend.app.services.ai_gateway.health import (
    CircuitBreaker,
    ModelHealthService,
    default_health_service,
)
from backend.app.services.ai_gateway.limits import (
    ConcurrencyLimiter,
    RetryPolicy,
    default_concurrency_limiter,
    MAX_MODEL_RETRIES,
    MODEL_REQUEST_TIMEOUT_SECONDS,
)
from backend.app.services.ai_gateway.policies import WorkspaceModelPolicyManager
from backend.app.services.ai_gateway.providers import ProviderRegistry, default_provider_registry
from backend.app.services.ai_gateway.requests import GatewayRequest
from backend.app.services.ai_gateway.responses import GatewayResponse, GatewayUsage
from backend.app.services.ai_gateway.routing import GatewayRouter
from backend.app.services.ai_gateway.streaming import NormalizedStreamEvent
from backend.app.services.models.base import FallbackCandidate, ModelSelection
from backend.app.services.models.registry import default_model_registry
from backend.app.services.models.router import default_model_router
from backend.app.services.observability.cost import CostCalculator
from backend.app.services.observability.events import TraceEventStatus, TraceEventType


class ModelResponseCache:
    """
    In-memory Response Cache abstraction.
    Disabled globally by default for Step 19, but provides a clean contract
    for future Redis / distributed caching implementations.
    """

    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.enabled: bool = False

    def get(self, key: str) -> Optional[GatewayResponse]:
        if not self.enabled:
            return None
        entry = self._cache.get(key)
        if entry and entry["expires_at"] > time.time():
            return entry["response"]
        return None

    def set(self, key: str, response: GatewayResponse, ttl_seconds: int = 300) -> None:
        if not self.enabled:
            return
        self._cache[key] = {
            "response": response,
            "expires_at": time.time() + ttl_seconds,
        }

    def delete(self, key: str) -> None:
        self._cache.pop(key, None)

    def clear(self) -> None:
        self._cache.clear()


class AIGateway:
    """
    Production-grade AI Gateway serving as the single runtime entry point
    for all model executions (Tasks, Workflows, Planners, Evaluator, Revision).
    """

    def __init__(
        self,
        providers: Optional[ProviderRegistry] = None,
        router: Optional[GatewayRouter] = None,
        health_service: Optional[ModelHealthService] = None,
        concurrency_limiter: Optional[ConcurrencyLimiter] = None,
        cost_calculator: Optional[CostCalculator] = None,
    ):
        self.providers = providers or default_provider_registry
        self.router = router or GatewayRouter(default_model_router)
        self.health = health_service or default_health_service
        self.concurrency = concurrency_limiter or default_concurrency_limiter
        self.costs = cost_calculator or CostCalculator(default_model_registry)
        self.cache = ModelResponseCache()

    def _record_trace(
        self,
        run_id_val: Optional[str],
        workspace_id: Optional[str],
        event_type: Any,
        status: Any,
        metadata: Dict[str, Any],
    ) -> None:
        """Safely records a trace event without leaking secrets or throwing exceptions."""
        if not run_id_val:
            return
        try:
            from backend.app.services.observability.tracer import ExecutionTracer
            r_uuid = uuid.UUID(str(run_id_val))
            w_uuid = uuid.UUID(str(workspace_id)) if workspace_id else r_uuid
            t = ExecutionTracer(run_id=r_uuid, workspace_id=w_uuid)
            t.record_event(event_type=event_type, status=status, metadata=metadata)
        except Exception:
            pass

    async def preview(
        self, request: GatewayRequest, db: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """
        Generate a routing preview showing selected model, provider, fallback candidates,
        and capability compatibility WITHOUT executing a model call.
        """
        policy = await WorkspaceModelPolicyManager.get_policy(db, request.workspace_id)
        selection = self.router.route_request(request, policy=policy)

        # Check candidate safety
        safe_fallbacks = FallbackEngine.resolve_fallback_candidates(
            candidates=selection.fallback_candidates,
            original_request=request,
            workspace_policy=policy,
        )

        return {
            "selected_model": selection.model_id,
            "selected_provider": selection.provider,
            "display_name": selection.display_name,
            "routing_reason": selection.reason,
            "satisfied_requirements": selection.satisfied_requirements,
            "fallback_candidates": [
                {
                    "model_id": fb.model_id,
                    "provider": fb.provider,
                    "display_name": fb.display_name,
                    "reason": fb.reason,
                }
                for fb in safe_fallbacks
            ],
            "capabilities": {
                "streaming": request.stream,
                "tools": bool(request.tools),
                "structured_output": bool(request.response_format),
            },
            "policy_compliant": True,
        }

    async def test(
        self, request: GatewayRequest, db: Optional[AsyncSession] = None
    ) -> GatewayResponse:
        """Execute a simple diagnostic prompt through the real gateway pipeline."""
        return await self.execute(request, db=db)

    async def execute(
        self,
        request: GatewayRequest,
        db: Optional[AsyncSession] = None,
        run_id: Optional[str] = None,
    ) -> GatewayResponse:
        """
        Execute standard completion request through the full AI Gateway pipeline.
        Enforces policies, routing, fallbacks, retries, concurrency, and observability.
        """
        req_id = request.metadata.get("request_id") or str(uuid.uuid4())
        workspace_id = request.workspace_id
        run_id_val = run_id or request.metadata.get("run_id")

        # 1. Fetch & Validate Workspace Model Policy
        policy = await WorkspaceModelPolicyManager.get_policy(db, workspace_id)

        # 2. Centralized Model Routing
        selection = self.router.route_request(request, policy=policy)
        resolved_provider = selection.provider
        resolved_model = selection.model_id

        # Server-side policy check on resolved target
        WorkspaceModelPolicyManager.validate_request_policy(
            request, policy, resolved_provider=resolved_provider
        )

        # 3. Check Optional Cache
        cache_key = request.get_fingerprint()
        cached_resp = self.cache.get(cache_key)
        if cached_resp:
            logger.info(f"[AIGateway] Cache hit for fingerprint '{cache_key[:8]}'")
            return cached_resp

        # 4. Prepare Candidate Queue: Primary + Safe Fallbacks
        candidates: List[tuple[str, str]] = [(resolved_provider, resolved_model)]
        if policy.get("fallback_enabled", True):
            safe_fallbacks = FallbackEngine.resolve_fallback_candidates(
                candidates=selection.fallback_candidates,
                original_request=request,
                workspace_policy=policy,
            )
            for fb in safe_fallbacks:
                candidates.append((fb.provider, fb.model_id))

        # 5. Telemetry: Gateway Request Started
        self._record_trace(
            run_id_val=run_id_val,
            workspace_id=workspace_id,
            event_type=TraceEventType.GATEWAY_REQUEST_STARTED,
            status=TraceEventStatus.STARTED,
            metadata={
                "gateway_request_id": req_id,
                "model": resolved_model,
                "provider": resolved_provider,
                "stream": False,
                "routing_reason": selection.reason,
            },
        )

        # 6. Concurrency Acquisition
        ws_concurrency_limit = policy.get("max_concurrent_requests", 10)
        await self.concurrency.acquire(workspace_id=workspace_id, limit=ws_concurrency_limit)

        last_error: Optional[Exception] = None
        fallback_attempt = 0

        try:
            for idx, (cand_prov, cand_model) in enumerate(candidates):
                circuit_key = f"{cand_prov}/{cand_model}"

                # Circuit breaker check
                if not self.health.circuit_breaker.can_execute(circuit_key):
                    logger.warning(
                        f"[AIGateway] Skipping candidate '{cand_model}' ({cand_prov}): circuit is OPEN."
                    )
                    continue

                if idx > 0:
                    fallback_attempt = idx
                    logger.info(
                        f"[AIGateway] Engaging fallback {idx}: '{cand_model}' ({cand_prov})"
                    )
                    self._record_trace(
                        run_id_val=run_id_val,
                        workspace_id=workspace_id,
                        event_type=TraceEventType.GATEWAY_FALLBACK,
                        status=TraceEventStatus.COMPLETED,
                        metadata={
                            "gateway_request_id": req_id,
                            "from_model": resolved_model,
                            "to_model": cand_model,
                            "provider": cand_prov,
                            "fallback_attempt": fallback_attempt,
                        },
                    )

                # Attempt execution with retries
                cand_request = request.model_copy(
                    update={"model": cand_model, "provider": cand_prov}
                )
                try:
                    response = await self._execute_with_retry(
                        cand_request, cand_prov, cand_model, run_id_val=run_id_val
                    )

                    # Calculate Pricing
                    estimated_cost = self.costs.calculate_generation_cost(
                        model_id=cand_model,
                        provider=cand_prov,
                        input_tokens=response.usage.input_tokens,
                        output_tokens=response.usage.output_tokens,
                    )
                    response.usage.estimated_cost = estimated_cost

                    # Telemetry: Completed
                    self._record_trace(
                        run_id_val=run_id_val,
                        workspace_id=workspace_id,
                        event_type=TraceEventType.GATEWAY_REQUEST_COMPLETED,
                        status=TraceEventStatus.COMPLETED,
                        metadata={
                            "gateway_request_id": req_id,
                            "model": cand_model,
                            "provider": cand_prov,
                            "fallback_attempt": fallback_attempt,
                            "total_tokens": response.usage.total_tokens,
                            "estimated_cost": estimated_cost,
                            "latency_ms": response.latency_ms,
                        },
                    )

                    # Cache successful result
                    self.cache.set(cache_key, response)
                    return response

                except Exception as cand_exc:
                    last_error = cand_exc
                    logger.warning(
                        f"[AIGateway] Candidate '{cand_model}' ({cand_prov}) failed: {cand_exc}. "
                        f"Remaining candidates: {len(candidates) - idx - 1}"
                    )
                    if not FallbackEngine.is_eligible_for_fallback(cand_exc):
                        # Non-transient errors (e.g. policy denial) do not fall back
                        raise cand_exc

            # If all candidates exhausted
            self._record_trace(
                run_id_val=run_id_val,
                workspace_id=workspace_id,
                event_type=TraceEventType.GATEWAY_FAILED,
                status=TraceEventStatus.FAILED,
                metadata={
                    "gateway_request_id": req_id,
                    "error": str(last_error),
                },
            )
            if len(candidates) == 1 and last_error:
                raise last_error
            raise AllFallbacksFailedError(
                f"All model candidates failed for request. Last error: {last_error}"
            )

        finally:
            self.concurrency.release(workspace_id=workspace_id)

    async def _execute_with_retry(
        self,
        request: GatewayRequest,
        provider_id: str,
        model_id: str,
        run_id_val: Optional[str] = None,
    ) -> GatewayResponse:
        """Execute request on adapter with bounded exponential backoff retries."""
        adapter = self.providers.get(provider_id)
        timeout_sec = (request.timeout_ms / 1000.0) if request.timeout_ms else MODEL_REQUEST_TIMEOUT_SECONDS

        for attempt in range(1, MAX_MODEL_RETRIES + 2):
            start_t = time.perf_counter()
            try:
                # Bounded execution with timeout
                response = await asyncio.wait_for(
                    adapter.generate(request), timeout=timeout_sec
                )
                lat_ms = round((time.perf_counter() - start_t) * 1000.0, 2)
                self.health.record_request_success(provider_id, model_id, lat_ms)
                return response

            except asyncio.TimeoutError:
                lat_ms = round((time.perf_counter() - start_t) * 1000.0, 2)
                self.health.record_request_failure(
                    provider_id, model_id, "Request timeout", is_timeout=True
                )
                self._record_trace(
                    run_id_val=run_id_val,
                    workspace_id=request.workspace_id,
                    event_type=TraceEventType.GATEWAY_TIMEOUT,
                    status=TraceEventStatus.FAILED,
                    metadata={"provider": provider_id, "model": model_id, "attempt": attempt},
                )
                raise ProviderTimeoutError(
                    f"Provider '{provider_id}' timed out after {timeout_sec}s."
                )

            except Exception as exc:
                lat_ms = round((time.perf_counter() - start_t) * 1000.0, 2)
                self.health.record_request_failure(provider_id, model_id, str(exc))

                if attempt <= MAX_MODEL_RETRIES and RetryPolicy.is_retryable(exc):
                    delay = RetryPolicy.get_backoff(attempt)
                    logger.warning(
                        f"[AIGateway] Retryable error on '{model_id}' ({provider_id}): {exc}. "
                        f"Retrying in {delay}s (attempt {attempt}/{MAX_MODEL_RETRIES})..."
                    )
                    self._record_trace(
                        run_id_val=run_id_val,
                        workspace_id=request.workspace_id,
                        event_type=TraceEventType.GATEWAY_RETRY,
                        status=TraceEventStatus.STARTED,
                        metadata={"provider": provider_id, "model": model_id, "attempt": attempt},
                    )
                    await asyncio.sleep(delay)
                    continue

                raise exc

    async def execute_stream(
        self,
        request: GatewayRequest,
        db: Optional[AsyncSession] = None,
        run_id: Optional[str] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Execute streaming generation through the normalized gateway pipeline.
        Yields normalized stream events: delta, usage, completed, error, model_fallback.
        """
        req_id = request.metadata.get("request_id") or str(uuid.uuid4())
        workspace_id = request.workspace_id
        run_id_val = run_id or request.metadata.get("run_id")

        policy = await WorkspaceModelPolicyManager.get_policy(db, workspace_id)
        selection = self.router.route_request(request, policy=policy)
        resolved_provider = selection.provider
        resolved_model = selection.model_id

        WorkspaceModelPolicyManager.validate_request_policy(
            request, policy, resolved_provider=resolved_provider
        )

        candidates: List[tuple[str, str]] = [(resolved_provider, resolved_model)]
        if policy.get("fallback_enabled", True):
            safe_fallbacks = FallbackEngine.resolve_fallback_candidates(
                candidates=selection.fallback_candidates,
                original_request=request,
                workspace_policy=policy,
            )
            for fb in safe_fallbacks:
                candidates.append((fb.provider, fb.model_id))

        ws_limit = policy.get("max_concurrent_requests", 10)
        await self.concurrency.acquire(workspace_id=workspace_id, limit=ws_limit)

        try:
            streamed = False
            last_err = None

            for idx, (cand_prov, cand_model) in enumerate(candidates):
                circuit_key = f"{cand_prov}/{cand_model}"
                if not self.health.circuit_breaker.can_execute(circuit_key):
                    continue

                if idx > 0:
                    yield NormalizedStreamEvent.fallback(
                        from_model=resolved_model,
                        to_model=cand_model,
                        provider=cand_prov,
                        attempt=idx,
                        reason="Fallback due to primary stream error",
                    )

                adapter = self.providers.get(cand_prov)
                cand_req = request.model_copy(
                    update={"model": cand_model, "provider": cand_prov, "stream": True}
                )

                try:
                    async for event in adapter.generate_stream(cand_req):
                        # Attach pricing to usage event if present
                        if event.get("type") == "usage" and "usage" in event:
                            cost = self.costs.calculate_generation_cost(
                                model_id=cand_model,
                                provider=cand_prov,
                                input_tokens=event["usage"].get("input_tokens"),
                                output_tokens=event["usage"].get("output_tokens"),
                            )
                            event["usage"]["estimated_cost"] = cost
                        yield event

                    self.health.record_request_success(cand_prov, cand_model, 0.0)
                    streamed = True
                    break

                except Exception as cand_exc:
                    last_err = cand_exc
                    self.health.record_request_failure(cand_prov, cand_model, str(cand_exc))
                    if not FallbackEngine.is_eligible_for_fallback(cand_exc):
                        raise cand_exc

            if not streamed:
                yield NormalizedStreamEvent.error(
                    message=f"Streaming generation failed: {last_err}",
                    code="STREAM_FAILED",
                )
                raise last_err or GatewayError("Streaming failed across all candidates.")

        finally:
            self.concurrency.release(workspace_id=workspace_id)


default_ai_gateway = AIGateway()
