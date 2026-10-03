import asyncio
import time
import pytest
import pytest_asyncio
from typing import AsyncIterator, List
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from backend.app.main import app
from backend.app.db.base import Base
from backend.app.db.database import get_db
import backend.app.db.models  # Register all models
from backend.app.core.auth import create_access_token, DEV_JWT_SECRET
from backend.app.schemas.llm import (
    LLMGenerateRequest,
    LLMGenerateResponse,
    LLMStreamChunk,
    TokenUsage,
)
from backend.app.schemas.models import ModelInfo
from backend.app.services.llm.base import BaseLLMProvider
from backend.app.services.llm.factory import LLMProviderFactory, get_llm_factory


class MockTestProvider(BaseLLMProvider):
    """
    Mock LLM Provider for deterministic unit testing at the service boundary.
    """

    def __init__(self, configured: bool = True, should_fail: bool = False, fail_type: str = "general"):
        self._configured = configured
        self._should_fail = should_fail
        self._fail_type = fail_type

    @property
    def provider_id(self) -> str:
        return "mock_provider"

    @property
    def provider_name(self) -> str:
        return "Mock Test Provider"

    @property
    def is_configured(self) -> bool:
        return self._configured

    def get_models(self) -> List[ModelInfo]:
        return [
            ModelInfo(
                id="mock-model-v1",
                name="Mock Model v1",
                provider=self.provider_id,
                description="Mock testing model",
                context_window=32000,
                supports_streaming=True,
                is_default=True,
            )
        ]

    def supports_model(self, model_id: str) -> bool:
        return model_id in ["mock-model-v1", "mock-custom"]

    async def generate(self, request: LLMGenerateRequest) -> LLMGenerateResponse:
        if not self._configured:
            from backend.app.core.errors import ProviderNotConfiguredError
            raise ProviderNotConfiguredError("Mock provider is not configured.")

        if self._should_fail:
            from backend.app.core.errors import (
                ProviderAuthenticationError,
                ProviderRateLimitError,
                ProviderAPIError,
            )
            if self._fail_type == "auth":
                raise ProviderAuthenticationError("Mock authentication failure.")
            elif self._fail_type == "rate_limit":
                raise ProviderRateLimitError("Mock rate limit exceeded.")
            else:
                raise ProviderAPIError("Mock upstream API failure.")

        return LLMGenerateResponse(
            content=f"Mock response for: {request.messages[-1].content}",
            model=request.model,
            provider=self.provider_id,
            usage=TokenUsage(input_tokens=15, output_tokens=25, total_tokens=40),
            finish_reason="stop",
        )

    async def generate_stream(
        self, request: LLMGenerateRequest
    ) -> AsyncIterator[LLMStreamChunk]:
        if not self._configured:
            from backend.app.core.errors import ProviderNotConfiguredError
            raise ProviderNotConfiguredError("Mock provider is not configured.")

        if self._should_fail:
            from backend.app.core.errors import ProviderAPIError
            raise ProviderAPIError("Mock streaming failure.")

        tokens = ["Mock", " ", "streamed", " ", "response", "!"]
        for idx, token in enumerate(tokens):
            is_last = idx == len(tokens) - 1
            yield LLMStreamChunk(
                content=token,
                model=request.model,
                provider=self.provider_id,
                is_finished=is_last,
                usage=TokenUsage(input_tokens=12, output_tokens=6, total_tokens=18) if is_last else None,
                finish_reason="stop" if is_last else None,
            )


# Async in-memory test database engine for fast, isolated tests
test_engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
test_async_session_factory = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    async def _init_tables():
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    asyncio.run(_init_tables())
    yield

    async def _drop_tables():
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await test_engine.dispose()

    asyncio.run(_drop_tables())


async def override_get_db():
    async with test_async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@pytest_asyncio.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    """Yields an isolated async session for database model testing."""
    async with test_async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@pytest.fixture
def mock_factory():
    factory = LLMProviderFactory()
    mock_provider = MockTestProvider(configured=True)
    factory.register_provider(mock_provider)
    return factory


@pytest.fixture
def user1_auth():
    auth_user_id = "user-auth-001-uuid"
    email = "user1@example.com"
    token = create_access_token(auth_user_id=auth_user_id, email=email)
    headers = {"Authorization": f"Bearer {token}"}
    return {
        "auth_user_id": auth_user_id,
        "email": email,
        "token": token,
        "headers": headers,
    }


@pytest.fixture
def user2_auth():
    auth_user_id = "user-auth-002-uuid"
    email = "user2@example.com"
    token = create_access_token(auth_user_id=auth_user_id, email=email)
    headers = {"Authorization": f"Bearer {token}"}
    return {
        "auth_user_id": auth_user_id,
        "email": email,
        "token": token,
        "headers": headers,
    }


@pytest.fixture
def client(mock_factory, monkeypatch):
    import backend.app.db.database as db_mod
    import backend.app.api.routes.documents as doc_mod

    monkeypatch.setattr(db_mod, "AsyncSessionLocal", test_async_session_factory)
    monkeypatch.setattr(db_mod, "async_session_factory", test_async_session_factory)
    monkeypatch.setattr(doc_mod, "AsyncSessionLocal", test_async_session_factory)


    app.dependency_overrides[get_llm_factory] = lambda: mock_factory
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def auth_client(client, user1_auth):
    """Test client pre-configured with User 1 authorization header."""
    class AuthenticatedClient:
        def __init__(self, c, headers):
            self._c = c
            self.headers = headers

        def get(self, url, **kwargs):
            h = {**self.headers, **kwargs.pop("headers", {})}
            return self._c.get(url, headers=h, **kwargs)

        def post(self, url, **kwargs):
            h = {**self.headers, **kwargs.pop("headers", {})}
            return self._c.post(url, headers=h, **kwargs)

        def patch(self, url, **kwargs):
            h = {**self.headers, **kwargs.pop("headers", {})}
            return self._c.patch(url, headers=h, **kwargs)

        def delete(self, url, **kwargs):
            h = {**self.headers, **kwargs.pop("headers", {})}
            return self._c.delete(url, headers=h, **kwargs)

    return AuthenticatedClient(client, user1_auth["headers"])
