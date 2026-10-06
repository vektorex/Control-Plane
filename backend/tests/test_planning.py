"""
Comprehensive Unit and Integration Tests for Step 44:
AI Work Planning, Capacity & Resource Optimization Layer.
"""
from datetime import datetime, timezone, timedelta
import uuid
import pytest

from backend.app.services.planning.capacity import CapacityManager
from backend.app.services.planning.constraints import ConstraintEngine
from backend.app.services.planning.dependency_graph import PlanningDependencyGraph
from backend.app.services.planning.errors import (
    CapacityExceededError,
    DependencyCycleError,
    DirectExecutionForbiddenError,
    FabricatedCapacityError,
    HardConstraintViolationError,
    HiddenAggregateScoreForbiddenError,
    ImmutableVersionError,
    PlanStaleError,
    PlanningError,
    PlanningTenantViolationError,
    PrivacyViolationError,
    SubjectiveRankingForbiddenError,
    UnauthorizedCapacityReservationError,
)
from backend.app.services.planning.lifecycle import PlanLifecycleManager
from backend.app.services.planning.models import (
    CapacityReservation,
    CapacitySnapshot,
    PlanningConstraint,
    PlanningDependency,
    PlanningItem,
    ResourceAvailability,
    WorkPlan,
    WorkPlanVersion,
    WorkResource,
)
from backend.app.services.planning.optimizer import CandidateComparison
from backend.app.services.planning.policies import PlanningPolicyEngine
from backend.app.services.planning.recommendations import PlanningRecommendationGenerator
from backend.app.services.planning.resources import ResourceMatcher
from backend.app.services.planning.scenarios import ScenarioEngine
from backend.app.services.planning.scheduler import ScheduleGenerator
from backend.app.services.planning.validators import PlanValidator


class TestPlanningPolicies:
    """Security, Privacy, and Factual Policy Enforcement."""

    def test_forbid_subjective_employee_rankings(self):
        with pytest.raises(SubjectiveRankingForbiddenError):
            PlanningPolicyEngine.validate_no_subjective_rankings("Assign to the best employee for speed.")

        with pytest.raises(SubjectiveRankingForbiddenError):
            PlanningPolicyEngine.validate_no_subjective_rankings("Identify top performer and delegate tasks.")

        # Factual description passes without error
        PlanningPolicyEngine.validate_no_subjective_rankings("Assign to resource with required python capability.")

    def test_forbid_hidden_aggregate_score(self):
        with pytest.raises(HiddenAggregateScoreForbiddenError):
            PlanningPolicyEngine.validate_no_hidden_aggregate_score({"overall_score": 95, "duration": 40})

        with pytest.raises(HiddenAggregateScoreForbiddenError):
            PlanningPolicyEngine.validate_no_hidden_aggregate_score({"plan_magic_score": 88})

        # Multi-dimensional factual metrics pass
        PlanningPolicyEngine.validate_no_hidden_aggregate_score({
            "duration_minutes": 120,
            "cost_usd": 15.5,
            "human_workload_minutes": 45,
            "agent_workload_minutes": 75,
        })

    def test_tenant_isolation_violation(self):
        ws_1 = str(uuid.uuid4())
        ws_2 = str(uuid.uuid4())

        with pytest.raises(PlanningTenantViolationError):
            PlanningPolicyEngine.validate_tenant_isolation(ws_1, ws_2)

        # Same workspace passes
        PlanningPolicyEngine.validate_tenant_isolation(ws_1, ws_1)

    def test_human_privacy_protection(self):
        with pytest.raises(PrivacyViolationError):
            PlanningPolicyEngine.validate_human_privacy("human", ["personal_calendar", "workload"])

        with pytest.raises(PrivacyViolationError):
            PlanningPolicyEngine.validate_human_privacy("human", ["medical", "habits"])

        # Explicit work availability passes
        PlanningPolicyEngine.validate_human_privacy("human", ["declared_availability", "work_hours"])
        PlanningPolicyEngine.validate_human_privacy("agent", ["personal_calendar"])

    def test_fabricated_capacity_forbidden(self):
        with pytest.raises(FabricatedCapacityError):
            PlanningPolicyEngine.validate_no_fabricated_capacity("unknown", 40.0)

        # Verified or manual capacity passes
        PlanningPolicyEngine.validate_no_fabricated_capacity("calendar", 40.0)
        PlanningPolicyEngine.validate_no_fabricated_capacity("manual", 20.0)

    def test_direct_execution_forbidden(self):
        with pytest.raises(DirectExecutionForbiddenError):
            PlanningPolicyEngine.validate_no_direct_execution()

    def test_unauthorized_reservation_forbidden(self):
        with pytest.raises(UnauthorizedCapacityReservationError):
            PlanningPolicyEngine.validate_reservation_authorization(is_authorized=False)

        PlanningPolicyEngine.validate_reservation_authorization(is_authorized=True)

    def test_stale_plan_activation_blocked(self):
        with pytest.raises(PlanStaleError) as exc_info:
            PlanningPolicyEngine.validate_activation_safety(
                is_stale=True,
                staleness_reasons=["Deadline moved", "Agent policy modified"],
            )
        assert "Deadline moved" in str(exc_info.value)

        PlanningPolicyEngine.validate_activation_safety(is_stale=False)


class TestDependencyGraphAndCycles:
    """Dependency Graph, Cycle Detection, and CPM Analysis."""

    def test_cycle_detection_and_rejection(self):
        graph = PlanningDependencyGraph()
        graph.add_node("item_A", 30)
        graph.add_node("item_B", 45)
        graph.add_node("item_C", 20)

        graph.add_edge("item_A", "item_B", "finish_to_start")
        graph.add_edge("item_B", "item_C", "finish_to_start")
        graph.add_edge("item_C", "item_A", "finish_to_start")  # Cycle!

        cycle = graph.detect_cycles()
        assert cycle is not None
        assert len(cycle) >= 3

        with pytest.raises(DependencyCycleError) as exc_info:
            graph.validate_no_cycles()
        assert "cycle detected" in str(exc_info.value).lower()

    def test_topological_sort_success(self):
        graph = PlanningDependencyGraph()
        graph.add_node("item_1", 20)
        graph.add_node("item_2", 30)
        graph.add_node("item_3", 15)

        graph.add_edge("item_1", "item_2")
        graph.add_edge("item_2", "item_3")

        order = graph.topological_sort()
        assert order == ["item_1", "item_2", "item_3"]

    def test_critical_path_calculation(self):
        graph = PlanningDependencyGraph()
        # Item 1 (30m) -> Item 2 (60m) [Total 90m - Critical Path]
        # Item 3 (10m) [Slack = 80m]
        graph.add_node("item_1", 30)
        graph.add_node("item_2", 60)
        graph.add_node("item_3", 10)

        graph.add_edge("item_1", "item_2", "finish_to_start")

        cpm = graph.compute_critical_path()
        assert cpm["total_duration"] == 90.0
        assert "item_1" in cpm["critical_path"]
        assert "item_2" in cpm["critical_path"]
        assert "item_3" not in cpm["critical_path"]
        assert cpm["slack"]["item_3"] == 80.0


class TestResourceAndCapabilityMatching:
    """Factual Suitability Matching without Subjective Ranking."""

    def test_capability_matching_factual(self):
        res = WorkResource(
            id="agent-1",
            workspace_id="ws-1",
            resource_type="agent",
            resource_ref="ref-1",
            name="Documentation Agent",
            status="active",
            capabilities=["python", "documentation", "markdown"],
            availability_policy={"max_concurrent_runs": 3},
        )

        # Requires capabilities that agent possesses
        match_success = ResourceMatcher.match_item_to_resource(
            item_capabilities=["python", "documentation"],
            resource=res,
            current_concurrency=1,
        )
        assert match_success.matched is True
        assert "matches all required capabilities" in match_success.explanation

        # Requires capability agent lacks
        match_fail = ResourceMatcher.match_item_to_resource(
            item_capabilities=["python", "k8s_deploy"],
            resource=res,
            current_concurrency=1,
        )
        assert match_fail.matched is False
        assert "k8s_deploy" in match_fail.missing_capabilities

    def test_concurrency_limit_check(self):
        res = WorkResource(
            id="agent-2",
            workspace_id="ws-1",
            resource_type="agent",
            resource_ref="ref-2",
            name="Analysis Agent",
            status="active",
            capabilities=["analysis"],
            availability_policy={"max_concurrent_runs": 2},
        )

        # Concurrency limit reached (current 2 >= max 2)
        match_concurrency_fail = ResourceMatcher.match_item_to_resource(
            item_capabilities=["analysis"],
            resource=res,
            current_concurrency=2,
        )
        assert match_concurrency_fail.matched is False
        assert "reached max concurrency limit" in match_concurrency_fail.explanation


class TestCapacityAndReservations:
    """Measurable Capacity, Honest Unknowns, and Reservations."""

    def test_calculate_capacity_factual(self):
        now = datetime.now(timezone.utc)
        res = WorkResource(
            id="res-1",
            workspace_id="ws-1",
            resource_type="agent",
            resource_ref="ref-1",
            name="Worker 1",
            status="active",
        )
        avail = ResourceAvailability(
            id="av-1",
            resource_id="res-1",
            start_at=now,
            end_at=now + timedelta(days=7),
            capacity_units=10.0,
            reserved_units=0.0,
            source="manual",
        )
        reservations = [
            CapacityReservation(
                id="r-1",
                resource_id="res-1",
                start_at=now,
                end_at=now + timedelta(days=2),
                units=3.0,
                status="reserved",
                created_by="user-1",
            )
        ]

        cap = CapacityManager.calculate_resource_capacity(
            resource=res,
            availabilities=[avail],
            reservations=reservations,
            window_start=now,
            window_end=now + timedelta(days=7),
        )

        assert cap["available_units"] == 10.0
        assert cap["reserved_units"] == 3.0
        assert cap["remaining_units"] == 7.0
        assert cap["is_unknown"] is False

    def test_reservation_exceeds_capacity(self):
        with pytest.raises(CapacityExceededError) as exc_info:
            CapacityManager.evaluate_reservation_request(
                resource_id="res-1",
                available_units=5.0,
                current_reserved=4.0,
                requested_units=2.0,  # 4 + 2 = 6 > 5
                is_authorized=True,
            )
        assert "capacity exceeded" in str(exc_info.value).lower()

    def test_forecast_integrity_labeled(self):
        now = datetime.now(timezone.utc)
        res_with_avail = WorkResource(id="r1", workspace_id="ws", resource_type="agent", resource_ref="1", name="A1")
        res_without_avail = WorkResource(id="r2", workspace_id="ws", resource_type="human", resource_ref="2", name="H1")

        avail = ResourceAvailability(
            id="a1", resource_id="r1",
            start_at=now, end_at=now + timedelta(days=7),
            capacity_units=8.0, source="system",
        )

        forecast = CapacityManager.generate_capacity_forecast(
            resources=[res_with_avail, res_without_avail],
            availabilities=[avail],
            reservations=[],
            planned_demands=[{"estimated_units": 4.0}],
            period_start=now,
            period_end=now + timedelta(days=7),
        )

        assert forecast["is_forecast"] is True
        assert forecast["available_capacity"] == 8.0
        assert forecast["planned_demand"] == 4.0
        assert forecast["remaining_capacity"] == 4.0
        assert forecast["unknown_capacity_count"] == 1  # H1 has no recorded availability


class TestConstraintsAndSchedules:
    """Deterministic Constraints and Multi-Dimensional Candidate Comparison."""

    def test_hard_constraint_deadline_violation(self):
        now = datetime.now(timezone.utc)
        deadline = now + timedelta(hours=2)

        constraint = PlanningConstraint(
            id="c-1",
            work_plan_version_id="v-1",
            constraint_type="deadline",
            configuration={"deadline": deadline.isoformat()},
            hard_constraint=True,
        )

        candidate_overdue = {
            "project_end": now + timedelta(hours=3),  # 3 hours > 2 hours deadline
        }

        with pytest.raises(HardConstraintViolationError) as exc_info:
            ConstraintEngine.evaluate_all(
                constraints=[constraint],
                candidate_schedule=candidate_overdue,
                raise_on_hard_violation=True,
            )
        assert "exceeds deadline" in str(exc_info.value)

    def test_multi_dimensional_candidate_comparison(self):
        candidates = [
            {
                "name": "Candidate A",
                "estimated_duration": 60,
                "estimated_cost": 2.50,
                "schedule": {
                    "task-1": {"duration_minutes": 60, "resource_type": "agent", "resource_id": "agent-1"},
                },
                "assumptions": ["Low concurrency"],
            },
            {
                "name": "Candidate B",
                "estimated_duration": 40,
                "estimated_cost": 5.00,
                "schedule": {
                    "task-1": {"duration_minutes": 40, "resource_type": "human", "resource_id": "human-1"},
                },
                "assumptions": ["High human intervention"],
            },
        ]

        comparison = CandidateComparison.compare_candidates(candidates)
        assert len(comparison) == 2
        assert comparison[0]["duration_minutes"] == 60
        assert comparison[0]["cost_usd"] == 2.50
        assert comparison[0]["agent_workload_minutes"] == 60
        assert comparison[1]["human_workload_minutes"] == 40
        # Verified: No single aggregate score manufactured in comparison
        assert "overall_score" not in comparison[0]


class TestScenariosAndRecommendations:
    """Isolated What-If Scenarios and Non-Privileged Advisory Recommendations."""

    def test_what_if_scenario_isolation(self):
        item = PlanningItem(
            id="it-1",
            work_plan_version_id="v-1",
            resource_type="task",
            resource_id="task-1",
            name="Run Workflow",
            estimated_duration=30,
            required_capabilities=[],
            status="planned",
        )

        res = WorkResource(
            id="r-1",
            workspace_id="ws-1",
            resource_type="workflow",
            resource_ref="wf-1",
            name="Workflow Worker",
            status="active",
        )

        # Apply +100% duration overrun simulation (multiplier = 2.0)
        output = ScenarioEngine.run_scenario(
            base_items=[item],
            base_dependencies=[],
            base_resources=[res],
            base_constraints=[],
            modifications={"duration_multiplier": 2.0},
        )

        assert output["is_simulation"] is True
        assert output["simulated_candidates_count"] >= 1
        # Original item duration is NOT modified (still 30 minutes)
        assert item.estimated_duration == 30

    def test_recommendations_generation_advisory(self):
        item_missing_cap = PlanningItem(
            id="it-2",
            work_plan_version_id="v-1",
            resource_type="task",
            resource_id="task-2",
            name="Deploy Microservice",
            required_capabilities=["kubernetes_admin"],
            status="planned",
        )

        res = WorkResource(
            id="r-2",
            workspace_id="ws-1",
            resource_type="agent",
            resource_ref="agent-2",
            name="Junior Agent",
            status="active",
            capabilities=["python"],  # Does NOT have kubernetes_admin
        )

        recs = PlanningRecommendationGenerator.generate_recommendations(
            items=[item_missing_cap],
            blockers=[],
            resources=[res],
        )

        assert len(recs) == 1
        assert recs[0]["recommendation_type"] == "use_another_agent"
        assert "kubernetes_admin" in recs[0]["reason"]


class TestPlanLifecycleAndVersionImmutability:
    """Plan Transitions and Published Version Immutability."""

    def test_version_immutability_enforced(self):
        published_version = WorkPlanVersion(
            id="v-published",
            work_plan_id="plan-1",
            version=1,
            published_at=datetime.now(timezone.utc),
            created_by="user-1",
        )

        with pytest.raises(ImmutableVersionError) as exc_info:
            PlanLifecycleManager.enforce_version_immutability(published_version)
        assert "immutable" in str(exc_info.value).lower()

        # Unpublished draft version passes
        draft_version = WorkPlanVersion(
            id="v-draft",
            work_plan_id="plan-1",
            version=2,
            published_at=None,
            created_by="user-1",
        )
        PlanLifecycleManager.enforce_version_immutability(draft_version)

    def test_invalid_lifecycle_transition(self):
        # Cannot jump from draft to active without approval
        with pytest.raises(PlanningError) as exc_info:
            PlanLifecycleManager.validate_transition("draft", "active")
        assert "Invalid work plan status transition" in str(exc_info.value)

        # Valid transitions pass
        PlanLifecycleManager.validate_transition("draft", "proposed")
        PlanLifecycleManager.validate_transition("proposed", "approved")
        PlanLifecycleManager.validate_transition("approved", "active")
        PlanLifecycleManager.validate_transition("active", "paused")
