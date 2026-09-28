from typing import Any, Dict, List, Optional
from backend.app.core.errors import ModelNotFoundError, ValidationError
from backend.app.core.logging import logger
from backend.app.services.models.base import ModelDefinition
from backend.app.services.models.catalog import get_default_catalog


class ModelRegistry:
    """
    Central, thread-safe registry for model metadata, capability flags, and policy enforcement.
    Decouples model definitions from vendor adapters and orchestrators.
    """

    def __init__(self, load_defaults: bool = True):
        self._models: Dict[str, ModelDefinition] = {}  # key: "provider/model_id" and "model_id"
        self._models_by_provider: Dict[str, List[ModelDefinition]] = {}
        if load_defaults:
            self._load_defaults()

    def _load_defaults(self):
        for model in get_default_catalog():
            self.register_model(model)
        logger.info(f"[ModelRegistry] Loaded {len(self.list_models(enabled_only=False))} models into catalog.")

    def register_model(self, model: ModelDefinition) -> None:
        """Register a new or updated model definition."""
        canonical_key = f"{model.provider}/{model.model_id}"
        self._models[canonical_key] = model
        # Also map bare model_id if not colliding or if preferred
        self._models[model.model_id] = model

        if model.provider not in self._models_by_provider:
            self._models_by_provider[model.provider] = []
        # Replace existing if already present
        self._models_by_provider[model.provider] = [
            m for m in self._models_by_provider[model.provider] if m.model_id != model.model_id
        ]
        self._models_by_provider[model.provider].append(model)

    def get_model(self, model_id: str, provider: Optional[str] = None) -> Optional[ModelDefinition]:
        """
        Retrieve a model definition by ID or provider/model_id.
        """
        if "/" in model_id:
            return self._models.get(model_id)
        if provider:
            canonical_key = f"{provider}/{model_id}"
            if canonical_key in self._models:
                return self._models[canonical_key]
        return self._models.get(model_id)

    def list_models(
        self,
        enabled_only: bool = True,
        provider: Optional[str] = None,
        capability: Optional[str] = None,
    ) -> List[ModelDefinition]:
        """
        List models registered in the catalog with optional filtering.
        Deduplicates canonical models.
        """
        seen_keys = set()
        result: List[ModelDefinition] = []

        for key, model in self._models.items():
            canonical_key = f"{model.provider}/{model.model_id}"
            if canonical_key in seen_keys:
                continue
            seen_keys.add(canonical_key)

            if enabled_only and not model.enabled:
                continue
            if provider and model.provider != provider:
                continue
            if capability and not model.has_capability(capability):
                continue

            result.append(model)

        return result

    def list_models_for_user(self, user: Any, enabled_only: bool = True) -> List[Dict[str, Any]]:
        """
        Return safe, serialized model metadata for authenticated client consumption.
        Never exposes API keys or internal infrastructure secrets.
        """
        models = self.list_models(enabled_only=enabled_only)
        return [
            {
                "id": m.model_id,
                "provider": m.provider,
                "name": m.display_name,
                "display_name": m.display_name,
                "description": m.description,
                "capabilities": m.capabilities,
                "context_window": m.context_window,
                "supports_streaming": m.supports_streaming,
                "supports_tools": m.supports_tools,
                "supports_vision": m.supports_vision,
                "supports_structured_output": m.supports_structured_output,
                "cost_class": m.cost_class,
                "latency_class": m.latency_class,
                "is_default": m.is_default,
                "enabled": m.enabled,
            }
            for m in models
        ]

    def is_model_supported(self, model_id: str, provider: Optional[str] = None) -> bool:
        """Check if model exists and is enabled."""
        m = self.get_model(model_id, provider=provider)
        return m is not None and m.enabled

    def validate_model_access(self, model_id: str, provider: Optional[str] = None) -> ModelDefinition:
        """
        Validate that a requested model exists, is enabled, and is allowed by server policy.
        Raises ModelNotFoundError or ValidationError if invalid.
        """
        model = self.get_model(model_id, provider=provider)
        if not model:
            raise ModelNotFoundError(f"Model '{model_id}' is not registered in the Model Registry.")
        if not model.enabled:
            raise ValidationError(f"Model '{model_id}' is currently disabled by server policy.")
        return model


# Global singleton instance
default_model_registry = ModelRegistry()
