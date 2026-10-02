"""
Server-Sent Events (SSE) Stream Service for Step 26: Real-Time Execution Updates.
Provides multi-tenant real-time streaming, bounded buffers, backpressure handling,
heartbeats, and Last-Event-ID resumption.
"""
import asyncio
import json
from typing import AsyncGenerator, Dict, List, Optional, Set
from uuid import UUID

from backend.app.config import settings
from backend.app.core.logging import logger
from backend.app.services.events.constants import SSE_HEARTBEAT_EVENT
from backend.app.services.events.filters import EventFilterValidator
from backend.app.services.events.schemas import EventContract


class SSEClientConnection:
    """
    Encapsulates an active browser SSE connection with bounded queuing.
    """

    def __init__(
        self,
        client_id: str,
        workspace_id: UUID,
        project_id: Optional[UUID] = None,
        event_type_pattern: Optional[str] = None,
        aggregate_type: Optional[str] = None,
        aggregate_id: Optional[str] = None,
        buffer_size: int = 100,
    ):
        self.client_id = client_id
        self.workspace_id = workspace_id
        self.project_id = project_id
        self.event_type_pattern = event_type_pattern
        self.aggregate_type = aggregate_type
        self.aggregate_id = aggregate_id
        self.queue: asyncio.Queue[Optional[str]] = asyncio.Queue(maxsize=buffer_size)
        self.is_active = True

    def matches(self, event: EventContract) -> bool:
        """Determines whether this client connection is interested in the event."""
        if str(self.workspace_id) != event.workspace_id:
            return False

        if self.project_id and event.project_id and str(self.project_id) != event.project_id:
            return False

        if self.aggregate_type and self.aggregate_type != event.aggregate.type:
            return False

        if self.aggregate_id and self.aggregate_id != event.aggregate.id:
            return False

        if self.event_type_pattern:
            return EventFilterValidator.matches(event.type, self.event_type_pattern)

        return True

    def enqueue(self, sse_message: str) -> bool:
        """
        Attempts to enqueue a message.
        If buffer is full (slow client), drops or returns False for backpressure handling.
        """
        if not self.is_active:
            return False

        try:
            self.queue.put_nowait(sse_message)
            return True
        except asyncio.QueueFull:
            logger.warning(f"[SSEClientConnection] Client '{self.client_id}' buffer overflowed. Terminating connection.")
            self.is_active = False
            return False


class SSEConnectionManager:
    """
    In-memory registry of active SSE connections for the current process.
    Thread-safe and async-safe.
    """

    def __init__(self):
        # workspace_id -> set of SSEClientConnection
        self._connections: Dict[str, Set[SSEClientConnection]] = {}
        self._lock = asyncio.Lock()

    async def register(self, connection: SSEClientConnection) -> None:
        async with self._lock:
            ws_key = str(connection.workspace_id)
            if ws_key not in self._connections:
                self._connections[ws_key] = set()
            self._connections[ws_key].add(connection)
            logger.info(f"[SSEManager] Registered client '{connection.client_id}' for workspace {ws_key}.")

    async def unregister(self, connection: SSEClientConnection) -> None:
        async with self._lock:
            connection.is_active = False
            ws_key = str(connection.workspace_id)
            if ws_key in self._connections:
                self._connections[ws_key].discard(connection)
                if not self._connections[ws_key]:
                    del self._connections[ws_key]
            logger.info(f"[SSEManager] Unregistered client '{connection.client_id}'.")

    async def broadcast_event(self, event: EventContract) -> None:
        """
        Broadcasts an event to all matching clients in the workspace.
        """
        ws_key = event.workspace_id
        async with self._lock:
            clients = list(self._connections.get(ws_key, set()))

        if not clients:
            return

        message = (
            f"event: {event.type}\n"
            f"id: {event.id}\n"
            f"data: {json.dumps(event.model_dump(), separators=(',', ':'))}\n\n"
        )

        dead_clients = []
        for client in clients:
            if client.matches(event):
                success = client.enqueue(message)
                if not success:
                    dead_clients.append(client)

        if dead_clients:
            for dead in dead_clients:
                await self.unregister(dead)


# Global singleton SSE manager
sse_connection_manager = SSEConnectionManager()


class EventStreamService:
    """
    Exposes authorized event generator streams for FastAPI endpoints.
    """

    @classmethod
    async def create_event_stream(
        cls,
        workspace_id: UUID,
        project_id: Optional[UUID] = None,
        event_type_pattern: Optional[str] = None,
        aggregate_type: Optional[str] = None,
        aggregate_id: Optional[str] = None,
        last_event_id: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Yields SSE formatted strings:
        1. Historical replay from last_event_id (bounded up to 50 events)
        2. Real-time events as they arrive
        3. Periodic heartbeats
        """
        import uuid
        client_id = f"client_{uuid.uuid4().hex[:12]}"
        connection = SSEClientConnection(
            client_id=client_id,
            workspace_id=workspace_id,
            project_id=project_id,
            event_type_pattern=event_type_pattern,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            buffer_size=getattr(settings, "SSE_CLIENT_BUFFER_SIZE", 100),
        )

        await sse_connection_manager.register(connection)

        # 1. Bounded replay if Last-Event-ID or after cursor provided
        after_uuid = None
        if last_event_id:
            try:
                after_uuid = UUID(last_event_id.strip())
            except ValueError:
                after_uuid = None

        if after_uuid:
            try:
                from backend.app.db.database import get_session
                from backend.app.services.events.repository import EventRepository
                from backend.app.services.events.sanitizer import EventSanitizer

                async for session in get_session():
                    repo = EventRepository(session)
                    replayed_events = await repo.replay_events(
                        workspace_id=workspace_id,
                        after_id=after_uuid,
                        event_type_pattern=event_type_pattern,
                        limit=50,
                    )
                    for rev in replayed_events:
                        contract = EventSanitizer.to_contract(rev)
                        msg = (
                            f"event: {contract.type}\n"
                            f"id: {contract.id}\n"
                            f"data: {json.dumps(contract.model_dump(), separators=(',', ':'))}\n\n"
                        )
                        yield msg
                    break
            except Exception as e:
                logger.warning(f"[EventStreamService] Error during Last-Event-ID replay: {e}")

        # 2. Continuous real-time streaming with heartbeats
        heartbeat_interval = getattr(settings, "SSE_HEARTBEAT_INTERVAL_SECONDS", 15.0)

        try:
            while connection.is_active:
                try:
                    # Wait for next event or heartbeat timeout
                    item = await asyncio.wait_for(connection.queue.get(), timeout=heartbeat_interval)
                    if item:
                        yield item
                except asyncio.TimeoutError:
                    # Send periodic keepalive heartbeat comment / event
                    yield f"event: {SSE_HEARTBEAT_EVENT}\ndata: {{}}\n\n"
        except (asyncio.CancelledError, GeneratorExit):
            logger.info(f"[EventStreamService] Client {client_id} disconnected.")
        finally:
            await sse_connection_manager.unregister(connection)
