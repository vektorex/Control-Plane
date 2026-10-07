from fastapi import APIRouter
from backend.app.api.endpoints.decisions import router as decisions_endpoints_router

router = APIRouter()

router.include_router(decisions_endpoints_router, prefix="/decisions", tags=["Decision Intelligence"])
