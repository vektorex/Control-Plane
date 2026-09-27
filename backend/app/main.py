from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError

from backend.app.config import settings
from backend.app.core.errors import (
    AppError,
    app_error_handler,
    validation_error_handler,
    generic_exception_handler,
)
from backend.app.core.logging import logger, setup_logging
from backend.app.api.routes import api_router
from backend.app.services.llm.factory import llm_factory
from backend.app.db.database import init_db, close_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    setup_logging()
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT} | Debug: {settings.DEBUG}")
    
    # Check LLM providers
    configured_providers = llm_factory.get_configured_provider_ids()
    logger.info(f"Configured LLM providers: {configured_providers or 'None (unit test / local mode)'}")

    # Initialize Database tables if configured
    try:
        await init_db()
        logger.info("[Startup] Database connection verified and initialized.")
    except Exception as e:
        logger.warning(f"[Startup] Database initialization deferred: {str(e)}")

    yield

    # Shutdown
    logger.info(f"Shutting down {settings.APP_NAME}")
    try:
        await close_db()
    except Exception as e:
        logger.warning(f"[Shutdown] Error closing database pool: {str(e)}")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Provider-Agnostic LLM Work Orchestration Layer API & PostgreSQL Data Layer",
    lifespan=lifespan,
)

# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Structured Exception Handlers
app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Mount Routes
app.include_router(api_router)
app.include_router(api_router, prefix="/v1")


@app.get("/", tags=["Root"])
async def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "online",
        "docs": "/docs",
        "health": "/api/health",
        "models": "/api/models",
        "workspaces": "/api/workspaces",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
