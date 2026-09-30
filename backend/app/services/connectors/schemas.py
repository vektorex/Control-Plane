"""
Pydantic schemas and enums for the Connector System.
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class ConnectorCapability(str, Enum):
    READ = "read"
    SEARCH = "search"
    LIST = "list"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


class PermissionLevel(str, Enum):
    READ = "read"
    WRITE = "write"
    DESTRUCTIVE = "destructive"


class ConnectorCategory(str, Enum):
    CODE = "code"
    PRODUCTIVITY = "productivity"
    COMMUNICATION = "communication"
    STORAGE = "storage"
    DATABASES = "databases"
    KNOWLEDGE = "knowledge"
    PROJECT_MANAGEMENT = "project_management"


class ConnectorAuthType(str, Enum):
    PAT = "pat"
    OAUTH = "oauth"
    API_KEY = "api_key"


class ConnectionStatus(str, Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    EXPIRED = "expired"
    INVALID = "invalid"
    UNAVAILABLE = "unavailable"


class ConnectorOperationMetadata(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: str = Field(..., description="Unique operation key, e.g. 'search_repositories'")
    display_name: str = Field(..., description="Human-readable operation label")
    description: str = Field(..., description="Detailed description of the operation")
    capability: ConnectorCapability = Field(default=ConnectorCapability.READ)
    permission_level: PermissionLevel = Field(default=PermissionLevel.READ)
    parameters_schema: Dict[str, Any] = Field(default_factory=dict, description="JSON schema defining accepted arguments")


class ConnectorMetadataResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: str = Field(..., description="Unique connector identifier, e.g. 'github'")
    display_name: str = Field(..., description="Human-readable connector name")
    description: str = Field(..., description="Summary of connector purpose")
    category: str = Field(..., description="Category group")
    version: str = Field(default="1.0.0")
    capabilities: List[str] = Field(default_factory=list)
    auth_type: str = Field(default="pat")
    supported_operations: List[ConnectorOperationMetadata] = Field(default_factory=list)
    status: Optional[str] = Field(default="disconnected", description="Connection status in active workspace")
    account: Optional[Dict[str, Any]] = Field(default=None, description="Safe connected account info (no secrets)")


class ConnectorStatusResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    connector: str
    status: str  # connected | disconnected | expired | invalid | unavailable
    account: Optional[Dict[str, Any]] = None
    last_verified_at: Optional[datetime] = None
    has_credentials: bool = False
    message: Optional[str] = None


class ConnectorConnectRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    credential: str = Field(..., min_length=1, description="Personal access token, API key, or oauth secret")
    credential_type: str = Field(default="pat", description="Credential type: pat | api_key | oauth")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Optional safe metadata (e.g. account name)")


class ConnectorExecuteRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    operation: str = Field(..., description="Operation to execute")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Operation arguments")


class ConnectorResult(BaseModel):
    model_config = ConfigDict(extra="ignore")
    success: bool
    connector: str
    operation: str
    data: Optional[Dict[str, Any]] = None
    items: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    source: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None


class ConnectorPermissionResponse(BaseModel):
    model_config = ConfigDict(extra="ignore", from_attributes=True)
    id: Optional[UUID] = None
    workspace_id: UUID
    connector_name: str
    operation: str
    permission_level: str
    enabled: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ConnectorPermissionUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    operation: str = Field(..., description="Operation name")
    enabled: bool = Field(..., description="Whether this operation is permitted")
    permission_level: Optional[str] = Field(default="read", description="Permission level")


class ConnectorTestResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    success: bool
    connector: str
    status: str
    account: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
