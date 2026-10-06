"""
Comprehensive Unit and Integration Tests for Step 43:
AI Outcome Intelligence & Work Impact Layer.
"""
import uuid
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from backend.app.services.outcomes.errors import (
    OutcomeError,
    ObjectiveNotFoundError,
    OutcomeNotFoundError,
    EvidenceNotFoundError,
    DecisionNotFoundError,
    RequirementNotMetError,
    CausalityClaimForbiddenError,
    SubjectiveScoreForbiddenError,
    HumanImpersonationError,
    OutcomeTenantViolationError,
    MissingBaselineError,
    FabricatedMetricError,
)
from backend.app.services.outcomes.registry import (
    ObjectiveType,
    ObjectiveStatus,
    OutcomeType,
    OutcomeStatus,
    OutcomeConfidence,
    TargetMetricType,
    MeasurementSource,
    EvidenceType,
    EvidenceStatus,
    MilestoneStatus,
    WorkDecisionType,
    WorkDecisionStatus,
    AttributionType,
    AttributionSource,
    ImpactAnalysisType,
    OutcomeHealthStatus,
)
from backend.app.services.outcomes.policies import (
    OutcomePolicyEngine,
    TenantIsolationPolicy,
    BaselinePolicy,
)
from backend.app.services.outcomes.validators import (
    OutcomeConditionValidator,
    DeterministicConditionEvaluator,
)
from backend.app.services.outcomes.health import HealthEvaluator
from backend.app.services.outcomes.attribution import (
    OutcomeAttributionAnalyzer,
    DeterministicAttributionBuilder,
)
from backend.app.services.outcomes.impact import ImpactCalculator
from backend.app.services.outcomes.verification import OutcomeVerificationService
from backend.app.services.outcomes.recommendations import OutcomeRecommendationService
from backend.app.services.outcomes.lifecycle import (
    OutcomeStateMachine,
    ObjectiveStateMachine,
    DecisionStateMachine,
)
from backend.app.services.outcomes.graph import OutcomeGraphService
from backend.app.services.outcomes.models import (
    Objective,
    OutcomeTarget,
    Outcome,
    OutcomeWorkLink,
    OutcomeEvidence,
    OutcomeMeasurement,
    OutcomeMilestone,
    WorkDecision,
    OutcomeAttribution,
    ImpactAnalysis,
)
from backend.app.services.developer_platform.scopes import ScopeRegistry
from backend.app.services.events.constants import SystemEventType
from backend.app.services.jobs.constants import JobType


# =============================================================================
# 1. POLICY & INTEGRITY CHECKS (ZERO FABRICATED METRICS, SAFE ATTRIBUTION)
# =============================================================================

class TestOutcomePolicies:
    def test_forbid_subjective_scores(self):
        """Must reject arbitrary AI IQ or subjective quality scores."""
        engine = OutcomePolicyEngine()
        with pytest.raises(SubjectiveScoreForbiddenError):
            engine.validate_measurement(metric_name="ai_intelligence_score", value=94)

        with pytest.raises(SubjectiveScoreForbiddenError):
            engine.validate_measurement(metric_name="agent_iq", value=140)

        with pytest.raises(SubjectiveScoreForbiddenError):
            engine.validate_measurement(metric_name="subjective_rating", value=8.5)

        # Factual measurements pass
        engine.validate_measurement(metric_name="time_to_remediate_minutes", value=42.5)
        engine.validate_measurement(metric_name="issues_closed_count", value=5)

    def test_causality_claim_forbidden_without_evidence(self):
        """Attribution cannot claim direct causation without explicit evidence."""
        engine = OutcomePolicyEngine()
        with pytest.raises(CausalityClaimForbiddenError):
            engine.validate_attribution(
                attribution_type=AttributionType.DIRECT,
                evidence_ids=[],
                explanation="Agent completely solved problem",
            )

        # Valid with supporting evidence
        engine.validate_attribution(
            attribution_type=AttributionType.DIRECT,
            evidence_ids=["ev-123"],
            explanation="Execution logs show agent generated the exact artifact committed",
        )

        # Contributing attribution does not claim single-handed causation
        engine.validate_attribution(
            attribution_type=AttributionType.CONTRIBUTING,
            evidence_ids=[],
            explanation="Agent analyzed context",
        )

    def test_missing_baseline_never_fabricates_savings(self):
        """Cannot fabricate business savings or time saved if baseline is missing."""
        calc = ImpactCalculator()
        with pytest.raises(MissingBaselineError):
            calc.calculate_time_saved(baseline_minutes=None, observed_minutes=45)

        with pytest.raises(MissingBaselineError):
            calc.calculate_cost_impact(baseline_cost=None, observed_cost=12.5)

        # Valid comparison
        diff = calc.calculate_time_saved(baseline_minutes=90, observed_minutes=45)
        assert diff == -45

    def test_ai_decision_cannot_be_represented_as_human(self):
        """AI-assisted or agent decisions cannot masquerade as human decisions."""
        engine = OutcomePolicyEngine()
        with pytest.raises(HumanImpersonationError):
            engine.validate_decision_provenance(
                decision_type=WorkDecisionType.HUMAN,
                provenance={"agent_id": "agent-007", "model_provider": "openai/gpt-4"},
            )

        # Valid AI decision captures provenance properly
        engine.validate_decision_provenance(
            decision_type=WorkDecisionType.AI_ASSISTED,
            provenance={"agent_id": "agent-007", "model_provider": "openai/gpt-4"},
        )

    def test_tenant_isolation_policy(self):
        """Cross-tenant operations are strictly rejected."""
        policy = TenantIsolationPolicy()
        with pytest.raises(OutcomeTenantViolationError):
            policy.check_tenant_match(
                expected_tenant="workspace-a",
                actual_tenant="workspace-b",
            )

        policy.check_tenant_match(
            expected_tenant="workspace-a",
            actual_tenant="workspace-a",
        )


# =============================================================================
# 2. DETERMINISTIC VERIFICATION & EVIDENCE CONDITIONS
# =============================================================================

class TestOutcomeVerificationEngine:
    @pytest.mark.asyncio
    async def test_outcome_cannot_become_verified_without_required_evidence(self):
        """Critical check 1: Outcome cannot become verified without required evidence."""
        verifier = OutcomeVerificationService()
        outcome = {
            "id": "out-1",
            "name": "Doc overhaul",
            "status": "observed",
            "evidence": [],
            "requirements": {"required_evidence": True},
        }

        with pytest.raises(RequirementNotMetError) as exc_info:
            await verifier.verify_outcome(outcome, human_user_id="user-1")
        assert "evidence" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_ai_generated_evidence_cannot_automatically_become_human_verified(self):
        """Critical check 2: AI-generated evidence cannot automatically become human-verified."""
        verifier = OutcomeVerificationService()
        outcome = {
            "id": "out-2",
            "name": "Security audit",
            "status": "observed",
            "evidence": [
                {
                    "id": "ev-ai",
                    "evidence_type": "execution_result",
                    "source_type": "agent_run",
                    "is_human_confirmed": False,
                }
            ],
            "requirements": {
                "required_evidence": True,
                "required_human_confirmation": True,
            },
        }

        # Attempt to verify without human confirmation
        with pytest.raises(RequirementNotMetError) as exc_info:
            await verifier.verify_outcome(outcome, human_user_id=None)
        assert "human confirmation" in str(exc_info.value).lower()

    def test_agent_completion_does_not_mark_outcome_verified(self):
        """Critical check 3: Agent completion cannot automatically mark an outcome verified."""
        state_machine = OutcomeStateMachine()
        outcome = {
            "id": "out-3",
            "status": "planned",
            "confidence": "unverified",
        }

        # Agent run completion can transition to OBSERVED, never directly to VERIFIED
        new_status = state_machine.transition_on_agent_complete(outcome)
        assert new_status == OutcomeStatus.OBSERVED
        assert new_status != OutcomeStatus.VERIFIED

    def test_deterministic_condition_evaluator(self):
        """Condition evaluator supports AND/OR trees without arbitrary code expressions."""
        evaluator = DeterministicConditionEvaluator()
        context = {
            "has_artifact": True,
            "evaluation_passed": True,
            "has_approval": False,
        }

        rule_and = {
            "and": [
                {"field": "has_artifact", "op": "eq", "value": True},
                {"field": "evaluation_passed", "op": "eq", "value": True},
            ]
        }
        assert evaluator.evaluate(rule_and, context) is True

        rule_or = {
            "or": [
                {"field": "has_approval", "op": "eq", "value": True},
                {"field": "evaluation_passed", "op": "eq", "value": True},
            ]
        }
        assert evaluator.evaluate(rule_or, context) is True

        rule_failing = {
            "and": [
                {"field": "has_artifact", "op": "eq", "value": True},
                {"field": "has_approval", "op": "eq", "value": True},
            ]
        }
        assert evaluator.evaluate(rule_failing, context) is False


# =============================================================================
# 3. DETERMINISTIC HEALTH & STALENESS
# =============================================================================

class TestOutcomeHealthAndStaleness:
    def test_explainable_deterministic_health_reasons(self):
        """Critical check 12: Objective health is explainable and deterministic."""
        evaluator = HealthEvaluator()
        now = datetime.now(timezone.utc)

        # Objective with overdue milestone
        milestones = [
            {
                "id": "m-1",
                "name": "Phase 1",
                "status": "planned",
                "due_at": now - timedelta(days=2),
            }
        ]
        outcomes = []
        targets = []

        health = evaluator.evaluate_objective_health(
            milestones=milestones,
            outcomes=outcomes,
            targets=targets,
        )
        assert health["status"] == OutcomeHealthStatus.AT_RISK
        assert any("overdue" in r.lower() for r in health["reasons"])

    def test_blocked_milestone_marks_blocked_health(self):
        evaluator = HealthEvaluator()
        milestones = [
            {
                "id": "m-2",
                "name": "Sec Review",
                "status": "blocked",
                "due_at": None,
            }
        ]
        health = evaluator.evaluate_objective_health(
            milestones=milestones,
            outcomes=[],
            targets=[],
        )
        assert health["status"] == OutcomeHealthStatus.BLOCKED
        assert any("blocked" in r.lower() for r in health["reasons"])

    def test_staleness_detection(self):
        """Stale outcome detection marks STALE and explains why."""
        evaluator = HealthEvaluator()
        old_time = datetime.now(timezone.utc) - timedelta(days=45)
        outcome = {
            "id": "out-stale",
            "status": "observed",
            "updated_at": old_time,
            "targets": [{"updated_at": old_time}],
        }

        res = evaluator.check_staleness(outcome, validity_days=30)
        assert res["is_stale"] is True
        assert "not updated for" in res["reason"]


# =============================================================================
# 4. ATTRIBUTION SAFETY & AI RECOMMENDATIONS
# =============================================================================

class TestAttributionAndRecommendations:
    def test_deterministic_attribution_builder(self):
        """Attributions strictly categorized as DIRECT, SUPPORTING, CONTRIBUTING, BLOCKING."""
        builder = DeterministicAttributionBuilder()
        attr = builder.build_attribution(
            outcome_id="out-10",
            resource_type="task",
            resource_id="task-42",
            relationship="produced",
            evidence_ids=["ev-run-log"],
            is_direct=True,
        )
        assert attr["attribution_type"] == AttributionType.DIRECT
        assert attr["source"] == AttributionSource.OBSERVED

    def test_ai_generated_attribution_labeled(self):
        """AI Gateway suggested attribution labeled AI_GENERATED_ATTRIBUTION."""
        analyzer = OutcomeAttributionAnalyzer()
        res = analyzer.label_ai_attribution(
            suggested_type="contributing",
            explanation="Likely assisted based on commit history timestamps",
        )
        assert res["source"] == AttributionSource.AI_GENERATED
        assert res["confidence"] == "estimated"

    def test_recommendations_never_bypass_governance(self):
        """Recommendations only propose actions, never execute privileged changes."""
        service = OutcomeRecommendationService()
        missing_evidence_context = {
            "outcome_id": "out-50",
            "status": "observed",
            "missing_evidence": ["test_coverage_report"],
            "has_human_review": False,
        }

        recs = service.generate_recommendations(missing_evidence_context)
        assert len(recs) > 0
        for rec in recs:
            assert rec["is_privileged_execution"] is False
            assert "reason" in rec
            assert rec["action"] in [
                "collect_missing_evidence",
                "request_human_review",
                "run_evaluation",
                "run_simulation",
                "review_blocked_milestone",
            ]


# =============================================================================
# 5. ASYNC DB REPOSITORY & MODEL INTEGRATION
# =============================================================================

@pytest.mark.asyncio
class TestOutcomeDatabaseIntegration:
    async def test_objective_and_outcome_lifecycle_in_db(self, db_session):
        workspace_id = f"ws-{uuid.uuid4().hex[:8]}"
        user_id = f"user-{uuid.uuid4().hex[:8]}"

        # 1. Create Objective
        obj = Objective(
            workspace_id=workspace_id,
            name="Improve API Latency",
            description="Reduce p99 latency to under 200ms",
            objective_type=ObjectiveType.ENGINEERING.value,
            status=ObjectiveStatus.ACTIVE.value,
            priority="high",
            created_by=user_id,
        )
        db_session.add(obj)
        await db_session.flush()
        assert obj.id is not None

        # 2. Add Target
        target = OutcomeTarget(
            objective_id=obj.id,
            name="P99 Latency Target",
            metric_type=TargetMetricType.DURATION.value,
            baseline_value=450.0,
            target_value=180.0,
            target_unit="ms",
            current_value=420.0,
            measurement_source=MeasurementSource.SYSTEM.value,
        )
        db_session.add(target)

        # 3. Add Milestone
        milestone = OutcomeMilestone(
            objective_id=obj.id,
            name="Benchmarking & Profiling",
            status=MilestoneStatus.COMPLETED.value,
            owner_user_id=user_id,
        )
        db_session.add(milestone)

        # 4. Add Outcome Deliverable
        outcome = Outcome(
            workspace_id=workspace_id,
            objective_id=obj.id,
            name="Optimized Query Indexing Deliverable",
            outcome_type=OutcomeType.OPTIMIZATION.value,
            status=OutcomeStatus.OBSERVED.value,
            confidence=OutcomeConfidence.SUPPORTED.value,
            created_by=user_id,
            observed_at=datetime.now(timezone.utc),
        )
        db_session.add(outcome)
        await db_session.flush()

        # 5. Add Evidence
        evidence = OutcomeEvidence(
            outcome_id=outcome.id,
            evidence_type=EvidenceType.EXECUTION_RESULT.value,
            source_type="run",
            source_id="run-benchmark-99",
            description="Benchmark run confirmed p99 dropped from 450ms to 175ms",
            snapshot={"baseline_ms": 450, "observed_ms": 175},
        )
        db_session.add(evidence)

        # 6. Add Factual Measurement
        measurement = OutcomeMeasurement(
            outcome_id=outcome.id,
            target_id=target.id,
            metric_name="p99_latency",
            value=175.0,
            unit="ms",
            measurement_source=MeasurementSource.SYSTEM.value,
            observed_at=datetime.now(timezone.utc),
        )
        db_session.add(measurement)

        # 7. Add Work Decision
        decision = WorkDecision(
            workspace_id=workspace_id,
            objective_id=obj.id,
            outcome_id=outcome.id,
            title="Adopt Composite Index Migration",
            description="Approved migration after benchmark evidence validated",
            decision_type=WorkDecisionType.HUMAN.value,
            status=WorkDecisionStatus.APPROVED.value,
            decision_owner=user_id,
        )
        db_session.add(decision)

        await db_session.commit()

        # Verify DB records
        assert obj.id is not None
        assert outcome.id is not None
        assert evidence.id is not None
        assert measurement.id is not None
        assert decision.id is not None

    async def test_cross_tenant_isolation_in_db(self, db_session):
        """Cross-tenant queries cannot access outcomes of another workspace."""
        ws_a = f"ws-a-{uuid.uuid4().hex[:6]}"
        ws_b = f"ws-b-{uuid.uuid4().hex[:6]}"

        outcome_a = Outcome(
            workspace_id=ws_a,
            name="Confidential Acquisition Brief",
            outcome_type=OutcomeType.RESEARCH_FINDING.value,
            created_by="user-a",
        )
        db_session.add(outcome_a)
        await db_session.commit()

        # Querying with workspace B filter
        from sqlalchemy import select
        res = await db_session.execute(
            select(Outcome).where(Outcome.workspace_id == ws_b)
        )
        found = res.scalars().all()
        assert len(found) == 0


# =============================================================================
# 6. SYSTEM EVENT BUS, JOBS, & SCOPE INTEGRATION
# =============================================================================

class TestSystemIntegration:
    def test_outcome_events_registered(self):
        """All required outcome event types must exist in SystemEventType."""
        required_events = [
            "objective.created",
            "objective.updated",
            "objective.at_risk",
            "objective.completed",
            "milestone.created",
            "milestone.completed",
            "milestone.blocked",
            "milestone.missed",
            "outcome.created",
            "outcome.updated",
            "outcome.observed",
            "outcome.verified",
            "outcome.disputed",
            "outcome.failed",
            "outcome.stale",
            "outcome.evidence_added",
            "outcome.measurement_added",
            "outcome.attribution_created",
            "decision.created",
            "decision.approved",
            "decision.rejected",
        ]
        for evt in required_events:
            assert evt in SystemEventType._value2member_map_, f"Missing event: {evt}"

    def test_outcome_job_types_registered(self):
        """Outcome background job types registered."""
        required_jobs = [
            "outcome_measurement",
            "outcome_verification",
            "outcome_health_refresh",
            "outcome_impact_analysis",
            "outcome_recommendation",
            "outcome_graph_update",
        ]
        for j in required_jobs:
            assert j in JobType._value2member_map_, f"Missing job type: {j}"

    def test_developer_platform_scopes_registered(self):
        """Developer platform API scopes registered."""
        required_scopes = [
            "objectives:read",
            "objectives:write",
            "outcomes:read",
            "outcomes:write",
            "outcomes:verify",
            "decisions:read",
            "decisions:write",
        ]
        for sc in required_scopes:
            assert sc in ScopeRegistry.SCOPES, f"Missing API scope: {sc}"
        assert ScopeRegistry.is_sensitive("outcomes:verify") is True

    def test_bounded_graph_traversal_constraints(self):
        """Graph traversal must never exceed 3 hops."""
        assert OutcomeGraphService.MAX_HOPS == 3
        assert OutcomeGraphService.DEFAULT_HOPS in [1, 2, 3]

    def test_python_sdk_methods_exist(self):
        """Python SDK exposes objectives, outcomes, decisions resources and methods."""
        from sdk.python.ai_work_layer.client import (
            ObjectivesResource,
            OutcomesResource,
            DecisionsResource,
        )
        assert hasattr(ObjectivesResource, "create")
        assert hasattr(ObjectivesResource, "get")
        assert hasattr(ObjectivesResource, "list")
        assert hasattr(ObjectivesResource, "update")
        assert hasattr(ObjectivesResource, "delete")
        assert hasattr(ObjectivesResource, "get_health")
        assert hasattr(ObjectivesResource, "get_work_map")

        assert hasattr(OutcomesResource, "create")
        assert hasattr(OutcomesResource, "get")
        assert hasattr(OutcomesResource, "list")
        assert hasattr(OutcomesResource, "add_evidence")
        assert hasattr(OutcomesResource, "verify")
        assert hasattr(OutcomesResource, "dispute")
        assert hasattr(OutcomesResource, "get_impact")
        assert hasattr(OutcomesResource, "get_work")
        assert hasattr(OutcomesResource, "get_graph")

        assert hasattr(DecisionsResource, "create")
        assert hasattr(DecisionsResource, "get")
        assert hasattr(DecisionsResource, "list")
        assert hasattr(DecisionsResource, "approve")
        assert hasattr(DecisionsResource, "reject")

