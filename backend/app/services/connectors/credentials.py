"""
Credential Vault and Secret Encryption abstraction for connectors.
"""
import base64
import hashlib
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from backend.app.config import settings
from backend.app.core.logging import logger
from backend.app.db.models.connector import Credential


class SecretEncryptor:
    """
    Authenticated symmetric encryption (AES-256-GCM) for storing sensitive connector credentials.
    Ensures confidentiality and integrity (tamper-resistance).
    """

    def __init__(self, key_material: Optional[str] = None) -> None:
        raw_key = key_material or settings.CONNECTOR_ENCRYPTION_KEY
        if not raw_key:
            # Deterministic development fallback key for local dev and testing
            raw_key = "ai-work-layer-dev-connector-encryption-key-32b-secret"
        
        # Derive exactly 32 bytes (256 bits) using SHA-256
        self._key = hashlib.sha256(raw_key.encode("utf-8")).digest()
        self._aesgcm = AESGCM(self._key)

    def encrypt(self, plaintext: str) -> str:
        """
        Encrypts plaintext string using AES-256-GCM with a fresh 12-byte random nonce.
        Returns a base64-encoded string containing nonce + ciphertext + tag.
        """
        if not plaintext:
            return ""
        nonce = os.urandom(12)  # 96-bit nonce standard for GCM
        ciphertext = self._aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
        combined = nonce + ciphertext
        return base64.b64encode(combined).decode("utf-8")

    def decrypt(self, encoded_ciphertext: str) -> str:
        """
        Decrypts base64-encoded ciphertext payload.
        Verifies authentication tag and extracts plaintext.
        """
        if not encoded_ciphertext:
            return ""
        try:
            combined = base64.b64decode(encoded_ciphertext.encode("utf-8"))
            if len(combined) < 13:
                raise ValueError("Ciphertext too short")
            nonce = combined[:12]
            ciphertext = combined[12:]
            decrypted_bytes = self._aesgcm.decrypt(nonce, ciphertext, None)
            return decrypted_bytes.decode("utf-8")
        except Exception as e:
            logger.error(f"[SecretEncryptor] Decryption failed: {type(e).__name__}")
            raise ValueError("Failed to decrypt secret. Possible key mismatch or data corruption.")


# Singleton encryptor instance
_default_encryptor: Optional[SecretEncryptor] = None


def get_secret_encryptor() -> SecretEncryptor:
    global _default_encryptor
    if _default_encryptor is None:
        _default_encryptor = SecretEncryptor()
    return _default_encryptor


class DecryptedCredential(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: uuid.UUID
    workspace_id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    connector_name: str
    credential_type: str
    secret: str  # Decrypted plaintext secret (never logged or serialized to client)
    metadata: Dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime] = None


class CredentialRecord(BaseModel):
    """Safe metadata representation without secret."""
    model_config = ConfigDict(extra="ignore")
    id: uuid.UUID
    workspace_id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    connector_name: str
    credential_type: str
    has_secret: bool = True
    metadata: Dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime] = None


class CredentialStore:
    """
    Manages secure lifecycle of encrypted credentials per workspace.
    """

    def __init__(self, encryptor: Optional[SecretEncryptor] = None) -> None:
        self.encryptor = encryptor or get_secret_encryptor()

    async def save(
        self,
        session: AsyncSession,
        workspace_id: uuid.UUID,
        connector_name: str,
        credential_type: str,
        secret: str,
        metadata: Optional[Dict[str, Any]] = None,
        user_id: Optional[uuid.UUID] = None,
        expires_at: Optional[datetime] = None,
    ) -> CredentialRecord:
        """
        Encrypts and persists a credential record for the workspace.
        """
        encrypted = self.encryptor.encrypt(secret)
        clean_meta = dict(metadata or {})

        # Check existing record
        stmt = select(Credential).where(
            Credential.workspace_id == workspace_id,
            Credential.connector_name == connector_name,
        )
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            existing.credential_type = credential_type
            existing.encrypted_secret = encrypted
            existing.metadata_json = clean_meta
            existing.user_id = user_id
            existing.expires_at = expires_at
            existing.updated_at = datetime.now(timezone.utc)
            cred = existing
        else:
            cred = Credential(
                workspace_id=workspace_id,
                user_id=user_id,
                connector_name=connector_name,
                credential_type=credential_type,
                encrypted_secret=encrypted,
                metadata_json=clean_meta,
                expires_at=expires_at,
            )
            session.add(cred)

        await session.flush()
        await session.refresh(cred)

        logger.info(f"[CredentialStore] Persisted encrypted credential for '{connector_name}' in workspace '{workspace_id}'")

        return CredentialRecord(
            id=cred.id,
            workspace_id=cred.workspace_id,
            user_id=cred.user_id,
            connector_name=cred.connector_name,
            credential_type=cred.credential_type,
            has_secret=True,
            metadata=cred.metadata_json,
            created_at=cred.created_at,
            updated_at=cred.updated_at,
            expires_at=cred.expires_at,
        )

    async def get(
        self,
        session: Optional[AsyncSession],
        workspace_id: uuid.UUID,
        connector_name: str,
        user_id: Optional[uuid.UUID] = None,
    ) -> Optional[DecryptedCredential]:
        """
        Retrieves and decrypts the credential secret for execution.
        Falls back to environment variable for local development if not in DB.
        """
        if session is not None:
            stmt = select(Credential).where(
                Credential.workspace_id == workspace_id,
                Credential.connector_name == connector_name,
            )
            result = await session.execute(stmt)
            record = result.scalar_one_or_none()

            if record:
                decrypted_secret = self.encryptor.decrypt(record.encrypted_secret)
                return DecryptedCredential(
                    id=record.id,
                    workspace_id=record.workspace_id,
                    user_id=record.user_id,
                    connector_name=record.connector_name,
                    credential_type=record.credential_type,
                    secret=decrypted_secret,
                    metadata=record.metadata_json,
                    created_at=record.created_at,
                    updated_at=record.updated_at,
                    expires_at=record.expires_at,
                )

        # Local development environment variable fallback
        if connector_name == "github":
            env_token = settings.GITHUB_API_TOKEN or os.getenv("GITHUB_TOKEN")
            if env_token:
                return DecryptedCredential(
                    id=uuid.uuid4(),
                    workspace_id=workspace_id,
                    user_id=user_id,
                    connector_name="github",
                    credential_type="pat",
                    secret=env_token,
                    metadata={"source": "environment_variable"},
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )

        return None

    async def get_safe_record(
        self,
        session: AsyncSession,
        workspace_id: uuid.UUID,
        connector_name: str,
        user_id: Optional[uuid.UUID] = None,
    ) -> Optional[CredentialRecord]:
        """
        Retrieves metadata record without decrypting or exposing the secret.
        """
        stmt = select(Credential).where(
            Credential.workspace_id == workspace_id,
            Credential.connector_name == connector_name,
        )
        result = await session.execute(stmt)
        record = result.scalar_one_or_none()

        if record:
            return CredentialRecord(
                id=record.id,
                workspace_id=record.workspace_id,
                user_id=record.user_id,
                connector_name=record.connector_name,
                credential_type=record.credential_type,
                has_secret=True,
                metadata=record.metadata_json,
                created_at=record.created_at,
                updated_at=record.updated_at,
                expires_at=record.expires_at,
            )

        # Dev environment fallback check
        if connector_name == "github":
            env_token = settings.GITHUB_API_TOKEN or os.getenv("GITHUB_TOKEN")
            if env_token:
                return CredentialRecord(
                    id=uuid.uuid4(),
                    workspace_id=workspace_id,
                    user_id=user_id,
                    connector_name="github",
                    credential_type="pat",
                    has_secret=True,
                    metadata={"source": "environment_variable"},
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )

        return None

    async def delete(
        self,
        session: AsyncSession,
        workspace_id: uuid.UUID,
        connector_name: str,
        user_id: Optional[uuid.UUID] = None,
    ) -> bool:
        """
        Deletes stored credential for workspace.
        """
        stmt = delete(Credential).where(
            Credential.workspace_id == workspace_id,
            Credential.connector_name == connector_name,
        )
        res = await session.execute(stmt)
        deleted_count = res.rowcount or 0
        logger.info(f"[CredentialStore] Deleted {deleted_count} credentials for '{connector_name}' in workspace '{workspace_id}'")
        return deleted_count > 0

    async def exists(
        self,
        session: Optional[AsyncSession],
        workspace_id: uuid.UUID,
        connector_name: str,
        user_id: Optional[uuid.UUID] = None,
    ) -> bool:
        """
        Checks whether credentials exist for the connector in the workspace.
        """
        if session is not None:
            stmt = select(Credential.id).where(
                Credential.workspace_id == workspace_id,
                Credential.connector_name == connector_name,
            )
            result = await session.execute(stmt)
            if result.scalar_one_or_none() is not None:
                return True

        if connector_name == "github":
            if settings.GITHUB_API_TOKEN or os.getenv("GITHUB_TOKEN"):
                return True

        return False


_default_credential_store: Optional[CredentialStore] = None


def get_credential_store() -> CredentialStore:
    global _default_credential_store
    if _default_credential_store is None:
        _default_credential_store = CredentialStore()
    return _default_credential_store
