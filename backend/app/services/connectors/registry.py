"""
Dynamic registry for managing available external connectors.
"""
from typing import Dict, List, Optional
from backend.app.core.logging import logger
from backend.app.services.connectors.base import BaseConnector
from backend.app.services.connectors.errors import ConnectorNotFoundError
from backend.app.services.connectors.github import GitHubConnector
from backend.app.services.connectors.schemas import ConnectorMetadataResponse


class ConnectorRegistry:
    """
    Central registry for discovering, registering, and retrieving external connectors.
    Extensible architecture allowing new connectors to be registered without modifying the core engine.
    """

    def __init__(self) -> None:
        self._connectors: Dict[str, BaseConnector] = {}
        # Register default connectors
        self.register(GitHubConnector())

    def register(self, connector: BaseConnector) -> None:
        """Registers a connector instance."""
        if not isinstance(connector, BaseConnector):
            raise TypeError(f"Expected BaseConnector instance, got {type(connector)}")
        self._connectors[connector.name] = connector
        logger.info(f"[ConnectorRegistry] Registered connector '{connector.name}' (v{connector.version})")

    def unregister(self, name: str) -> Optional[BaseConnector]:
        """Removes a connector from the registry."""
        conn = self._connectors.pop(name, None)
        if conn:
            logger.info(f"[ConnectorRegistry] Unregistered connector '{name}'")
        return conn

    def get(self, name: str) -> Optional[BaseConnector]:
        """Retrieves a connector by name."""
        return self._connectors.get(name)

    def get_or_raise(self, name: str) -> BaseConnector:
        """Retrieves a connector or raises ConnectorNotFoundError."""
        conn = self.get(name)
        if not conn:
            raise ConnectorNotFoundError(name)
        return conn

    def exists(self, name: str) -> bool:
        """Returns True if the connector is registered."""
        return name in self._connectors

    def list(self) -> List[BaseConnector]:
        """Returns list of registered connector instances."""
        return list(self._connectors.values())

    def get_capabilities(self, name: str) -> List[str]:
        """Returns supported capability list for connector."""
        conn = self.get_or_raise(name)
        return list(conn.capabilities)

    def list_metadata(self) -> List[ConnectorMetadataResponse]:
        """Returns normalized metadata for all registered connectors."""
        return [conn.get_metadata() for conn in self._connectors.values()]


_default_connector_registry: Optional[ConnectorRegistry] = None


def get_connector_registry() -> ConnectorRegistry:
    """Dependency injection factory for ConnectorRegistry."""
    global _default_connector_registry
    if _default_connector_registry is None:
        _default_connector_registry = ConnectorRegistry()
    return _default_connector_registry
