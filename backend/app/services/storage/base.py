from abc import ABC, abstractmethod
from typing import Optional


class FileStorage(ABC):
    """
    Abstract Base Class for document file persistence.
    Provides a decoupled storage abstraction capable of backing local disk,
    Cloudflare R2, AWS S3, or in-memory test fixtures.
    """

    @abstractmethod
    async def upload(self, storage_key: str, data: bytes, content_type: Optional[str] = None) -> str:
        """
        Uploads binary file data to the specified storage key.
        Returns the confirmed storage key.
        """
        pass

    @abstractmethod
    async def download(self, storage_key: str) -> bytes:
        """
        Retrieves binary file contents for the given storage key.
        """
        pass

    @abstractmethod
    async def delete(self, storage_key: str) -> bool:
        """
        Deletes the file at storage_key. Returns True if deleted or did not exist.
        """
        pass

    @abstractmethod
    async def exists(self, storage_key: str) -> bool:
        """
        Checks if a file exists at the given storage key.
        """
        pass
