from fastapi import APIRouter
from backend.app.api.endpoints.intent import router as intent_endpoints_router

router = APIRouter()

router.include_router(intent_endpoints_router, prefix="/intent", tags=["Intent Synthesis"])
