"""
Base abstract connector interface and contracts.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from backend.app.services.connectors.schemas import (
    ConnectorMetadataResponse,
    ConnectorOperationMetadata,
    ConnectorResult,
)


class BaseConnector(ABC):
    """
    Provider-independent abstract base class for all external service connectors.
    """
    name: str
    display_name: str
    description: str
    category: str
    version: str = "1.0.0"
    capabilities: List[str] = []
    auth_type: str = "pat"
    supported_operations: List[ConnectorOperationMetadata] = []

    def get_metadata(self) -> ConnectorMetadataResponse:
        """Returns standard metadata for this connector."""
        return ConnectorMetadataResponse(
            name=self.name,
            display_name=self.display_name,
            description=self.description,
            category=self.category,
            version=self.version,
            capabilities=self.capabilities,
            auth_type=self.auth_type,
            supported_operations=self.supported_operations,
        )

    def get_operation(self, operation_name: str) -> Optional[ConnectorOperationMetadata]:
        """Look up an operation metadata definition by name."""
        for op in self.supported_operations:
            if op.name == operation_name:
                return op
        return None

    def has_operation(self, operation_name: str) -> bool:
        """Returns True if the operation is supported by this connector."""
        return self.get_operation(operation_name) is not None

    @abstractmethod
    async def test_connection(
        self,
        credentials: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Validates authentication credentials against the remote service and returns
        safe account information. Never returns secrets.
        """
        pass

    @abstractmethod
    async def execute_operation(
        self,
        operation: str,
        arguments: Dict[str, Any],
        credentials: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ConnectorResult:
        """
        Executes a named operation with supplied arguments and credentials.
        Returns a normalized ConnectorResult.
        """
        pass
