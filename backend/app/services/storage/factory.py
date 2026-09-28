from typing import Optional
from backend.app.config import settings
from backend.app.services.storage.base import FileStorage
from backend.app.services.storage.local import LocalFileStorage

_global_storage: Optional[FileStorage] = None


def get_storage() -> FileStorage:
    """
    Factory function returning the configured FileStorage backend.
    """
    global _global_storage
    if _global_storage is None:
        _global_storage = LocalFileStorage(base_path=settings.DOCUMENT_STORAGE_PATH)
    return _global_storage


def set_storage(storage: FileStorage) -> None:
    """Override storage backend for testing."""
    global _global_storage
    _global_storage = storage


# Alias
get_file_storage = get_storage
