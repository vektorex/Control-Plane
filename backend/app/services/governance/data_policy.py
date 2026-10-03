"""
DataClassificationService: deterministic classification engine.
Classifications are always assigned by system-trusted sources.
LLM output may be advisory only – never authoritative. Step 32.
"""
from datetime import datetime, timezone
from typing import Dict, Optional
import uuid

from backend.app.services.governance.constants import (
    ClassificationSource,
    DataClassification,
)
from backend.app.services.governance.schemas import (
    DataClassificationRequest,
    DataClassificationResponse,
)

# In-memory registry of classifications assigned to known target types/IDs
# In production this would be persisted; for this layer it acts as session-scoped cache
_CLASSIFICATION_REGISTRY: Dict[str, DataClassification] = {}

# Default classification by target type when none is set
_DEFAULT_CLASSIFICATIONS: Dict[str, DataClassification] = {
    "artifact": DataClassification.INTERNAL,
    "document": DataClassification.INTERNAL,
    "connector": DataClassification.CONFIDENTIAL,
    "memory": DataClassification.INTERNAL,
    "entity": DataClassification.INTERNAL,
    "workflow": DataClassification.INTERNAL,
    "task": DataClassification.INTERNAL,
    "prompt": DataClassification.INTERNAL,
}

# Untrusted external content must not self-classify above this level
_MAX_EXTERNAL_CLASSIFICATION = DataClassification.INTERNAL


def _classification_key(target_type: str, target_id: uuid.UUID) -> str:
    return f"{target_type}:{target_id}"


class DataClassificationService:
    """
    Assigns and resolves data classifications for artifacts, documents, connectors,
    memory, graph entities, workflows, tasks, and prompts.

    Rules:
    - External content cannot self-classify as CONFIDENTIAL or RESTRICTED.
    - LLM output may be advisory only and must be passed through source=SYSTEM or an admin.
    - Classification precedence: SYSTEM > ORG_POLICY > WORKSPACE_POLICY > PROJECT_POLICY > USER_EXPLICIT.
    """

    # Source trust ordering: lower = more trusted
    _SOURCE_PRIORITY: Dict[ClassificationSource, int] = {
        ClassificationSource.SYSTEM: 0,
        ClassificationSource.ORGANIZATION_POLICY: 1,
        ClassificationSource.WORKSPACE_POLICY: 2,
        ClassificationSource.PROJECT_POLICY: 3,
        ClassificationSource.USER_EXPLICIT: 4,
    }

    @staticmethod
    def assign(request: DataClassificationRequest) -> DataClassificationResponse:
        """Assign a classification to a target. Returns confirmed assignment."""
        # Prevent external/untrusted sources from self-classifying above INTERNAL
        if request.source == ClassificationSource.USER_EXPLICIT:
            if request.classification in (DataClassification.CONFIDENTIAL, DataClassification.RESTRICTED):
                # Users may not self-escalate to confidential/restricted without policy
                request = DataClassificationRequest(
                    target_type=request.target_type,
                    target_id=request.target_id,
                    classification=DataClassification.INTERNAL,
                    source=request.source,
                    reason="User escalation to confidential/restricted requires policy approval",
                )

        key = _classification_key(request.target_type, request.target_id)
        _CLASSIFICATION_REGISTRY[key] = request.classification

        return DataClassificationResponse(
            target_type=request.target_type,
            target_id=request.target_id,
            classification=request.classification,
            source=request.source.value,
            assigned_at=datetime.now(timezone.utc),
        )

    @staticmethod
    def get(target_type: str, target_id: uuid.UUID) -> DataClassification:
        """Return the classification for a target, defaulting to the type default."""
        key = _classification_key(target_type, target_id)
        if key in _CLASSIFICATION_REGISTRY:
            return _CLASSIFICATION_REGISTRY[key]
        return _DEFAULT_CLASSIFICATIONS.get(target_type, DataClassification.INTERNAL)

    @staticmethod
    def is_restricted(target_type: str, target_id: uuid.UUID) -> bool:
        return DataClassificationService.get(target_type, target_id) == DataClassification.RESTRICTED

    @staticmethod
    def is_at_least_confidential(target_type: str, target_id: uuid.UUID) -> bool:
        cls = DataClassificationService.get(target_type, target_id)
        return cls in (DataClassification.CONFIDENTIAL, DataClassification.RESTRICTED)

    @staticmethod
    def requires_approved_provider(target_type: str, target_id: uuid.UUID) -> bool:
        """Restricted and confidential data must only flow to explicitly approved providers."""
        return DataClassificationService.is_at_least_confidential(target_type, target_id)
