from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class TraceEventType(str, Enum):
    RUN_STARTED = "run_started"
    PLANNING_STARTED = "planning_started"
    PLANNING_COMPLETED = "planning_completed"
    RETRIEVAL_STARTED = "retrieval_started"
    RETRIEVAL_COMPLETED = "retrieval_completed"
    TOOL_STARTED = "tool_started"
    TOOL_COMPLETED = "tool_completed"
    CONNECTOR_STARTED = "connector_started"
    CONNECTOR_COMPLETED = "connector_completed"
    CONNECTOR_FAILED = "connector_failed"
    GENERATION_STARTED = "generation_started"
    GENERATION_COMPLETED = "generation_completed"
    EVALUATION_STARTED = "evaluation_started"
    EVALUATION_COMPLETED = "evaluation_completed"
    REVISION_STARTED = "revision_started"
    REVISION_COMPLETED = "revision_completed"
    RUN_COMPLETED = "run_completed"
    RUN_FAILED = "run_failed"



class TraceEventStatus(str, Enum):
    STARTED = "started"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
