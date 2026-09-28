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
from backend.app.api.routes.workspaces import router as workspaces_router

api_router = APIRouter(prefix="/api")
api_router.include_router(health_router)
api_router.include_router(models_router)
api_router.include_router(auth_router)
api_router.include_router(llm_router)
api_router.include_router(workspaces_router)
api_router.include_router(projects_router)
api_router.include_router(tasks_router)
api_router.include_router(runs_router)
api_router.include_router(context_router)
api_router.include_router(documents_router)

__all__ = ["api_router"]
