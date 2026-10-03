"""
Exceptions for Step 29 Knowledge Graph and Structured Context Layer.
"""
from typing import Any, Optional
from fastapi import status
from backend.app.core.errors import AppError


class KnowledgeGraphError(AppError):
    """Base exception for Knowledge Graph errors."""
    code = "KNOWLEDGE_GRAPH_ERROR"
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR


class EntityNotFoundError(KnowledgeGraphError):
    code = "ENTITY_NOT_FOUND"
    status_code = status.HTTP_404_NOT_FOUND


class RelationshipNotFoundError(KnowledgeGraphError):
    code = "RELATIONSHIP_NOT_FOUND"
    status_code = status.HTTP_404_NOT_FOUND


class InvalidEntityTypeError(KnowledgeGraphError):
    code = "INVALID_ENTITY_TYPE"
    status_code = status.HTTP_400_BAD_REQUEST


class InvalidRelationshipTypeError(KnowledgeGraphError):
    code = "INVALID_RELATIONSHIP_TYPE"
    status_code = status.HTTP_400_BAD_REQUEST


class CrossTenantGraphError(KnowledgeGraphError):
    code = "CROSS_TENANT_GRAPH_VIOLATION"
    status_code = status.HTTP_403_FORBIDDEN


class UnauthorizedGraphAccessError(KnowledgeGraphError):
    code = "UNAUTHORIZED_GRAPH_ACCESS"
    status_code = status.HTTP_403_FORBIDDEN


class ProposalNotFoundError(KnowledgeGraphError):
    code = "PROPOSAL_NOT_FOUND"
    status_code = status.HTTP_404_NOT_FOUND


class ConflictNotFoundError(KnowledgeGraphError):
    code = "CONFLICT_NOT_FOUND"
    status_code = status.HTTP_404_NOT_FOUND


class SelfRelationshipError(KnowledgeGraphError):
    code = "SELF_RELATIONSHIP_NOT_ALLOWED"
    status_code = status.HTTP_400_BAD_REQUEST


class EntityMergeError(KnowledgeGraphError):
    code = "ENTITY_MERGE_ERROR"
    status_code = status.HTTP_400_BAD_REQUEST


class ExtractionValidationError(KnowledgeGraphError):
    code = "EXTRACTION_VALIDATION_ERROR"
    status_code = status.HTTP_400_BAD_REQUEST


class DanglingEntityError(KnowledgeGraphError):
    code = "DANGLING_ENTITY_ERROR"
    status_code = status.HTTP_400_BAD_REQUEST
