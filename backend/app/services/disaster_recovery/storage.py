"""
Storage abstraction and encryption provider for Step 36: Disaster Recovery.
"""
import base64
import hashlib
import json
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional

from cryptography.fernet import Fernet

from backend.app.services.disaster_recovery.exceptions import (
    StorageProviderError,
    BackupEncryptionError,
)


class BackupStorageProvider(ABC):
    """
    Abstract interface for persisting, retrieving, and inspecting backup artifacts.
    """

    @abstractmethod
    def put(self, key: str, data: bytes, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Store backup artifact data and return storage reference URI."""
        pass

    @abstractmethod
    def get(self, key: str) -> bytes:
        """Retrieve stored backup artifact data."""
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if backup artifact exists."""
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete stored backup artifact."""
        pass

    @abstractmethod
    def list(self, prefix: str = "") -> List[str]:
        """List keys matching prefix."""
        pass

    @abstractmethod
    def get_metadata(self, key: str) -> Dict[str, Any]:
        """Retrieve metadata associated with storage key."""
        pass


class LocalBackupStorageProvider(BackupStorageProvider):
    """
    Local filesystem storage provider for backup artifacts.
    Configurable via BACKUP_STORAGE_PATH environment variable.
    """

    def __init__(self, base_path: Optional[str] = None):
        configured_path = base_path or os.getenv("BACKUP_STORAGE_PATH", "./data/backups")
        self.root_dir = Path(configured_path).resolve()
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def _get_path(self, key: str) -> Path:
        # Sanitize against path traversal
        clean_key = key.replace("\\", "/").strip("/")
        if ".." in clean_key:
            raise StorageProviderError(f"Path traversal detected in storage key: {key}")
        file_path = (self.root_dir / clean_key).resolve()
        if not str(file_path).startswith(str(self.root_dir)):
            raise StorageProviderError(f"Storage path escaped root directory: {key}")
        return file_path

    def put(self, key: str, data: bytes, metadata: Optional[Dict[str, Any]] = None) -> str:
        try:
            target_path = self._get_path(key)
            target_path.parent.mkdir(parents=True, exist_ok=True)
            with open(target_path, "wb") as f:
                f.write(data)

            # Persist companion metadata
            if metadata is not None:
                meta_path = target_path.with_suffix(target_path.suffix + ".meta.json")
                with open(meta_path, "w", encoding="utf-8") as mf:
                    json.dump(metadata, mf, indent=2)

            return f"local://{key}"
        except Exception as exc:
            raise StorageProviderError(f"Failed to put backup data into storage '{key}': {exc}")

    def get(self, key: str) -> bytes:
        try:
            target_path = self._get_path(key)
            if not target_path.exists():
                raise StorageProviderError(f"Backup file not found at key: {key}")
            with open(target_path, "rb") as f:
                return f.read()
        except Exception as exc:
            raise StorageProviderError(f"Failed to get backup data '{key}': {exc}")

    def exists(self, key: str) -> bool:
        try:
            return self._get_path(key).exists()
        except Exception:
            return False

    def delete(self, key: str) -> bool:
        try:
            target_path = self._get_path(key)
            if target_path.exists():
                target_path.unlink()
                meta_path = target_path.with_suffix(target_path.suffix + ".meta.json")
                if meta_path.exists():
                    meta_path.unlink()
                return True
            return False
        except Exception as exc:
            raise StorageProviderError(f"Failed to delete backup file '{key}': {exc}")

    def list(self, prefix: str = "") -> List[str]:
        results = []
        try:
            clean_prefix = prefix.replace("\\", "/").strip("/")
            search_dir = self.root_dir / clean_prefix if clean_prefix else self.root_dir
            if not search_dir.exists():
                return []
            for path in search_dir.rglob("*"):
                if path.is_file() and not path.name.endswith(".meta.json"):
                    rel = path.relative_to(self.root_dir).as_posix()
                    results.append(rel)
            return sorted(results)
        except Exception as exc:
            raise StorageProviderError(f"Failed to list backup directory: {exc}")

    def get_metadata(self, key: str) -> Dict[str, Any]:
        try:
            target_path = self._get_path(key)
            if not target_path.exists():
                return {}
            meta_path = target_path.with_suffix(target_path.suffix + ".meta.json")
            if meta_path.exists():
                with open(meta_path, "r", encoding="utf-8") as mf:
                    return json.load(mf)
            stat = target_path.stat()
            return {
                "size_bytes": stat.st_size,
                "modified_at": stat.st_mtime,
            }
        except Exception as exc:
            raise StorageProviderError(f"Failed to read backup metadata '{key}': {exc}")


class BackupEncryptionProvider:
    """
    Standard Fernet encryption provider for confidential and restricted backups.
    Generates deterministic or environment-derived keys without storing keys in backup payloads.
    """

    def __init__(self, key: Optional[bytes] = None):
        raw_secret = key or os.getenv("BACKUP_ENCRYPTION_KEY", "default-dev-backup-key-do-not-use-in-prod-32b").encode("utf-8")
        # Derive 32-byte urlsafe base64 key
        digest = hashlib.sha256(raw_secret).digest()
        self.fernet_key = base64.urlsafe_b64encode(digest)
        self.cipher = Fernet(self.fernet_key)

    def encrypt(self, data: bytes) -> bytes:
        try:
            return self.cipher.encrypt(data)
        except Exception as exc:
            raise BackupEncryptionError(f"Encryption failed: {exc}")

    def decrypt(self, token: bytes) -> bytes:
        try:
            return self.cipher.decrypt(token)
        except Exception as exc:
            raise BackupEncryptionError(f"Decryption failed: {exc}")

    def is_encrypted(self, data: bytes) -> bool:
        """Fernet tokens start with gAAAAA in urlsafe b64."""
        return data.startswith(b"gAAAAA")


def get_backup_storage_provider() -> BackupStorageProvider:
    """Factory returning configured storage provider."""
    provider_type = os.getenv("BACKUP_STORAGE_PROVIDER", "local").lower()
    if provider_type == "local":
        return LocalBackupStorageProvider()
    raise StorageProviderError(f"Unsupported storage provider type: {provider_type}")
