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

__all__ = ["api_router"]




