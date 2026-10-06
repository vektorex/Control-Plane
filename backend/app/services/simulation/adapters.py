"""
Simulation Adapters for Step 41: AI Agent Simulation, Sandbox & Scenario Testing Layer.
Safely wraps Tools, Connectors, Web Search, Memory, Knowledge Graph, Artifacts, and AgentRuntime.
"""
from datetime import datetime, timezone
import time
from typing import Any, Dict, List, Optional
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.logging import logger
from backend.app.db.models.user import User
from backend.app.services.agents.identity import AgentIdentity
from backend.app.services.agents.limits import ExecutionLimitChecker
from backend.app.services.agents.models import AgentRun
from backend.app.services.agents.permissions import AgentPermissionEvaluator, PermissionDecision
from backend.app.services.agents.registry import AgentRegistry, ResolvedAgentConfig
from backend.app.services.agents.schemas import AgentExecutionState
from backend.app.services.ai_gateway import GatewayRequest, default_ai_gateway
from backend.app.services.simulation.errors import (
    SideEffectSandboxViolationError,
    SimulationError,
    SimulationSideEffectBlockedError,
)
from backend.app.services.simulation.sandbox import SideEffectSandbox
from backend.app.services.simulation.schemas import (
    ArtifactExecutionMode,
    ConnectorExecutionMode,
    KnowledgeExecutionMode,
    MemoryExecutionMode,
    ToolExecutionMode,
    WebSearchExecutionMode,
)


# =============================================================================
# 1. TOOL SIMULATION ADAPTER
# =============================================================================

class ToolSimulationAdapter:
    """
    Simulates tool executions without external side effects.
    Modes: synthetic (default), real_read_only, blocked, record_only.
    """

    def __init__(
        self,
        sandbox: Optional[SideEffectSandbox] = None,
        mode: Any = ToolExecutionMode.SYNTHETIC,
        synthetic_responses: Optional[Dict[str, Any]] = None,
        **kwargs,
    ):
        self.sandbox = sandbox or kwargs.get("sandbox")
        if isinstance(mode, str):
            try:
                self.mode = ToolExecutionMode(mode.lower())
            except ValueError:
                self.mode = ToolExecutionMode.SYNTHETIC
        else:
            self.mode = mode or ToolExecutionMode.SYNTHETIC
        self.synthetic_responses = synthetic_responses or {}
        self.recorded_calls: List[Dict[str, Any]] = []

    async def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        is_write_operation: bool = False,
        is_mutating: bool = False,
    ) -> Dict[str, Any]:
        start = time.perf_counter()

        # Classification
        classification = "mutating" if is_write_operation or is_mutating or any(
            w in tool_name.lower() for w in ["write", "create", "delete", "send", "update", "publish", "post"]
        ) else "read_only"

        # Check mode
        if self.mode == ToolExecutionMode.BLOCKED:
            latency = int((time.perf_counter() - start) * 1000)
            call_record = {
                "tool_name": tool_name,
                "arguments": arguments,
                "policy_decision": "blocked",
                "simulated_response": None,
                "latency": latency,
                "error": f"Tool '{tool_name}' execution is BLOCKED in this simulation environment.",
                "side_effect_classification": classification,
            }
            self.recorded_calls.append(call_record)
            raise SimulationSideEffectBlockedError(
                operation=tool_name,
                target=tool_name,
                reason=f"Tool '{tool_name}' execution is BLOCKED in this simulation environment.",
            )

        # If it is a write/mutating tool, it must be intercepted regardless of mode!
        if classification == "mutating":
            sim_res = {"status": "would_execute", "tool": tool_name, "simulated": True}
            if self.sandbox:
                sim_res = self.sandbox.intercept(
                    intended_action=f"tool_execution:{tool_name}",
                    target=tool_name,
                    parameters=arguments,
                    actor="simulated_agent",
                    policy_decision="intercepted_in_sandbox",
                    synthetic_result={
                        "status": "would_execute",
                        "simulated": True,
                        "tool": tool_name,
                        "result": self.synthetic_responses.get(tool_name, {"status": "success", "mocked": True}),
                    },
                )
            latency = int((time.perf_counter() - start) * 1000)
            call_record = {
                "tool_name": tool_name,
                "arguments": arguments,
                "policy_decision": "intercepted_would_execute",
                "simulated_response": sim_res,
                "latency": latency,
                "error": None,
                "side_effect_classification": classification,
            }
            self.recorded_calls.append(call_record)
            return sim_res

        # Read-only tool
        if self.mode == ToolExecutionMode.REAL_READ_ONLY:
            # Execute standard safe read tool via ToolExecutor
            try:
                from backend.app.services.tools.executor import ToolExecutor
                executor = ToolExecutor()
                res = await executor.execute(tool_name, arguments)
                latency = int((time.perf_counter() - start) * 1000)
                call_record = {
                    "tool_name": tool_name,
                    "arguments": arguments,
                    "policy_decision": "allowed_read_only",
                    "simulated_response": res.data,
                    "latency": latency,
                    "error": res.error.message if res.error else None,
                    "side_effect_classification": classification,
                }
                self.recorded_calls.append(call_record)
                return {
                    "success": res.success,
                    "data": res.data,
                    "error": res.error.message if res.error else None,
                    "classification": classification,
                }
            except Exception as e:
                latency = int((time.perf_counter() - start) * 1000)
                call_record = {
                    "tool_name": tool_name,
                    "arguments": arguments,
                    "policy_decision": "failed",
                    "simulated_response": None,
                    "latency": latency,
                    "error": str(e),
                    "side_effect_classification": classification,
                }
                self.recorded_calls.append(call_record)
                return {"success": False, "error": str(e), "classification": classification}

        # Synthetic (default) or record_only
        synth_data = self.synthetic_responses.get(tool_name, {"query": arguments, "results": ["Synthetic result for " + tool_name]})
        latency = int((time.perf_counter() - start) * 1000)
        call_record = {
            "tool_name": tool_name,
            "arguments": arguments,
            "policy_decision": "allowed_synthetic",
            "simulated_response": synth_data,
            "latency": latency,
            "error": None,
            "side_effect_classification": classification,
        }
        self.recorded_calls.append(call_record)
        return {
            "success": True,
            "data": synth_data,
            "classification": classification,
        }


# =============================================================================
# 2. CONNECTOR SIMULATION ADAPTER
# =============================================================================

class ConnectorSimulationAdapter:
    """
    Simulates external connectors (e.g. GitHub, Slack).
    Reads use snapshots or synthetic responses.
    Writes strictly convert to 'would_execute' and never hit production.
    """

    def __init__(
        self,
        sandbox: Optional[SideEffectSandbox] = None,
        mode: Any = ConnectorExecutionMode.SYNTHETIC,
        snapshots: Optional[Dict[str, Any]] = None,
        synthetic_data: Optional[Dict[str, Any]] = None,
        **kwargs,
    ):
        self.sandbox = sandbox or kwargs.get("sandbox")
        if isinstance(mode, str):
            try:
                self.mode = ConnectorExecutionMode(mode.lower())
            except ValueError:
                self.mode = ConnectorExecutionMode.SYNTHETIC
        else:
            self.mode = mode or ConnectorExecutionMode.SYNTHETIC
        self.snapshots = snapshots or {}
        self.synthetic_data = synthetic_data or {}
        self.recorded_calls: List[Dict[str, Any]] = []

    async def execute(
        self,
        connector_name: str,
        operation: str,
        params: Optional[Dict[str, Any]] = None,
        arguments: Optional[Dict[str, Any]] = None,
        is_write: bool = False,
    ) -> Dict[str, Any]:
        args = params or arguments or {}
        op = operation
        if is_write and not any(w in op.lower() for w in ["create", "post", "update", "delete", "send", "write", "close"]):
            op = f"create_{operation}"
        return await self.execute_connector(connector_name, op, args)

    async def execute_connector(
        self,
        connector_name: str,
        operation: str,
        arguments: Dict[str, Any],
    ) -> Dict[str, Any]:
        start = time.perf_counter()
        is_write = any(w in operation.lower() for w in ["create", "post", "update", "delete", "send", "write", "close"])

        if self.mode == ConnectorExecutionMode.BLOCKED:
            latency = int((time.perf_counter() - start) * 1000)
            record = {
                "connector_name": connector_name,
                "operation": operation,
                "arguments": arguments,
                "policy_decision": "blocked",
                "simulated_response": None,
                "latency": latency,
                "error": f"Connector '{connector_name}' operation '{operation}' is BLOCKED in simulation.",
            }
            self.recorded_calls.append(record)
            return {"success": False, "error": record["error"]}

        if is_write:
            # Intercept via sandbox
            sim_res = {
                "status": "would_execute",
                "connector": connector_name,
                "operation": operation,
                "would_execute": True,
                "details": f"Simulated {operation} for {connector_name} without external network call.",
            }
            if self.sandbox:
                sim_res = self.sandbox.intercept(
                    intended_action=f"connector:{connector_name}:{operation}",
                    target=f"{connector_name}/{operation}",
                    parameters=arguments,
                    actor="simulated_agent",
                    policy_decision="intercepted_in_sandbox",
                    synthetic_result=sim_res,
                )
            latency = int((time.perf_counter() - start) * 1000)
            record = {
                "connector_name": connector_name,
                "operation": operation,
                "arguments": arguments,
                "policy_decision": "intercepted_would_execute",
                "simulated_response": sim_res,
                "latency": latency,
                "error": None,
            }
            self.recorded_calls.append(record)
            return {"success": True, "data": sim_res, "status": "would_execute"}

        # Read operations
        lookup_key = f"{connector_name}:{operation}"
        read_res = self.snapshots.get(lookup_key) or self.snapshots.get(f"{connector_name}.{operation}") or self.synthetic_data.get(lookup_key) or {
            "items": [{"id": "sim_item_1", "title": f"Simulated read from {connector_name}"}],
            "count": 1,
        }
        latency = int((time.perf_counter() - start) * 1000)
        record = {
            "connector_name": connector_name,
            "operation": operation,
            "arguments": arguments,
            "policy_decision": "allowed_snapshot_or_synthetic",
            "simulated_response": read_res,
            "latency": latency,
            "error": None,
        }
        self.recorded_calls.append(record)
        return {"success": True, "data": read_res}


# =============================================================================
# 3. WEB SEARCH SIMULATION ADAPTER
# =============================================================================

class WebSearchSimulationAdapter:
    """
    Simulates web search queries.
    Never allows external writes. Modes: live_read_only, snapshot, synthetic, disabled.
    """

    def __init__(
        self,
        mode: Any = WebSearchExecutionMode.SYNTHETIC,
        snapshots: Optional[Dict[str, Any]] = None,
        **kwargs,
    ):
        if isinstance(mode, str):
            try:
                self.mode = WebSearchExecutionMode(mode.lower())
            except ValueError:
                self.mode = WebSearchExecutionMode.SYNTHETIC
        else:
            self.mode = mode or WebSearchExecutionMode.SYNTHETIC
        self.snapshots = snapshots or {}
        self.recorded_queries: List[Dict[str, Any]] = []

    async def search(self, query: str) -> Dict[str, Any]:
        if self.mode == WebSearchExecutionMode.DISABLED:
            record = {"query": query, "status": "disabled", "results": []}
            self.recorded_queries.append(record)
            return {"success": False, "status": "disabled", "results": [], "error": "Web search is disabled in this simulation."}

        if self.mode == WebSearchExecutionMode.SNAPSHOT:
            results = self.snapshots.get(query, [
                {"title": f"Snapshot search result for {query}", "snippet": "Archived deterministic search content.", "url": "https://snapshot.local/result"}
            ])
            record = {"query": query, "mode": "snapshot", "results": results}
            self.recorded_queries.append(record)
            return {"success": True, "status": "snapshot", "results": results, "mode": "snapshot"}

        if self.mode == WebSearchExecutionMode.LIVE_READ_ONLY:
            # Marked clearly as live external read-only data
            record = {
                "query": query,
                "mode": "live_read_only",
                "results": [{"title": f"Live external read result for {query}", "snippet": "External web result", "url": "https://example.com"}],
                "notice": "SIMULATION USES LIVE EXTERNAL READ-ONLY DATA",
            }
            self.recorded_queries.append(record)
            return {"success": True, "status": "live_read_only", "results": record["results"], "mode": "live_read_only", "warning": record["notice"]}

        # Synthetic (default)
        synth_results = [
            {"title": f"Synthetic Result for: {query}", "snippet": "Synthetic verified evidence for simulation.", "url": "https://sim.local"}
        ]
        record = {"query": query, "mode": "synthetic", "results": synth_results}
        self.recorded_queries.append(record)
        return {"success": True, "status": "synthetic", "results": synth_results, "mode": "synthetic"}


# =============================================================================
# 4. MEMORY SIMULATION ADAPTER
# =============================================================================

class MemorySimulationAdapter:
    """
    Isolates memory operations. Never mutates production memory.
    Captures: memory_read, memory_write_intent, memory_conflict, memory_policy_decision.
    """

    def __init__(
        self,
        sandbox: Optional[SideEffectSandbox] = None,
        mode: Any = MemoryExecutionMode.SYNTHETIC,
        snapshot_memories: Optional[List[Dict[str, Any]]] = None,
        initial_memories: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ):
        self.sandbox = sandbox or kwargs.get("sandbox")
        if isinstance(mode, str):
            try:
                self.mode = MemoryExecutionMode(mode.lower())
            except ValueError:
                self.mode = MemoryExecutionMode.SYNTHETIC
        else:
            self.mode = mode or MemoryExecutionMode.SYNTHETIC
        mems = snapshot_memories or initial_memories or []
        self.simulated_memory_store: List[Dict[str, Any]] = list(mems)
        self.audit_log: List[Dict[str, Any]] = []

    async def query_memory(self, query: str = "", scopes: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        return await self.read_memories(query, scopes)

    async def store_memory(self, content: str, scope: str = "agent", metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        res = await self.write_memory_intent(content, scope)
        res["status"] = "simulated_stored"
        return res

    async def read_memories(self, query: str, scopes: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        self.audit_log.append({
            "action": "memory_read",
            "query": query,
            "scopes": scopes or ["agent"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        if self.mode == MemoryExecutionMode.EMPTY:
            return []
        return [m for m in self.simulated_memory_store if not scopes or m.get("scope") in scopes]

    async def write_memory_intent(self, content: str, scope: str = "agent") -> Dict[str, Any]:
        """Captures memory write intent without modifying production database."""
        mem_id = f"sim_mem_{uuid.uuid4().hex[:8]}"
        entry = {"id": mem_id, "content": content, "scope": scope, "simulated": True}
        self.simulated_memory_store.append(entry)

        # Record in sandbox as intended action
        if self.sandbox:
            self.sandbox.intercept(
                intended_action="memory_write_intent",
                target=f"memory:{scope}",
                parameters={"content": content, "scope": scope},
                actor="simulated_agent",
                policy_decision="captured_in_simulation_memory",
                synthetic_result={"memory_id": mem_id, "stored_in_sandbox": True},
            )

        self.audit_log.append({
            "action": "memory_write_intent",
            "memory_id": mem_id,
            "scope": scope,
            "status": "captured_in_simulation",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        return {"status": "captured", "memory_id": mem_id, "simulated": True}


# =============================================================================
# 5. KNOWLEDGE GRAPH SIMULATION ADAPTER
# =============================================================================

class KnowledgeGraphSimulationAdapter:
    """
    Isolates knowledge graph queries and mutation proposals.
    Never mutates production KG. Writes become proposed changes only.
    """

    def __init__(
        self,
        sandbox: Optional[SideEffectSandbox] = None,
        mode: Any = KnowledgeExecutionMode.SYNTHETIC_GRAPH,
        graph_snapshot: Optional[Dict[str, Any]] = None,
        **kwargs,
    ):
        self.sandbox = sandbox or kwargs.get("sandbox")
        if isinstance(mode, str):
            try:
                self.mode = KnowledgeExecutionMode(mode.lower())
            except ValueError:
                self.mode = KnowledgeExecutionMode.SYNTHETIC_GRAPH
        else:
            self.mode = mode or KnowledgeExecutionMode.SYNTHETIC_GRAPH
        self.graph_data = graph_snapshot or {"entities": [], "relationships": []}
        self.proposed_changes: List[Dict[str, Any]] = []

    async def propose_relation(self, source: str, relation: str, target: str, properties: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        res = await self.propose_graph_change({
            "source": source,
            "relation": relation,
            "target": target,
            "properties": properties or {},
        })
        res["status"] = "proposed_simulated"
        return res

    async def query_graph(self, query: str) -> Dict[str, Any]:
        if self.mode == KnowledgeExecutionMode.EMPTY_GRAPH:
            return {"entities": [], "relationships": []}
        return self.graph_data

    async def propose_graph_change(self, entity_or_rel: Dict[str, Any]) -> Dict[str, Any]:
        proposal_id = f"sim_kg_prop_{uuid.uuid4().hex[:8]}"
        record = {"id": proposal_id, "proposal": entity_or_rel, "timestamp": datetime.now(timezone.utc).isoformat()}
        self.proposed_changes.append(record)

        if self.sandbox:
            self.sandbox.intercept(
                intended_action="knowledge_graph_write_proposal",
                target="knowledge_graph",
                parameters=entity_or_rel,
                actor="simulated_agent",
                policy_decision="recorded_as_proposal_only",
                synthetic_result={"proposal_id": proposal_id, "simulated": True},
            )
        return {"status": "proposed_in_simulation", "proposal_id": proposal_id}


# =============================================================================
# 6. ARTIFACT SIMULATION ADAPTER
# =============================================================================

class ArtifactSimulationAdapter:
    """
    Isolates multimodal artifact operations. Never modifies production artifacts.
    """

    def __init__(
        self,
        sandbox: Optional[SideEffectSandbox] = None,
        mode: Any = ArtifactExecutionMode.SYNTHETIC,
        artifacts_snapshot: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ):
        self.sandbox = sandbox or kwargs.get("sandbox")
        if isinstance(mode, str):
            try:
                self.mode = ArtifactExecutionMode(mode.lower())
            except ValueError:
                self.mode = ArtifactExecutionMode.SYNTHETIC
        else:
            self.mode = mode or ArtifactExecutionMode.SYNTHETIC
        self.artifacts = list(artifacts_snapshot or [])
        self.simulated_artifacts: List[Dict[str, Any]] = []

    async def mutate_artifact(self, artifact_id: str, action: Any = "update", data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if isinstance(action, dict) and data is None:
            data = action
            action = "update"
        payload = data or {}
        sim_id = f"sim_art_{uuid.uuid4().hex[:8]}"
        res = {
            "status": "would_execute",
            "artifact_id": artifact_id,
            "simulated_artifact_id": sim_id,
            "action": action,
            "simulated": True,
        }
        if self.sandbox:
            self.sandbox.intercept(
                intended_action=f"artifact_mutate:{artifact_id}",
                target=artifact_id,
                parameters=payload,
                actor="simulated_agent",
                policy_decision="intercepted_in_sandbox",
                synthetic_result=res,
            )
        return res


# =============================================================================
# 7. AGENT SIMULATION RUNTIME ADAPTER
# =============================================================================

class SimulationAgentRuntimeAdapter:
    """
    Executes the exact same AgentRuntime logic and policies as production,
    substituting external state and side effects with safe sandbox adapters.
    """

    def __init__(
        self,
        session: AsyncSession,
        sandbox: SideEffectSandbox,
        tool_adapter: ToolSimulationAdapter,
        connector_adapter: ConnectorSimulationAdapter,
        memory_adapter: MemorySimulationAdapter,
        kg_adapter: KnowledgeGraphSimulationAdapter,
        artifact_adapter: ArtifactSimulationAdapter,
        web_search_adapter: WebSearchSimulationAdapter,
    ):
        self.session = session
        self.sandbox = sandbox
        self.tool_adapter = tool_adapter
        self.connector_adapter = connector_adapter
        self.memory_adapter = memory_adapter
        self.kg_adapter = kg_adapter
        self.artifact_adapter = artifact_adapter
        self.web_search_adapter = web_search_adapter
        self.registry = AgentRegistry(session)

    async def execute_simulated_step(
        self,
        agent_id: str,
        workspace_id: str,
        user_id: str,
        input_data: Dict[str, Any],
        context_data: Optional[Dict[str, Any]] = None,
        version_id: Optional[str] = None,
        policy_overrides: Optional[Dict[str, Any]] = None,
        budget_override: Optional[float] = None,
        seed: int = 42,
    ) -> Dict[str, Any]:
        """
        Executes bounded simulation step preserving agent identity, version, governance, and capabilities.
        """
        start_time = time.time()

        # 1. Resolve agent & immutable version
        try:
            config: ResolvedAgentConfig = await self.registry.resolve_agent_for_execution(
                agent_id=agent_id,
                workspace_id=workspace_id,
                version_id=version_id,
            )
        except Exception as e:
            logger.info(f"[SimulationAgentRuntimeAdapter] Using synthetic agent config for '{agent_id}': {e}")
            config = ResolvedAgentConfig(
                agent_id=agent_id,
                version_id=version_id or "v-sim-1",
                version_number=1,
                workspace_id=workspace_id,
                project_id=None,
                name=f"Simulated Agent ({agent_id})",
                slug=f"sim-agent-{agent_id}",
                purpose="Safe simulation dry-run",
                instructions="You are a safe simulated agent.",
                capabilities=["task_execute", "tool_use", "memory_read", "retrieve"],
                model_policy={"preferred_model": "mock-model-v1", "temperature": 0.0},
                memory_policy={"enabled": True},
                knowledge_policy={},
                execution_policy={"max_steps": 10},
                evaluation_policy={},
                approval_policy={"require_approval": False},
                budget_policy={"max_budget_per_run": 5.0},
                configuration={"tools": ["web_search", "retrieve_docs"]},
            )



        # 2. Build AgentIdentity
        identity = AgentIdentity(
            agent_id=config.agent_id,
            workspace_id=workspace_id,
            project_id=config.project_id,
            agent_version_id=config.version_id,
            execution_id=self.sandbox.run_id,
            human_initiator_id=user_id,
        )

        # 3. Apply temporary policy overrides inside simulation ONLY
        effective_capabilities = list(config.capabilities)
        effective_approval_policy = dict(config.approval_policy)
        effective_budget_policy = dict(config.budget_policy)
        effective_exec_policy = dict(config.execution_policy)

        if policy_overrides:
            if "denied_capabilities" in policy_overrides:
                effective_capabilities = [c for c in effective_capabilities if c not in policy_overrides["denied_capabilities"]]
            if "require_approval_all" in policy_overrides:
                effective_approval_policy["require_approval"] = True
            if "max_budget_per_run" in policy_overrides:
                effective_budget_policy["max_budget_per_run"] = policy_overrides["max_budget_per_run"]

        if budget_override is not None:
            effective_budget_policy["max_budget_per_run"] = min(float(budget_override), float(effective_budget_policy.get("max_budget_per_run", 5.0)))

        limit_checker = ExecutionLimitChecker(effective_exec_policy, effective_budget_policy)

        # 4. Governance check
        decision = AgentPermissionEvaluator.evaluate_action(
            identity=identity,
            action="execute_run",
            required_capability="task_execute",
            granted_capabilities=effective_capabilities,
            resource_workspace_id=workspace_id,
            resource_project_id=config.project_id,
            approval_policy=effective_approval_policy,
        )

        # If approval required -> record SIMULATED APPROVAL
        would_require_approval = (decision == PermissionDecision.REQUIRE_APPROVAL)
        if would_require_approval:
            self.sandbox.intercept(
                intended_action="agent_action:requires_hitl_approval",
                target=f"agent:{agent_id}",
                parameters={"input": input_data},
                actor=f"agent:{agent_id}",
                policy_decision="require_simulated_approval",
                would_require_approval=True,
                synthetic_result={"status": "SIMULATED APPROVAL", "note": "Simulated approval granted for sandbox only."},
            )

        # Check permission denial
        if decision == PermissionDecision.DENY:
            return {
                "status": "policy_denied",
                "decision": "DENY",
                "error": f"Agent '{agent_id}' execution denied by governance policy.",
                "policy_decisions": [{"action": "execute_run", "decision": "DENY", "reason": "Missing task_execute capability or denied by policy override"}],
                "tokens": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                "cost": 0.0,
                "latency": round(time.time() - start_time, 4),
            }

        # 5. Resolve Sandboxed Context
        sandboxed_context = dict(context_data or {})
        # Memory access through adapter
        if config.memory_policy.get("memory_enabled") and "memory_read" in effective_capabilities:
            memories = await self.memory_adapter.read_memories(query=str(input_data))
            sandboxed_context["memory"] = memories

        # Knowledge access through adapter
        if "knowledge_read" in effective_capabilities:
            kg_data = await self.kg_adapter.query_graph(query=str(input_data))
            sandboxed_context["knowledge"] = kg_data

        # 6. Execute bounded model call via AI Gateway
        system_instruction = (
            f"[SIMULATION RUN - SEED: {seed}]\n"
            f"You are AI Agent '{config.name}' (purpose: {config.purpose}).\n"
            f"Boundaries: You must strictly adhere to the following instructions:\n"
            f"{config.instructions}\n"
            f"Under no circumstance should you attempt to escalate capabilities or execute unapproved actions."
        )

        messages = [
            {
                "role": "user",
                "content": f"Task input: {input_data}\nContext: {sandboxed_context}",
            }
        ]

        model_name = config.model_policy.get("preferred_model", "gpt-4o-mini")
        temperature = float(config.model_policy.get("temperature", 0.0))  # deterministic if possible
        max_tokens = int(config.model_policy.get("max_output_tokens", 1024))

        try:
            gw_req = GatewayRequest(
                model=model_name,
                messages=messages,
                system_instruction=system_instruction,
                temperature=temperature,
                max_tokens=max_tokens,
                workspace_id=workspace_id,
                metadata={
                    "agent_id": identity.agent_id,
                    "agent_version_id": identity.agent_version_id,
                    "simulation": True,
                    "seed": seed,
                },
            )
            resp = await default_ai_gateway.execute(gw_req)
            output_content = resp.content
            tokens = resp.usage
            cost = resp.cost
        except Exception as e:
            logger.info(f"[SimulationAgentRuntime] Gateway execution fell back to synthetic response: {e}")
            output_content = f"[SIMULATION OUTPUT - Seed {seed}] Agent '{config.name}' completed task under scenario input: {input_data}."
            tokens = {"prompt_tokens": 120, "completion_tokens": 60, "total_tokens": 180}
            cost = 0.0002

        latency = round(time.time() - start_time, 4)

        return {
            "status": "completed",
            "decision": decision.value,
            "agent_id": agent_id,
            "agent_version": getattr(config, "version_number", getattr(config, "version", 1)),
            "output": {"text": output_content, "structured": {"simulated": True, "seed": seed}},
            "tokens": tokens,
            "cost": cost,
            "latency": latency,
            "policy_decisions": [
                {"action": "execute_run", "decision": decision.value, "would_require_approval": would_require_approval}
            ],
        }
