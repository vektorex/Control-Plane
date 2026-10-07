from fastapi import APIRouter
from backend.app.api.routes.auth import router as auth_router
from backend.app.api.routes.context import router as context_router
from backend.app.api.routes.documents import router as documents_router
from backend.app.api.routes.health import router as health_router
from backend.app.api.routes.llm import router as llm_router
from backend.app.api.routes.models import router as models_router
from backend.app.api.routes.projects import router as projects_router
from backend.app.api.routes.runs import router as runs_router
from backend.app.api.routes.tasks import router as tasks_router
from backend.app.api.routes.tools import router as tools_router
from backend.app.api.routes.workspaces import router as workspaces_router
from backend.app.api.routes.evaluation import router as evaluation_router
from backend.app.api.routes.analytics import router as analytics_router, admin_router as observability_admin_router
from backend.app.api.routes.workflows import router as workflows_router
from backend.app.api.routes.connectors import router as connectors_router
from backend.app.api.routes.memory import router as memory_router
from backend.app.api.routes.hitl import router as hitl_router
from backend.app.api.routes.notifications import (
    router as notifications_router,
    webhooks_router,
    preferences_router,
    deliveries_router,
)
from backend.app.api.routes.gateway import router as gateway_router
from backend.app.api.routes.replay import router as replay_router
from backend.app.api.routes.evaluation_lab import router as evaluation_lab_router
from backend.app.api.routes.triggers import router as triggers_router
from backend.app.api.routes.jobs import router as jobs_router
from backend.app.api.routes.events import events_router
from backend.app.api.routes.organizations import organizations_router, invitations_router
from backend.app.api.routes.prompts import router as prompts_router
from backend.app.api.routes.prompt_experiments import router as prompt_experiments_router
from backend.app.api.routes.knowledge_graph import router as knowledge_graph_router
from backend.app.api.routes.artifacts import router as artifacts_router
from backend.app.api.routes.cache import router as cache_router
from backend.app.api.routes.governance import router as governance_router
from backend.app.api.routes.data_governance import router as data_governance_router
from backend.app.api.routes.security import router as security_router
from backend.app.api.routes.reliability import router as reliability_router
from backend.app.api.routes.recovery import router as recovery_router
from backend.app.api.routes.developer import developer_router
from backend.app.api.routes.marketplace import router as marketplace_router
from backend.app.api.routes.collaboration import router as collaboration_router
from backend.app.api.routes.agents import agents_router, teams_router, runs_router
from backend.app.api.routes.simulation import (
    simulations_router,
    scenarios_router,
    suites_router,
    runs_router as simulation_runs_router,
)
from backend.app.api.routes.outcomes import (
    objectives_router,
    outcomes_router,
    targets_router,
    evidence_router,
    measurements_router,
    decisions_router,
    impact_router,
)
from backend.app.api.routes.planning import (
    work_plans_router,
    planning_router,
    planning_scenarios_router,
    resources_router,
    capacity_router,
    reservations_router,
)
from backend.app.api.routes.control_tower import router as control_tower_router
from backend.app.api.routes.public_v1 import public_v1_router
from backend.app.api.routes.knowledge import router as knowledge_router
from backend.app.api.routes.contracts import router as contracts_router
from backend.app.api.routes.catalog import router as catalog_router
from backend.app.api.routes.solutions import router as solutions_router
from backend.app.api.routes.intent import router as intent_router
from backend.app.api.routes.decisions import router as decisions_router
from backend.app.api.endpoints.changes import router as changes_router
from backend.app.api.endpoints.releases import router as releases_router
from backend.app.api.endpoints.rollouts import router as rollouts_router
from backend.app.api.endpoints.release_coordination import router as coordination_router

api_router = APIRouter(prefix="/api")
api_router.include_router(health_router)
api_router.include_router(models_router)
api_router.include_router(auth_router)
api_router.include_router(organizations_router)
api_router.include_router(invitations_router)
api_router.include_router(llm_router)
api_router.include_router(workspaces_router)
api_router.include_router(projects_router)
api_router.include_router(tasks_router)
api_router.include_router(runs_router)
api_router.include_router(context_router)
api_router.include_router(documents_router)
api_router.include_router(artifacts_router)
api_router.include_router(cache_router)
api_router.include_router(governance_router)
api_router.include_router(data_governance_router)
api_router.include_router(security_router)
api_router.include_router(reliability_router)
api_router.include_router(recovery_router)
api_router.include_router(tools_router)
api_router.include_router(evaluation_router)
api_router.include_router(analytics_router)
api_router.include_router(observability_admin_router)
api_router.include_router(workflows_router)
api_router.include_router(connectors_router)
api_router.include_router(memory_router)
api_router.include_router(hitl_router)
api_router.include_router(notifications_router)
api_router.include_router(webhooks_router)
api_router.include_router(preferences_router)
api_router.include_router(deliveries_router)
api_router.include_router(gateway_router)
api_router.include_router(replay_router)
api_router.include_router(evaluation_lab_router)
api_router.include_router(triggers_router)
api_router.include_router(jobs_router)
api_router.include_router(events_router)
api_router.include_router(prompts_router)
api_router.include_router(prompt_experiments_router)
api_router.include_router(knowledge_graph_router)
api_router.include_router(developer_router)
api_router.include_router(marketplace_router)
api_router.include_router(collaboration_router)
api_router.include_router(agents_router)
api_router.include_router(teams_router)
api_router.include_router(runs_router)
api_router.include_router(simulations_router)
api_router.include_router(scenarios_router)
api_router.include_router(suites_router)
api_router.include_router(simulation_runs_router)
api_router.include_router(objectives_router)
api_router.include_router(outcomes_router)
api_router.include_router(targets_router)
api_router.include_router(evidence_router)
api_router.include_router(measurements_router)
api_router.include_router(decisions_router)
api_router.include_router(impact_router)
api_router.include_router(work_plans_router)
api_router.include_router(planning_router)
api_router.include_router(planning_scenarios_router)
api_router.include_router(resources_router)
api_router.include_router(capacity_router)
api_router.include_router(reservations_router)
api_router.include_router(control_tower_router)
api_router.include_router(knowledge_router)
api_router.include_router(contracts_router)
api_router.include_router(catalog_router)
api_router.include_router(solutions_router)
api_router.include_router(intent_router)
api_router.include_router(decisions_router)
api_router.include_router(changes_router, prefix='/changes', tags=['changes'])
api_router.include_router(releases_router, prefix='/releases', tags=['releases'])
api_router.include_router(rollouts_router, prefix='/rollouts', tags=['rollouts'])
api_router.include_router(coordination_router, prefix='/release-coordination', tags=['release_coordination'])
api_router.include_router(public_v1_router)

__all__ = ["api_router"]





