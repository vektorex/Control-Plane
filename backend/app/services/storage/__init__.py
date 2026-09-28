from backend.app.services.storage.base import FileStorage
from backend.app.services.storage.factory import get_file_storage, get_storage, set_storage
from backend.app.services.storage.local import LocalFileStorage

__all__ = [
    "FileStorage",
    "LocalFileStorage",
    "get_storage",
    "get_file_storage",
    "set_storage",
]
