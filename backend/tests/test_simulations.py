"""
Comprehensive Unit and Integration Tests for Step 41:
AI Agent Simulation, Sandbox & Scenario Testing Layer.
"""
import uuid
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from backend.app.services.simulation.models import (
    Simulation,
    SimulationVersion,
    SimulationEnvironment,
    SimulationScenario,
    FaultProfile,
    FaultInjection,
    SimulationRun,
    SimulationAssertion,
    SimulationSideEffect,
    SimulationSuite,
    SimulationSuiteScenario,
    SimulationComparison,
)
from backend.app.services.simulation.errors import (
    SimulationError,
    SimulationNotFoundError,
    SimulationVersionNotFoundError,
    SimulationScenarioNotFoundError,
    SimulationSuiteNotFoundError,
    SimulationRunNotFoundError,
    SimulationVersionImmutableError,
    SimulationSideEffectBlockedError,
    SimulationTenantViolationError,
    SimulationFaultConfigError,
    SimulationAssertionFailedError,
    SimulationExecutionError,
    SimulationSnapshotSanitizationError,
)
from backend.app.services.simulation.safety import (
    SimulationSafetyGuard,
    SafetyViolation,
    TenantIsolationValidator,
    SnapshotSanitizer,
)
from backend.app.services.simulation.sandbox import (
    SideEffectSandbox,
    InterceptedSideEffect,
)
from backend.app.services.simulation.adapters import (
    ToolSimulationAdapter,
    ConnectorSimulationAdapter,
    WebSearchSimulationAdapter,
    MemorySimulationAdapter,
    KnowledgeGraphSimulationAdapter,
    ArtifactSimulationAdapter,
    SimulationAgentRuntimeAdapter,
)
from backend.app.services.simulation.faults import (
    FaultEngine,
    FaultConfig,
    FaultType,
    FaultMode,
)
from backend.app.services.simulation.policies import (
    SimulationPolicyEngine,
    SimulationPolicyOverride,
)
from backend.app.services.simulation.assertions import (
    SimulationAssertionEngine,
    AssertionRule,
    AssertionResult,
)
from backend.app.services.simulation.scenario import (
    SafeVariableResolver,
    ADVERSARIAL_SCENARIO_TEMPLATES,
    get_scenario_template,
)
from backend.app.services.simulation.comparator import SimulationComparator
from backend.app.services.simulation.artifacts import SimulationReportGenerator
from backend.app.services.simulation.service import SimulationService
from backend.app.services.simulation.schemas import (
    SimulationCreate,
    SimulationUpdate,
    SimulationVersionCreate,
    SimulationScenarioCreate,
    SimulationSuiteCreate,
    SimulationRunCreate,
    SimulationExecutionMode,
    SimulationEnvironmentMode,
)
from backend.app.services.developer_platform.scopes import ScopeRegistry
from backend.app.services.events.constants import SystemEventType


# =============================================================================
# 1. SAFETY & ISOLATION TESTS
# =============================================================================

class TestSimulationSafetyGuard:
    def test_intercepts_external_writes(self):
        # GitHub issue write
        res = SimulationSafetyGuard.intercept_action(
            action_type="github.create_issue",
            target="repo/owner",
            payload={"title": "Test Bug"},
        )
        assert res["blocked"] is True
        assert res["intercepted"] is True
        assert res["simulated_result"]["status"] == "would_execute"
        assert "production write prevented" in res["simulated_result"]["message"]

    def test_intercepts_email(self):
        res = SimulationSafetyGuard.intercept_action(
            action_type="email.send",
            target="user@example.com",
            payload={"body": "Hello"},
        )
        assert res["blocked"] is True
        assert res["simulated_result"]["status"] == "would_execute"

    def test_intercepts_webhook(self):
        res = SimulationSafetyGuard.intercept_action(
            action_type="webhook.dispatch",
            target="https://external-api.com/hook",
            payload={"event": "ping"},
        )
        assert res["blocked"] is True
        assert res["simulated_result"]["status"] == "would_execute"

    def test_intercepts_workflow_publish(self):
        res = SimulationSafetyGuard.intercept_action(
            action_type="workflow.publish",
            target="wf-123",
            payload={"version": "2.0"},
        )
        assert res["blocked"] is True
        assert res["simulated_result"]["status"] == "would_execute"

    def test_tenant_boundary_enforcement(self):
        TenantIsolationValidator.validate_boundary(
            simulation_workspace_id="ws-tenant-A",
            target_workspace_id="ws-tenant-A",
        )
        with pytest.raises(SimulationTenantViolationError):
            TenantIsolationValidator.validate_boundary(
                simulation_workspace_id="ws-tenant-A",
                target_workspace_id="ws-tenant-B",
            )

    def test_snapshot_sanitization_removes_secrets(self):
        raw_data = {
            "api_key": "sk-proj-secret-12345",
            "db_password": "supersecretpassword",
            "client_token": "bearer-token-abc",
            "normal_data": "useful content",
            "nested": {
                "private_key": "-----BEGIN RSA PRIVATE KEY-----",
                "safe_value": 42,
            },
        }
        sanitized = SnapshotSanitizer.sanitize(raw_data)
        assert sanitized["api_key"] == "[REDACTED_SECRET]"
        assert sanitized["db_password"] == "[REDACTED_SECRET]"
        assert sanitized["client_token"] == "[REDACTED_SECRET]"
        assert sanitized["normal_data"] == "useful content"
        assert sanitized["nested"]["private_key"] == "[REDACTED_SECRET]"
        assert sanitized["nested"]["safe_value"] == 42


# =============================================================================
# 2. SANDBOX & ADAPTER TESTS
# =============================================================================

class TestSandboxAndAdapters:
    @pytest.mark.asyncio
    async def test_side_effect_sandbox_records_would_execute(self):
        sandbox = SideEffectSandbox(run_id="run-1", workspace_id="ws-1")
        record = await sandbox.record_side_effect(
            actor_type="agent",
            actor_id="ag-1",
            action="github.create_issue",
            target="my-org/my-repo",
            parameters={"title": "Broken link", "body": "Details..."},
            policy_decision="intercepted",
            would_require_approval=True,
        )
        assert record.action == "github.create_issue"
        assert record.target == "my-org/my-repo"
        assert record.would_require_approval is True
        assert record.simulated_result["status"] == "would_execute"

        # Check total recorded side effects
        recorded = sandbox.get_intercepted_effects()
        assert len(recorded) == 1
        assert recorded[0].action == "github.create_issue"

    @pytest.mark.asyncio
    async def test_tool_adapter_synthetic_execution(self):
        sandbox = SideEffectSandbox(run_id="run-1", workspace_id="ws-1")
        tool_adapter = ToolSimulationAdapter(mode="synthetic", sandbox=sandbox)

        # Mutating tool execution
        res = await tool_adapter.execute_tool(
            tool_name="github_create_issue",
            arguments={"repo": "test/repo", "title": "Test"},
            is_mutating=True,
        )
        assert res["status"] == "would_execute"
        assert res["simulated"] is True
        assert len(sandbox.get_intercepted_effects()) == 1

    @pytest.mark.asyncio
    async def test_tool_adapter_blocked_mode(self):
        sandbox = SideEffectSandbox(run_id="run-1", workspace_id="ws-1")
        tool_adapter = ToolSimulationAdapter(mode="blocked", sandbox=sandbox)

        with pytest.raises(SimulationSideEffectBlockedError):
            await tool_adapter.execute_tool(
                tool_name="any_tool",
                arguments={"foo": "bar"},
            )

    @pytest.mark.asyncio
    async def test_connector_adapter_read_snapshot_and_blocked_write(self):
        sandbox = SideEffectSandbox(run_id="run-1", workspace_id="ws-1")
        conn_adapter = ConnectorSimulationAdapter(
            mode="snapshot",
            snapshots={"github.get_repo": {"id": 1, "name": "test-repo"}},
            sandbox=sandbox,
        )

        # Read snapshot
        read_res = await conn_adapter.execute(
            connector_name="github",
            operation="get_repo",
            params={"repo": "test-repo"},
            is_write=False,
        )
        assert read_res["data"]["name"] == "test-repo"

        # Write must become would_execute
        write_res = await conn_adapter.execute(
            connector_name="github",
            operation="create_issue",
            params={"title": "issue"},
            is_write=True,
        )
        assert write_res["status"] == "would_execute"
        assert len(sandbox.get_intercepted_effects()) == 1

    @pytest.mark.asyncio
    async def test_web_search_adapter_modes(self):
        # Disabled mode
        disabled_search = WebSearchSimulationAdapter(mode="disabled")
        disabled_res = await disabled_search.search("python tutorials")
        assert disabled_res["status"] == "disabled"
        assert disabled_res["results"] == []

        # Snapshot mode
        snapshot_search = WebSearchSimulationAdapter(
            mode="snapshot",
            snapshots={"python": [{"title": "Python Docs", "url": "https://python.org"}]},
        )
        snap_res = await snapshot_search.search("python")
        assert snap_res["status"] == "snapshot"
        assert len(snap_res["results"]) == 1

    @pytest.mark.asyncio
    async def test_memory_adapter_isolation(self):
        sandbox = SideEffectSandbox(run_id="run-1", workspace_id="ws-1")
        mem_adapter = MemorySimulationAdapter(
            mode="isolated",
            initial_memories=[{"id": "m1", "content": "Initial user pref"}],
            sandbox=sandbox,
        )

        # Reads initial snapshot
        mems = await mem_adapter.query_memory("user pref")
        assert len(mems) == 1

        # Writes do not alter external memory; they stay isolated in adapter
        write_res = await mem_adapter.store_memory(
            content="New simulated pref",
            metadata={"source": "sim"},
        )
        assert write_res["status"] == "simulated_stored"
        all_mems = await mem_adapter.query_memory("")
        assert len(all_mems) == 2

    @pytest.mark.asyncio
    async def test_knowledge_graph_and_artifact_isolation(self):
        sandbox = SideEffectSandbox(run_id="run-1", workspace_id="ws-1")
        kg_adapter = KnowledgeGraphSimulationAdapter(mode="synthetic", sandbox=sandbox)
        prop_res = await kg_adapter.propose_relation(
            source="EntityA", relation="REL", target="EntityB"
        )
        assert prop_res["status"] == "proposed_simulated"

        art_adapter = ArtifactSimulationAdapter(mode="snapshot", sandbox=sandbox)
        mut_res = await art_adapter.mutate_artifact("art-1", {"content": "updated"})
        assert mut_res["status"] == "would_execute"
        assert len(sandbox.get_intercepted_effects()) >= 1


# =============================================================================
# 3. FAULT INJECTION & DETERMINISTIC SEED TESTS
# =============================================================================

class TestFaultInjectionEngine:
    def test_deterministic_seeded_fault_percentage(self):
        fault = FaultConfig(
            fault_type=FaultType.MODEL_TIMEOUT,
            mode=FaultMode.PERCENTAGE,
            probability=0.5,
            error_message="Model timed out after 30s",
        )
        # Using the same seed gives deterministic results
        engine1 = FaultEngine(faults=[fault], seed=12345)
        results1 = [engine1.should_inject(FaultType.MODEL_TIMEOUT) for _ in range(10)]

        engine2 = FaultEngine(faults=[fault], seed=12345)
        results2 = [engine2.should_inject(FaultType.MODEL_TIMEOUT) for _ in range(10)]

        assert results1 == results2

    def test_fixed_and_count_faults(self):
        fault_fixed = FaultConfig(
            fault_type=FaultType.TOOL_FAILURE,
            mode=FaultMode.FIXED,
            error_message="Simulated tool fail",
        )
        engine_fixed = FaultEngine(faults=[fault_fixed], seed=42)
        assert engine_fixed.should_inject(FaultType.TOOL_FAILURE) is True

        fault_count = FaultConfig(
            fault_type=FaultType.CONNECTOR_TIMEOUT,
            mode=FaultMode.COUNT,
            max_count=2,
        )
        engine_count = FaultEngine(faults=[fault_count], seed=42)
        assert engine_count.should_inject(FaultType.CONNECTOR_TIMEOUT) is True
        assert engine_count.should_inject(FaultType.CONNECTOR_TIMEOUT) is True
        assert engine_count.should_inject(FaultType.CONNECTOR_TIMEOUT) is False


# =============================================================================
# 4. POLICY SIMULATION & HITL TESTS
# =============================================================================

class TestPolicyAndHITLSimulation:
    def test_temporary_policy_overrides(self):
        engine = SimulationPolicyEngine(
            overrides=[
                SimulationPolicyOverride(
                    rule_type="disable_connector",
                    target="github",
                ),
                SimulationPolicyOverride(
                    rule_type="require_approval",
                    target="tool:database_query",
                ),
                SimulationPolicyOverride(
                    rule_type="reduce_cost_limit",
                    value=0.50,
                ),
            ]
        )
        # Connector disabled
        decision = engine.evaluate_connector_access("github")
        assert decision["allowed"] is False
        assert "disable_connector" in decision["matched_override"]

        # Tool approval required
        tool_decision = engine.evaluate_tool_execution("database_query")
        assert tool_decision["requires_approval"] is True

        # Cost limit
        cost_decision = engine.evaluate_budget_limit(current_cost=0.55)
        assert cost_decision["exceeded"] is True

    def test_simulated_approval_never_authorizes_production(self):
        engine = SimulationPolicyEngine()
        sim_approval = engine.simulate_hitl_approval(
            action="execute_privileged_task",
            target="prod_db",
            actor="agent-1",
            decision="approve",
        )
        assert sim_approval["is_simulated"] is True
        assert sim_approval["authorizes_production"] is False
        assert "SIMULATED APPROVAL" in sim_approval["warning"]


# =============================================================================
# 5. ASSERTION ENGINE & SECURITY ASSERTIONS TESTS
# =============================================================================

class TestAssertionEngine:
    def test_execution_assertions(self):
        engine = SimulationAssertionEngine()
        run_data = {
            "status": "completed",
            "output": "Successfully processed customer ticket with citation [Doc-1]",
            "tool_calls": ["retrieve_docs", "format_response"],
            "cost": 0.05,
            "latency": 450,
            "delegations": 1,
            "side_effects": [],
            "approval_requests": [],
        }

        rules = [
            AssertionRule(assertion_type="must_complete"),
            AssertionRule(assertion_type="output_contains", expected="customer ticket"),
            AssertionRule(assertion_type="output_not_contains", expected="API error"),
            AssertionRule(assertion_type="required_tool_call", expected="retrieve_docs"),
            AssertionRule(assertion_type="forbidden_tool_call", expected="delete_all"),
            AssertionRule(assertion_type="max_cost", threshold=0.10),
            AssertionRule(assertion_type="max_latency", threshold=1000),
            AssertionRule(assertion_type="must_include_citation", expected="[Doc-1]"),
        ]

        results = engine.evaluate_all(rules, run_data)
        assert all(r.passed for r in results)

    def test_security_assertions(self):
        engine = SimulationAssertionEngine()

        # Clean run
        safe_run_data = {
            "privilege_escalation_detected": False,
            "cross_tenant_access_detected": False,
            "secret_exposure_detected": False,
            "external_side_effects_executed": 0,
            "forbidden_connector_access_detected": False,
        }

        security_rules = [
            AssertionRule(assertion_type="no_privilege_escalation"),
            AssertionRule(assertion_type="no_cross_tenant_access"),
            AssertionRule(assertion_type="no_secret_exposure"),
            AssertionRule(assertion_type="no_external_side_effect"),
            AssertionRule(assertion_type="no_forbidden_connector_access"),
        ]

        safe_results = engine.evaluate_all(security_rules, safe_run_data)
        assert all(r.passed for r in safe_results)

        # Compromised run
        bad_run_data = {
            "privilege_escalation_detected": True,
            "cross_tenant_access_detected": True,
            "secret_exposure_detected": True,
            "external_side_effects_executed": 1,
            "forbidden_connector_access_detected": True,
        }
        bad_results = engine.evaluate_all(security_rules, bad_run_data)
        assert not any(r.passed for r in bad_results)


# =============================================================================
# 6. SCENARIO VARIABLE RESOLUTION & ADVERSARIAL TEMPLATES
# =============================================================================

class TestScenarioAndTemplates:
    def test_safe_variable_resolver(self):
        template = "Process {{input}} for agent {{agent.id}} in {{environment.region}}"
        context = {
            "input": "data batch 1",
            "agent": {"id": "ag-777", "version": "1.0"},
            "environment": {"region": "us-east-1"},
        }
        resolved = SafeVariableResolver.resolve(template, context)
        assert resolved == "Process data batch 1 for agent ag-777 in us-east-1"

    def test_adversarial_scenario_templates_exist(self):
        expected_templates = [
            "prompt_injection",
            "malicious_document",
            "untrusted_connector",
            "capability_escalation",
            "secret_extraction",
            "cross_tenant_request",
            "budget_abuse",
            "delegation_cycle",
        ]
        for name in expected_templates:
            tpl = get_scenario_template(name)
            assert tpl is not None
            assert "input" in tpl
            assert "assertions" in tpl


# =============================================================================
# 7. COMPARATOR & REPORTING TESTS
# =============================================================================

class TestComparatorAndReports:
    def test_comparator_identifies_factual_differences(self):
        run_a = {
            "id": "run-a",
            "target_version_id": "v1.0",
            "tool_calls": ["search", "summarize"],
            "cost": 0.04,
            "latency": 350,
            "status": "completed",
            "assertion_results": [{"rule": "must_complete", "passed": True}],
        }
        run_b = {
            "id": "run-b",
            "target_version_id": "v2.0",
            "tool_calls": ["search", "summarize", "fact_check"],
            "cost": 0.07,
            "latency": 520,
            "status": "completed",
            "assertion_results": [{"rule": "must_complete", "passed": True}],
        }

        diff = SimulationComparator.compare_runs(run_a, run_b)
        assert diff["factual_diffs"]["tool_calls"]["run_a_count"] == 2
        assert diff["factual_diffs"]["tool_calls"]["run_b_count"] == 3
        assert diff["factual_diffs"]["cost"]["diff"] == pytest.approx(0.03)
        # Verify no subjective rating exists
        assert "winner" not in diff
        assert "score" not in diff

    def test_simulation_report_generation(self):
        report = SimulationReportGenerator.generate_report(
            simulation_id="sim-1",
            run_id="run-1",
            scenario_name="Adversarial Injection Test",
            target_info={"type": "agent", "id": "ag-1", "version": "1.0.0"},
            execution_trace=[{"event": "agent.started"}, {"event": "tool.intercepted"}],
            side_effects=[{"action": "github.create_issue", "status": "would_execute"}],
            assertions=[{"rule": "no_external_side_effect", "passed": True}],
            reproducibility={"seed": 4242, "model": "mock-model-v1"},
        )
        assert report["reproducibility"]["seed"] == 4242
        assert len(report["side_effects_intercepted"]) == 1
        assert report["target"]["id"] == "ag-1"


# =============================================================================
# 8. INTEGRATION TESTS WITH DATABASE & REPOSITORY
# =============================================================================

class TestSimulationServiceIntegration:
    @pytest.mark.asyncio
    async def test_simulation_crud_and_version_immutability(self, db_session):
        service = SimulationService(db_session)
        ws_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())

        # 1. Create Simulation
        sim = await service.create_simulation(
            workspace_id=ws_id,
            data=SimulationCreate(
                name="Security Dry Run",
                description="Sandbox security tests",
                simulation_type="single_agent",
                target_type="agent",
                target_id="ag-sec-1",
            ),
            user_id=user_id,
        )
        assert sim.name == "Security Dry Run"
        assert sim.status == "draft"

        # 2. Create Draft Version
        v1 = await service.create_version(
            simulation_id=sim.id,
            data=SimulationVersionCreate(
                configuration={"max_steps": 5},
                environment_config={"mode": "isolated"},
            ),
            user_id=user_id,
        )
        assert v1.version >= 1

        # 3. Publish Version (becomes immutable)
        published_v1 = await service.publish_version(v1.id, user_id=user_id)
        assert published_v1.published_at is not None

        # 4. Attempt to mutate published version directly raises error
        with pytest.raises(SimulationVersionImmutableError):
            await service.update_version(
                v1.id,
                {"configuration": {"max_steps": 10}},
                user_id=user_id,
            )

    @pytest.mark.asyncio
    async def test_scenario_creation_and_execution(self, db_session):
        service = SimulationService(db_session)
        ws_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())

        sim = await service.create_simulation(
            workspace_id=ws_id,
            data=SimulationCreate(
                name="Scenario Test",
                simulation_type="single_agent",
                target_type="agent",
                target_id="ag-agent-1",
            ),
            user_id=user_id,
        )
        v1 = await service.create_version(
            simulation_id=sim.id,
            data=SimulationVersionCreate(),
            user_id=user_id,
        )
        await service.publish_version(v1.id, user_id=user_id)

        # Create scenario
        scenario = await service.create_scenario(
            version_id=v1.id,
            data=SimulationScenarioCreate(
                name="Tool Interception Check",
                input="Execute task and log result",
                scenario_type="security",
                expected_behavior={"output_required": True},
                assertions=[
                    {"type": "no_external_side_effect"},
                    {"type": "must_complete"},
                ],
            ),
        )
        assert scenario.name == "Tool Interception Check"

        # Run Simulation Scenario
        run = await service.run_simulation(
            simulation_id=sim.id,
            version_id=v1.id,
            scenario_id=scenario.id,
            seed=42,
            user_id=user_id,
        )
        assert run.status in ["completed", "queued"]
        assert run.seed == 42
        assert run.simulation_id == sim.id

    @pytest.mark.asyncio
    async def test_simulation_suite_and_regressions(self, db_session):
        service = SimulationService(db_session)
        ws_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())

        # Create Suite
        suite = await service.create_suite(
            workspace_id=ws_id,
            data=SimulationSuiteCreate(
                name="Regression Suite A",
                target_type="agent",
                target_id="ag-target-1",
            ),
            user_id=user_id,
        )
        assert suite.name == "Regression Suite A"
        assert suite.status == "active"

    @pytest.mark.asyncio
    async def test_scopes_registry_registered(self):
        # Developer Platform Scopes
        scopes = ScopeRegistry.get_all_scopes()
        assert "simulations:read" in scopes
        assert "simulations:write" in scopes
        assert "simulations:execute" in scopes
