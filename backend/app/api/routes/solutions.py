from fastapi import APIRouter
from backend.app.api.endpoints.solutions import router as solutions_endpoints_router

router = APIRouter()

router.include_router(solutions_endpoints_router, prefix="/solutions", tags=["Solutions"])
