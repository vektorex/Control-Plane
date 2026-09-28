from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type
from pydantic import BaseModel

from backend.app.db.models.user import User


class BaseTool(ABC):
    """
    Provider-independent abstract base interface for all tools.
    Every tool defines its name, description, input schema, permission requirements,
    and asynchronous execution handler.
    """
    name: str
    description: str
    input_schema: Type[BaseModel]
    requires_auth: bool = True
    metadata: Dict[str, Any] = {}

    def get_input_json_schema(self) -> Dict[str, Any]:
        """Returns the JSON Schema specification for this tool's input model."""
        if hasattr(self.input_schema, "model_json_schema"):
            return self.input_schema.model_json_schema()
        return {}

    def validate_input(self, raw_input: Any) -> Any:
        """Validates and parses raw dictionary arguments into the tool's Pydantic input schema."""
        if hasattr(self, "input_schema") and self.input_schema is not None:
            if isinstance(raw_input, dict):
                return self.input_schema.model_validate(raw_input)
            elif isinstance(raw_input, self.input_schema):
                return raw_input
        return raw_input

    def check_permission(
        self,
        user: Optional[User] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Enforces tool authorization permissions.
        Extensible for future workspace_allowed, project_allowed, user_allowed, admin_only.
        """
        if self.requires_auth and user is None:
            return False
        return True

    @abstractmethod
    async def execute(
        self,
        input_data: BaseModel,
        user: Optional[User] = None,
        **kwargs: Any,
    ) -> Any:
        """
        Executes the tool with validated Pydantic input arguments and returns output data.
        Must be implemented by concrete tool classes.
        """
        pass
