from typing import Optional, Tuple
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from backend.app.core.errors import ConflictError, NotFoundError, DatabaseError
from backend.app.db.models.user import User


class UserRepository:
    """Repository handling persistence and lookup for User profiles."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        stmt = select(User).where(User.id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id_or_raise(self, user_id: UUID) -> User:
        user = await self.get_by_id(user_id)
        if not user:
            raise NotFoundError(f"User with id '{user_id}' not found.")
        return user

    async def get_by_auth_user_id(self, auth_user_id: str) -> Optional[User]:
        stmt = select(User).where(User.auth_user_id == auth_user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        stmt = select(User).where(User.email == email.strip().lower())
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, auth_user_id: str, email: str) -> User:
        user = User(
            auth_user_id=auth_user_id,
            email=email.strip().lower(),
        )
        self.session.add(user)
        try:
            await self.session.flush()
            await self.session.refresh(user)
            return user
        except IntegrityError as e:
            await self.session.rollback()
            raise ConflictError("User with this identity or email already exists.", details=str(e))
        except Exception as e:
            await self.session.rollback()
            raise DatabaseError("Failed to create user profile.", details=str(e))

    async def get_or_create(self, auth_user_id: str, email: str) -> Tuple[User, bool]:
        """
        Idempotently fetch or create user profile based on Supabase auth_user_id.
        Returns (user, is_created).
        """
        existing = await self.get_by_auth_user_id(auth_user_id)
        if existing:
            # Update email if changed in identity provider
            clean_email = email.strip().lower()
            if existing.email != clean_email:
                existing.email = clean_email
                await self.session.flush()
                await self.session.refresh(existing)
            return existing, False

        user = User(
            auth_user_id=auth_user_id,
            email=email.strip().lower(),
        )
        self.session.add(user)
        try:
            await self.session.flush()
            await self.session.refresh(user)
            return user, True
        except IntegrityError:
            # Race condition handling: re-fetch
            await self.session.rollback()
            existing = await self.get_by_auth_user_id(auth_user_id)
            if existing:
                return existing, False
            raise ConflictError("Concurrent user creation conflict.")
