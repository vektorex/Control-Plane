import pytest
from datetime import datetime, timezone
from uuid import uuid4

from backend.app.db.models.context import TaskContext
from backend.app.db.models.task import Task
from backend.app.services.context.base import ContextProvider
from backend.app.services.context.builders.context_builder import ContextBuilder
from backend.app.services.context.engine import ContextEngine
from backend.app.services.context.models import (
    ContextBudget,
    ContextItem,
    ContextPackage,
    ContextSourceType,
)
from backend.app.services.context.providers.manual_context import ManualContextProvider
from backend.app.services.context.providers.task_context import TaskContextProvider
from backend.app.services.context.registry import ContextProviderRegistry
from backend.app.services.context.token_estimator import (
    estimate_context_item_tokens,
    estimate_tokens,
)


def test_token_estimator():
    """Validates token estimation logic for text and ContextItems."""
    assert estimate_tokens("") == 0
    assert estimate_tokens(None) == 0
    assert estimate_tokens("   ") == 0

    short_text = "Hello world"
    tokens = estimate_tokens(short_text)
    assert tokens >= 2

    long_text = "This is a longer paragraph intended to verify the proportional scaling of the local token estimation heuristic."
    assert estimate_tokens(long_text) > tokens

    item = ContextItem(
        title="Sample Item",
        content="Sample content inside the item.",
        priority=10,
    )
    item_tokens = estimate_context_item_tokens(item)
    assert item_tokens > estimate_tokens(item.content)


@pytest.mark.asyncio
async def test_provider_registry():
    """Tests provider registration, retrieval, and deregistration."""
    registry = ContextProviderRegistry()
    assert len(registry.get_providers()) == 0

    task_provider = TaskContextProvider()
    registry.register(task_provider)
    assert len(registry.get_providers()) == 1
    assert registry.get_provider("task_context") == task_provider

    unregistered = registry.unregister("task_context")
    assert unregistered == task_provider
    assert len(registry.get_providers()) == 0


@pytest.mark.asyncio
async def test_task_context_provider():
    """Tests task context extraction from Task entity."""
    provider = TaskContextProvider()
    task = Task(
        id=uuid4(),
        project_id=uuid4(),
        title="Implement Auth",
        description="Detailed auth description",
        instructions="Write unit tests for JWT",
        context_text="FastAPI backend using PyJWT and bcrypt",
    )

    can_handle = await provider.can_handle(task)
    assert can_handle is True

    items = await provider.provide(task)
    assert len(items) >= 1

    bg_item = next((i for i in items if "FastAPI backend" in i.content), None)
    assert bg_item is not None
    assert bg_item.source_type == ContextSourceType.TASK.value
    assert bg_item.priority == 80
    assert bg_item.token_estimate > 0


@pytest.mark.asyncio
async def test_manual_context_provider_with_relationship():
    """Tests ManualContextProvider when contexts are pre-loaded in relationship."""
    provider = ManualContextProvider()
    task_id = uuid4()
    manual_ctx = TaskContext(
        id=uuid4(),
        task_id=task_id,
        source_type="manual",
        title="Custom Note",
        content="Important security rule: always hash passwords",
        priority=50,
        created_at=datetime.now(timezone.utc),
    )
    task = Task(
        id=task_id,
        project_id=uuid4(),
        title="Security Task",
    )
    task.contexts = [manual_ctx]

    items = await provider.provide(task)
    assert len(items) == 1
    assert items[0].title == "Custom Note"
    assert items[0].content == "Important security rule: always hash passwords"
    assert items[0].priority == 50
    assert items[0].source_type == "manual"


def test_context_builder_deduplication():
    """Tests deduplication of identical items, preserving highest priority."""
    builder = ContextBuilder()
    item1 = ContextItem(
        title="Duplicate Title",
        content="Identical content payload",
        priority=10,
    )
    item2 = ContextItem(
        title="Duplicate Title",
        content="Identical content payload",
        priority=90,
    )
    item3 = ContextItem(
        title="Unique Title",
        content="Different content payload",
        priority=30,
    )

    deduped = builder.deduplicate([item1, item2, item3])
    assert len(deduped) == 2
    # The duplicate that was kept should have the higher priority (90)
    kept_dup = next(i for i in deduped if i.title == "Duplicate Title")
    assert kept_dup.priority == 90


def test_context_builder_prioritization():
    """Tests priority sorting: higher priority -> relevance -> recency."""
    builder = ContextBuilder()
    item_low = ContextItem(title="Low", content="Low priority", priority=10)
    item_high = ContextItem(title="High", content="High priority", priority=90)
    item_system = ContextItem(title="System", content="System critical", priority=100)

    prioritized = builder.prioritize([item_low, item_system, item_high])
    assert prioritized[0].title == "System"
    assert prioritized[1].title == "High"
    assert prioritized[2].title == "Low"


def test_context_builder_budget_enforcement():
    """Tests context budget truncation when total tokens exceed max_context_tokens."""
    builder = ContextBuilder()
    # Create large items
    item1 = ContextItem(
        title="Item 1 (High Priority)",
        content="Word " * 100,  # ~130 tokens
        priority=90,
    )
    item2 = ContextItem(
        title="Item 2 (Medium Priority)",
        content="Word " * 100,  # ~130 tokens
        priority=50,
    )
    item3 = ContextItem(
        title="Item 3 (Low Priority)",
        content="Word " * 100,  # ~130 tokens
        priority=10,
    )

    # Set tight budget allowing only 1-2 items (~200 tokens)
    budget = ContextBudget(max_context_tokens=180)
    package = builder.build([item1, item2, item3], budget=budget)

    assert package.total_items == 1
    assert package.items[0].title == "Item 1 (High Priority)"
    assert package.truncated is True
    assert package.dropped_items_count == 2
    assert package.estimated_tokens <= 180


def test_context_builder_empty_context():
    """Tests builder handling of empty context items list."""
    builder = ContextBuilder()
    package = builder.build([], budget=ContextBudget(max_context_tokens=8000))
    assert package.total_items == 0
    assert package.estimated_tokens == 0
    assert package.truncated is False
    assert package.sources == []


def test_context_builder_format_messages():
    """Tests formatting ContextPackage into LLM chat messages."""
    builder = ContextBuilder()
    task = Task(
        id=uuid4(),
        project_id=uuid4(),
        title="Analyze Repo",
        instructions="Check repository structure",
    )
    item = ContextItem(
        source_type="manual",
        title="Architecture Guide",
        content="Backend uses FastAPI with SQLite",
        priority=50,
    )
    package = builder.build([item], budget=ContextBudget(max_context_tokens=8000))

    messages = builder.format_as_messages(package, task)
    assert len(messages) == 2
    assert messages[0].role == "system"
    assert "Architecture Guide" in messages[0].content
    assert "FastAPI with SQLite" in messages[0].content
    assert messages[1].role == "user"
    assert messages[1].content == "Check repository structure"


@pytest.mark.asyncio
async def test_context_engine_build_context():
    """Tests full ContextEngine orchestration."""
    engine = ContextEngine()
    task = Task(
        id=uuid4(),
        project_id=uuid4(),
        title="Deploy App",
        instructions="Create deployment manifest",
        context_text="Targeting Kubernetes cluster 1.28",
    )

    package = await engine.build_context(task, max_context_tokens=8000)
    assert package.total_items >= 1
    assert "task" in package.sources
    assert package.estimated_tokens > 0
    assert package.truncated is False


@pytest.mark.asyncio
async def test_extensibility_custom_provider():
    """Verifies that a future custom provider (e.g. VectorProvider) plugs in seamlessly."""
    class CustomVectorProvider(ContextProvider):
        @property
        def provider_id(self) -> str:
            return "vector_retrieval"

        @property
        def source_type(self) -> str:
            return "vector"

        async def can_handle(self, task: Task, **kwargs) -> bool:
            return True

        async def collect(self, task: Task, session=None, **kwargs):
            return [{"id": "vec-1", "title": "Vector Match #1", "content": "Relevant embedding chunk", "relevance": 0.95}]

        def normalize(self, raw_items, **kwargs):
            return [
                ContextItem(
                    id=r["id"],
                    source_type=self.source_type,
                    title=r["title"],
                    content=r["content"],
                    relevance_score=r["relevance"],
                    priority=60,
                )
                for r in raw_items
            ]

    engine = ContextEngine()
    engine.register_provider(CustomVectorProvider())

    task = Task(id=uuid4(), project_id=uuid4(), title="Vector Test")
    package = await engine.build_context(task)

    assert "vector" in package.sources
    vector_item = next((i for i in package.items if i.source_type == "vector"), None)
    assert vector_item is not None
    assert vector_item.title == "Vector Match #1"
