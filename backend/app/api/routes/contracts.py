from fastapi import APIRouter
from backend.app.api.endpoints.contracts import router as contracts_endpoints_router

router = APIRouter()

router.include_router(contracts_endpoints_router, prefix="/contracts", tags=["Contracts"])
