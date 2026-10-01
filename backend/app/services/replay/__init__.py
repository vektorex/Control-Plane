"""
AI Execution Replay & Debugging Studio Services (Step 21).

Provides safe, deterministic execution snapshotting, sanitized capture,
policy enforcement (dry-run by default, fresh HITL authorization gating),
cooperative execution replay, factual diff comparison, and error analysis.
"""

from backend.app.services.replay.service import ReplayService
from backend.app.services.replay.runner import ReplayRunner
from backend.app.services.replay.snapshot import ReplaySnapshotService
from backend.app.services.replay.comparator import ReplayComparator
from backend.app.services.replay.policies import ReplayPolicy, ReplayEligibilityChecker
from backend.app.services.replay.error_analysis import ErrorAnalysisService
from backend.app.services.replay.sanitizer import sanitize_replay_snapshot
from backend.app.services.replay.schemas import (
    ReplayMode,
    ReplayStatus,
    RetrievalReplayMode,
    ExecutionSnapshot,
    ReplayEligibility,
    ReplayRunCreateRequest,
    ReplayStepRequest,
    FailureInsights,
    ReplayComparisonResult,
    ReplayRunResponse,
    ReplayListResponse,
)
from backend.app.services.replay.errors import (
    ReplayError,
    ReplayNotFoundError,
    ReplayEligibilityError,
    ReplayPermissionDeniedError,
    SnapshotSanitizationError,
    SideEffectBlockedError,
    ReplayConflictError,
)

__all__ = [
    "ReplayService",
    "ReplayRunner",
    "ReplaySnapshotService",
    "ReplayComparator",
    "ReplayPolicy",
    "ReplayEligibilityChecker",
    "ErrorAnalysisService",
    "sanitize_replay_snapshot",
    "ReplayMode",
    "ReplayStatus",
    "RetrievalReplayMode",
    "ExecutionSnapshot",
    "ReplayEligibility",
    "ReplayRunCreateRequest",
    "ReplayStepRequest",
    "FailureInsights",
    "ReplayComparisonResult",
    "ReplayRunResponse",
    "ReplayListResponse",
    "ReplayError",
    "ReplayNotFoundError",
    "ReplayEligibilityError",
    "ReplayPermissionDeniedError",
    "SnapshotSanitizationError",
    "SideEffectBlockedError",
    "ReplayConflictError",
]
