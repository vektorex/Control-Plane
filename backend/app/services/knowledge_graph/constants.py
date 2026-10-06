"""
Constants and Enums for Step 29: Knowledge Graph and Structured Context Layer.
Provides controlled registries for entity types, relationship types, and statuses.
"""
from enum import Enum
from typing import Set


class EntityType(str, Enum):
    """
    Controlled registry of recognized entity categories in the AI Work Layer.
    Untrusted model outputs are validated against this registry.
    """
    PERSON = "person"
    ORGANIZATION = "organization"
    PROJECT = "project"
    REPOSITORY = "repository"
    FILE = "file"
    DOCUMENT = "document"
    TASK = "task"
    WORKFLOW = "workflow"
    WORKFLOW_STEP = "workflow_step"
    TECHNOLOGY = "technology"
    SERVICE = "service"
    API = "api"
    DATABASE = "database"
    MODEL = "model"
    PROMPT = "prompt"
    DATASET = "dataset"
    ISSUE = "issue"
    PULL_REQUEST = "pull_request"
    CONCEPT = "concept"
    TOPIC = "topic"
    EVENT = "event"
    # Step 43 Outcome Intelligence entity types
    OBJECTIVE = "objective"
    OUTCOME = "outcome"
    OUTCOME_TARGET = "outcome_target"
    MILESTONE = "milestone"
    DECISION = "decision"
    MEASUREMENT = "measurement"
    # Step 44 Planning entity types
    WORK_PLAN = "work_plan"
    PLANNING_ITEM = "planning_item"
    WORK_RESOURCE = "work_resource"
    CAPACITY_SNAPSHOT = "capacity_snapshot"
    PLANNING_CONSTRAINT = "planning_constraint"
    PLANNING_SCENARIO = "planning_scenario"


ALLOWED_ENTITY_TYPES: Set[str] = {e.value for e in EntityType}


class RelationshipType(str, Enum):
    """
    Controlled registry of semantic edge types connecting entities.
    """
    OWNS = "owns"
    MEMBER_OF = "member_of"
    PART_OF = "part_of"
    DEPENDS_ON = "depends_on"
    USES = "uses"
    IMPLEMENTS = "implements"
    CALLS = "calls"
    IMPORTS = "imports"
    CONTAINS = "contains"
    REFERENCES = "references"
    RELATED_TO = "related_to"
    DERIVED_FROM = "derived_from"
    CREATED_BY = "created_by"
    ASSIGNED_TO = "assigned_to"
    BELONGS_TO = "belongs_to"
    DEPLOYED_TO = "deployed_to"
    CONFIGURED_BY = "configured_by"
    DOCUMENTS = "documents"
    MENTIONS = "mentions"
    BLOCKS = "blocks"
    DUPLICATES = "duplicates"
    SUPERSEDES = "supersedes"
    TESTED_BY = "tested_by"
    EVALUATED_BY = "evaluated_by"
    # Step 43 Outcome Intelligence relationship types
    SUPPORTS = "supports"
    CONTRIBUTES_TO = "contributes_to"
    ACHIEVES = "achieves"
    MEASURES = "measures"
    DECIDED_BY = "decided_by"
    VALIDATED_BY = "validated_by"
    # Step 44 Planning relationship types
    PLANNED_FOR = "planned_for"
    ALLOCATED_TO = "allocated_to"
    CONSTRAINED_BY = "constrained_by"
    REQUIRES_CAPABILITY = "requires_capability"


ALLOWED_RELATIONSHIP_TYPES: Set[str] = {r.value for r in RelationshipType}


class EntityStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class RelationshipStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class ProposalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class SourceType(str, Enum):
    DOCUMENT = "document"
    CONNECTOR = "connector"
    WORKFLOW = "workflow"
    TASK = "task"
    PROJECT = "project"
    REPOSITORY = "repository"
    ISSUE = "issue"
    PULL_REQUEST = "pull_request"
    MANUAL = "manual"
    SYSTEM = "system"


ALLOWED_SOURCE_TYPES: Set[str] = {s.value for s in SourceType}


class ConflictType(str, Enum):
    DUPLICATE_ENTITY = "duplicate_entity"
    CONTRADICTORY_RELATIONSHIP = "contradictory_relationship"
    STALE_RELATIONSHIP = "stale_relationship"
    AMBIGUOUS_ENTITY = "ambiguous_entity"


class ConflictStatus(str, Enum):
    OPEN = "open"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class ChangeLogAction(str, Enum):
    CREATED = "created"
    UPDATED = "updated"
    ARCHIVED = "archived"
    MERGED = "merged"
    RELATIONSHIP_CREATED = "relationship_created"
    RELATIONSHIP_REMOVED = "relationship_removed"


# Traversal & context budgeting bounds
GRAPH_MAX_HOPS: int = 3
GRAPH_DEFAULT_HOPS: int = 1
GRAPH_MAX_ENTITIES: int = 100
GRAPH_MAX_RELATIONSHIPS: int = 200
MAX_GRAPH_CONTEXT_TOKENS: int = 3000
