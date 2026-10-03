"""
GovernanceClassifiers: deterministic metadata classifiers used as safe policy inputs.
Never uses LLM output as an authoritative classification. Step 32.
"""
from typing import List, Optional

from backend.app.services.governance.constants import (
    ActionCategory,
    DataClassification,
)


class ModelCapabilityClassifier:
    """Classifies model capabilities relevant to governance decisions."""

    MULTIMODAL_CAPABILITIES = {"vision", "image", "audio", "video", "multimodal"}
    CODE_CAPABILITIES = {"code", "code_generation", "code_execution"}
    TOOL_CAPABILITIES = {"tools", "function_calling", "tool_use"}

    @staticmethod
    def requires_vision(capabilities: List[str]) -> bool:
        return bool(set(c.lower() for c in capabilities) & ModelCapabilityClassifier.MULTIMODAL_CAPABILITIES)

    @staticmethod
    def requires_tool_use(capabilities: List[str]) -> bool:
        return bool(set(c.lower() for c in capabilities) & ModelCapabilityClassifier.TOOL_CAPABILITIES)

    @staticmethod
    def requires_code(capabilities: List[str]) -> bool:
        return bool(set(c.lower() for c in capabilities) & ModelCapabilityClassifier.CODE_CAPABILITIES)


class ArtifactTypeClassifier:
    """Classifies artifact types for governance decisions."""

    HIGH_RISK_TYPES = {"code_file", "executable", "archive", "script"}
    SENSITIVE_TYPES = {"medical_record", "legal_document", "financial_report", "credentials_file"}
    MULTIMODAL_TYPES = {"image", "audio", "video", "spreadsheet", "pdf"}

    @staticmethod
    def is_high_risk(artifact_type: str) -> bool:
        return artifact_type.lower() in ArtifactTypeClassifier.HIGH_RISK_TYPES

    @staticmethod
    def is_sensitive(artifact_type: str) -> bool:
        return artifact_type.lower() in ArtifactTypeClassifier.SENSITIVE_TYPES

    @staticmethod
    def implied_classification(artifact_type: str) -> DataClassification:
        if ArtifactTypeClassifier.is_sensitive(artifact_type):
            return DataClassification.CONFIDENTIAL
        if ArtifactTypeClassifier.is_high_risk(artifact_type):
            return DataClassification.INTERNAL
        return DataClassification.INTERNAL


class ProviderClassifier:
    """Classifies AI providers for governance constraints."""

    KNOWN_PROVIDERS = {"openai", "anthropic", "google", "cohere", "mistral", "together", "local"}

    @staticmethod
    def is_known_provider(provider: str) -> bool:
        return provider.lower() in ProviderClassifier.KNOWN_PROVIDERS

    @staticmethod
    def normalize(provider: str) -> str:
        return provider.lower().strip()


class TaskTypeClassifier:
    """Classifies task types for governance decisions."""

    SIDE_EFFECTING_TYPES = {
        "connector_write", "notification", "webhook_delivery",
        "hitl_decision", "external_api_call", "file_write",
    }
    DETERMINISTIC_TYPES = {
        "summarization", "translation", "extraction", "classification",
        "analysis", "qa", "question_answering", "code_review",
    }

    @staticmethod
    def is_side_effecting(task_type: str) -> bool:
        return task_type.lower() in TaskTypeClassifier.SIDE_EFFECTING_TYPES

    @staticmethod
    def is_deterministic(task_type: str) -> bool:
        return task_type.lower() in TaskTypeClassifier.DETERMINISTIC_TYPES

    @staticmethod
    def implied_action_category(task_type: str) -> ActionCategory:
        if TaskTypeClassifier.is_side_effecting(task_type):
            if any(x in task_type.lower() for x in ["delete", "destroy", "remove"]):
                return ActionCategory.DESTRUCTIVE
            return ActionCategory.WRITE
        return ActionCategory.READ
