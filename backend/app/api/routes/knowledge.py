from fastapi import APIRouter
from backend.app.api.endpoints.knowledge import router as knowledge_router
from backend.app.api.endpoints.knowledge_candidates import router as candidates_router
from backend.app.api.endpoints.knowledge_conflicts import router as conflicts_router

router = APIRouter()

router.include_router(knowledge_router, prefix="/knowledge", tags=["Organizational Knowledge"])
router.include_router(candidates_router, prefix="/knowledge-candidates", tags=["Knowledge Candidates"])
router.include_router(conflicts_router, prefix="/knowledge-conflicts", tags=["Knowledge Conflicts"])
