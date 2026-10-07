from fastapi import APIRouter
from backend.app.api.endpoints.catalog import router as catalog_endpoints_router

router = APIRouter()

router.include_router(catalog_endpoints_router, prefix="/catalog", tags=["Service Catalog"])
