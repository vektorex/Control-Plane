import asyncio
import os
from pathlib import Path
from typing import Optional

from backend.app.core.errors import NotFoundError, StorageError
from backend.app.services.storage.base import FileStorage


class LocalFileStorage(FileStorage):
    """
    Local filesystem implementation of FileStorage.
    Persists uploaded documents safely outside the source tree with strict
    path traversal validation and directory auto-creation.
    """

    def __init__(self, base_path: str = ".storage/documents") -> None:
        self.base_path = Path(base_path).resolve()
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _resolve_safe_path(self, storage_key: str) -> Path:
        """
        Resolves a storage key to an absolute filesystem path and guards against path traversal.
        """
        # Strip leading slashes to prevent root escaping
        clean_key = storage_key.lstrip("/\\")
        target_path = (self.base_path / clean_key).resolve()

        if not str(target_path).startswith(str(self.base_path)):
            raise StorageError(f"Security error: Invalid storage key path traversal attempt '{storage_key}'.")

        return target_path

    async def upload(self, storage_key: str, data: bytes, content_type: Optional[str] = None) -> str:
        target_path = self._resolve_safe_path(storage_key)
        target_path.parent.mkdir(parents=True, exist_ok=True)

        def _write():
            with open(target_path, "wb") as f:
                f.write(data)

        try:
            await asyncio.to_thread(_write)
            return storage_key
        except Exception as e:
            raise StorageError(f"Failed to write file to local storage: {str(e)}")

    async def download(self, storage_key: str) -> bytes:
        target_path = self._resolve_safe_path(storage_key)
        if not target_path.exists() or not target_path.is_file():
            raise NotFoundError(f"Document file at storage key '{storage_key}' not found.")

        def _read() -> bytes:
            with open(target_path, "rb") as f:
                return f.read()

        try:
            return await asyncio.to_thread(_read)
        except NotFoundError:
            raise
        except Exception as e:
            raise StorageError(f"Failed to read file from local storage: {str(e)}")

    async def delete(self, storage_key: str) -> bool:
        target_path = self._resolve_safe_path(storage_key)
        if not target_path.exists():
            return True

        def _remove():
            if target_path.is_file():
                target_path.unlink()

        try:
            await asyncio.to_thread(_remove)
            return True
        except Exception as e:
            raise StorageError(f"Failed to delete file from local storage: {str(e)}")

    async def exists(self, storage_key: str) -> bool:
        target_path = self._resolve_safe_path(storage_key)
        return target_path.exists() and target_path.is_file()
