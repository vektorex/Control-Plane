"""
Pydantic schemas and serialization contracts for Step 26: Unified Event Bus.
"""
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ActorSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    type: str = Field(..., description="user, system, worker, connector, scheduler")
    id: Optional[str] = Field(None, description="Identifier of actor if available")


class AggregateSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    type: str = Field(..., description="workflow, job, trigger, document, etc.")
    id: str = Field(..., description="Target aggregate identifier")


class EventContract(BaseModel):
    """
    Standardized, safe event contract broadcast to consumers, APIs, and SSE streams.
    Adheres strictly to Step 26 specification.
    """
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="UUID of the event")
    type: str = Field(..., description="Standardized event type e.g. workflow.completed")
    timestamp: str = Field(..., description="ISO 8601 UTC timestamp")
    workspace_id: str = Field(..., description="Workspace boundary")
    project_id: Optional[str] = Field(None, description="Optional project boundary")
    actor: ActorSchema = Field(..., description="Initiator of the event")
    aggregate: AggregateSchema = Field(..., description="Domain aggregate reference")
    parent_event_id: Optional[str] = Field(None, description="Parent event ID if causally linked")
    correlation_id: Optional[str] = Field(None, description="Distributed correlation trace ID")
    causation_id: Optional[str] = Field(None, description="Immediate triggering event ID")
    sequence_number: Optional[int] = Field(None, description="Monotonic sequence number within aggregate")
    data: Dict[str, Any] = Field(default_factory=dict, description="Sanitized payload")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Sanitized metadata")


class EventPublishRequest(BaseModel):
    """
    Internal request model for publishing an event into the bus.
    """
    event_type: str = Field(..., description="System event type")
    aggregate_type: str = Field(..., description="Aggregate type")
    aggregate_id: str = Field(..., description="Aggregate ID")
    workspace_id: uuid.UUID = Field(..., description="Workspace ID")
    project_id: Optional[uuid.UUID] = Field(None, description="Project ID")
    actor_type: str = Field("system", description="user | system | worker | connector | scheduler")
    actor_id: Optional[str] = Field(None, description="Actor identifier")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Event data payload")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Optional metadata")
    parent_event_id: Optional[uuid.UUID] = Field(None, description="Parent event ID")
    correlation_id: Optional[str] = Field(None, description="Correlation trace ID")
    causation_id: Optional[str] = Field(None, description="Causation ID")
    idempotency_key: Optional[str] = Field(None, description="Idempotency key for deduplication")


class EventFilterParams(BaseModel):
    """
    Validated filter parameters for stream and history endpoints.
    """
    workspace_id: Optional[uuid.UUID] = None
    project_id: Optional[uuid.UUID] = None
    event_type: Optional[str] = Field(None, description="Exact type or category wildcard e.g. job.*")
    aggregate_type: Optional[str] = None
    aggregate_id: Optional[str] = None
    correlation_id: Optional[str] = None
    after: Optional[str] = Field(None, description="Event ID or timestamp cursor for pagination/resume")
    limit: int = Field(50, ge=1, le=100, description="Max records to return")


class EventReplayResponse(BaseModel):
    events: List[EventContract]
    has_more: bool
    next_cursor: Optional[str] = None
    total_count: int = 0
