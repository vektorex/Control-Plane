"""
Central Reliability Service facade coordinating components, checkpoints, resume, and chaos experiments.
"""
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.reliability.checkpoint import CheckpointService
from backend.app.services.reliability.experiments import ChaosExperimentService
from backend.app.services.reliability.health import HealthCheckService
from backend.app.services.reliability.incident import ReliabilityIncidentBridge
from backend.app.services.reliability.models import (
    ChaosExperiment,
    ExecutionCheckpoint,
    ReliabilityComponent,
)
from backend.app.services.reliability.recovery import RecoveryOrchestrator
from backend.app.services.reliability.repository import ReliabilityRepository
from backend.app.services.reliability.resume import ResumeService
from backend.app.services.reliability.schemas import (
    CheckpointResumeRequest,
    CheckpointResumeResponse,
    ExecutionCheckpointCreate,
    ReliabilityObjectiveCreate,
)


class ReliabilityService:
    """Unified service facade for Step 35 Reliability, Resilience & Chaos Engineering."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.health = HealthCheckService(session)
        self.checkpoints = CheckpointService(session)
        self.resume = ResumeService(session)
        self.recovery = RecoveryOrchestrator(session)
        self.experiments = ChaosExperimentService(session)
        self.repository = ReliabilityRepository(session)
        self.incident_bridge = ReliabilityIncidentBridge(session)
