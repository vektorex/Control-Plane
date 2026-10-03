"""
Central facade service for Step 36: Disaster Recovery, Backup & Business Continuity Layer.
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.disaster_recovery.repository import DisasterRecoveryRepository
from backend.app.services.disaster_recovery.backup import BackupService
from backend.app.services.disaster_recovery.backup_planner import BackupPlanner
from backend.app.services.disaster_recovery.verification import BackupVerificationService
from backend.app.services.disaster_recovery.restore import RestoreService
from backend.app.services.disaster_recovery.restore_planner import RestorePlanner
from backend.app.services.disaster_recovery.integrity import BackupIntegrityService
from backend.app.services.disaster_recovery.recovery_objectives import RecoveryObjectivesService
from backend.app.services.disaster_recovery.continuity import ContinuityService
from backend.app.services.disaster_recovery.exercises import RecoveryExerciseService
from backend.app.services.disaster_recovery.retention import BackupRetentionService
from backend.app.services.disaster_recovery.evidence import RecoveryEvidenceBridge
from backend.app.services.disaster_recovery.storage import (
    BackupStorageProvider,
    BackupEncryptionProvider,
    get_backup_storage_provider,
)


class DisasterRecoveryService:
    """
    Unified entry point for application-level backup snapshotting, cryptographic verification,
    restore evaluation, business continuity planning, and recovery exercises.
    """

    def __init__(
        self,
        session: AsyncSession,
        storage_provider: Optional[BackupStorageProvider] = None,
        encryption_provider: Optional[BackupEncryptionProvider] = None,
    ):
        self.session = session
        self.storage = storage_provider or get_backup_storage_provider()
        self.encryption = encryption_provider or BackupEncryptionProvider()

        # Engine sub-services
        self.repository = DisasterRecoveryRepository(session)
        self.planner = BackupPlanner(session)
        self.backup = BackupService(session, self.storage, self.encryption)
        self.integrity = BackupIntegrityService(self.storage)
        self.verification = BackupVerificationService(session, self.storage, self.encryption)
        self.restore_planner = RestorePlanner(session)
        self.restore = RestoreService(session, self.storage, self.encryption)
        self.objectives = RecoveryObjectivesService(session)
        self.continuity = ContinuityService(session)
        self.exercises = RecoveryExerciseService(session)
        self.retention = BackupRetentionService(session)
        self.evidence = RecoveryEvidenceBridge(session)
