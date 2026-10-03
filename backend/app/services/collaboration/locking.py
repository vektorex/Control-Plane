"""
Advisory Short-Lived Locking Service for Step 39: Collaboration.
Enforces auto-expiring advisory locks to prevent race conditions during sensitive concurrent operations.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from backend.app.services.collaboration.exceptions import LockConflictError
from backend.app.services.collaboration.models import CollaborationLock


class CollaborationLockManager:
    """Manages ephemeral advisory locks with automatic TTL expiration."""

    def __init__(self, session: AsyncSession):
        self.db = session

    async def acquire_lock(
        self,
        resource_type: str,
        resource_id: str,
        owner_id: str,
        ttl_seconds: int = 60,
    ) -> CollaborationLock:
        """
        Attempts to acquire an advisory lock for a resource.
        Replaces expired locks. Raises LockConflictError if actively locked by another user.
        """
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=max(5, min(ttl_seconds, 300)))  # Cap TTL between 5s and 5m

        # Check existing lock
        query = select(CollaborationLock).where(
            CollaborationLock.resource_type == resource_type,
            CollaborationLock.resource_id == resource_id,
        )
        result = await self.db.execute(query)
        existing = result.scalar_one_or_none()

        if existing:
            # If not expired and owned by another user
            if existing.expires_at > now and existing.owner_id != owner_id:
                raise LockConflictError(resource_id=resource_id, owner_id=existing.owner_id)

            # Update existing lock
            existing.owner_id = owner_id
            existing.acquired_at = now
            existing.expires_at = expires_at
            await self.db.flush()
            return existing

        # Create new lock
        lock = CollaborationLock(
            resource_type=resource_type,
            resource_id=resource_id,
            owner_id=owner_id,
            acquired_at=now,
            expires_at=expires_at,
        )
        self.db.add(lock)
        await self.db.flush()
        return lock

    async def release_lock(
        self,
        resource_type: str,
        resource_id: str,
        owner_id: str,
    ) -> bool:
        """Releases lock if held by owner or expired."""
        query = select(CollaborationLock).where(
            CollaborationLock.resource_type == resource_type,
            CollaborationLock.resource_id == resource_id,
        )
        result = await self.db.execute(query)
        lock = result.scalar_one_or_none()

        if lock and (lock.owner_id == owner_id or lock.expires_at <= datetime.now(timezone.utc)):
            await self.db.delete(lock)
            await self.db.flush()
            return True
        return False

    async def verify_not_locked(
        self,
        resource_type: str,
        resource_id: str,
        user_id: str,
    ) -> None:
        """Verifies that the resource is not locked by another user."""
        now = datetime.now(timezone.utc)
        query = select(CollaborationLock).where(
            CollaborationLock.resource_type == resource_type,
            CollaborationLock.resource_id == resource_id,
            CollaborationLock.expires_at > now,
        )
        result = await self.db.execute(query)
        active_lock = result.scalar_one_or_none()

        if active_lock and active_lock.owner_id != user_id:
            raise LockConflictError(resource_id=resource_id, owner_id=active_lock.owner_id)
