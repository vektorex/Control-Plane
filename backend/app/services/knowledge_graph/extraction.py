"""
Extraction service for Knowledge Graph.
Extracts entities and relationships from documents, connectors, workflows, and tasks.
Enforces strict structured validation, treats external text as untrusted, and creates proposals when approval is required.
"""
import hashlib
import json
import logging
import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.ai_gateway.gateway import default_ai_gateway
from backend.app.services.ai_gateway.requests import GatewayRequest
from backend.app.services.knowledge_graph.constants import (
    ALLOWED_ENTITY_TYPES,
    ALLOWED_RELATIONSHIP_TYPES,
    EntityType,
    ProposalStatus,
    RelationshipType,
    SourceType,
)
from backend.app.services.knowledge_graph.errors import ExtractionValidationError
from backend.app.services.knowledge_graph.models import Entity, Relationship
from backend.app.services.knowledge_graph.normalization import (
    normalize_entity_name,
    normalize_entity_type,
)
from backend.app.services.knowledge_graph.repository import KnowledgeGraphRepository
from backend.app.services.knowledge_graph.resolver import EntityResolver
from backend.app.services.knowledge_graph.sanitizer import (
    sanitize_properties,
    sanitize_source_metadata,
)
from backend.app.services.knowledge_graph.schemas import (
    ExtractedEntity,
    ExtractedRelationship,
    GraphExtractResponse,
    GraphExtractionPayload,
)

logger = logging.getLogger(__name__)


EXTRACTION_SYSTEM_PROMPT = """You are a precise knowledge graph extraction engine.
Analyze the provided text and extract significant named entities and the relationships between them.
Return strictly valid JSON with the exact following structure:
{
  "entities": [
    {
      "canonical_name": "Entity Name",
      "entity_type": "technology|service|api|database|model|person|organization|project|concept|document|topic",
      "description": "Short summary",
      "properties": {},
      "aliases": ["Alternative Name"],
      "confidence": 0.95
    }
  ],
  "relationships": [
    {
      "source_name": "Entity Name A",
      "relationship_type": "depends_on|uses|implements|calls|contains|references|related_to|part_of|belongs_to|deployed_to|documents|mentions",
      "target_name": "Entity Name B",
      "properties": {},
      "confidence": 0.90
    }
  ]
}
Do NOT include preamble, markdown backticks, or reasoning. Output only the JSON."""


class GraphExtractionService:
    """
    Coordinates extraction of structured knowledge graph elements from heterogeneous sources.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = KnowledgeGraphRepository(session)
        self.resolver = EntityResolver(session)

    async def extract_from_text(
        self,
        organization_id: uuid.UUID,
        workspace_id: uuid.UUID,
        text: str,
        source_id: str,
        source_type: str = "document",
        project_id: Optional[uuid.UUID] = None,
        require_approval: bool = False,
        actor_id: Optional[uuid.UUID] = None,
    ) -> GraphExtractResponse:
        """
        Extracts entities and relationships from arbitrary text using the unified AI Gateway.
        Validates against strict Pydantic schemas, and routes to proposals if approval required.
        """
        if not text or not text.strip():
            return GraphExtractResponse(message="Empty text provided for extraction.")

        content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()

        # Execute through AI Gateway
        prompt_payload = f"Text to extract entities and relationships from:\n\n{text[:8000]}"
        gw_res = await default_ai_gateway.execute(
            GatewayRequest(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt_payload},
                ],
                temperature=0.0,
                max_tokens=2048,
                response_format={"type": "json_object"},
                workspace_id=str(workspace_id),
            ),
            db=self.session,
        )

        raw_output = gw_res.content.strip()
        # Clean potential markdown fences
        if raw_output.startswith("```json"):
            raw_output = raw_output[7:]
        elif raw_output.startswith("```"):
            raw_output = raw_output[3:]
        if raw_output.endswith("```"):
            raw_output = raw_output[:-3]
        raw_output = raw_output.strip()

        try:
            payload = GraphExtractionPayload.model_validate_json(raw_output)
        except Exception as e:
            logger.warning(f"[GraphExtraction] Failed to validate LLM output: {e}\nRaw output: {raw_output[:200]}")
            # Try parsing json directly
            try:
                data = json.loads(raw_output)
                payload = GraphExtractionPayload.model_validate(data)
            except Exception as e2:
                raise ExtractionValidationError(f"Extraction produced malformed payload: {e2}")

        # Filter entities to valid types
        valid_entities: List[ExtractedEntity] = []
        for ent in payload.entities:
            norm_type = normalize_entity_type(ent.entity_type)
            if norm_type in ALLOWED_ENTITY_TYPES and ent.canonical_name.strip():
                ent.entity_type = norm_type
                ent.properties = sanitize_properties(ent.properties)
                valid_entities.append(ent)

        # Filter relationships to valid types
        valid_relationships: List[ExtractedRelationship] = []
        for rel in payload.relationships:
            norm_rel = rel.relationship_type.strip().lower()
            if (
                norm_rel in ALLOWED_RELATIONSHIP_TYPES
                and rel.source_name.strip()
                and rel.target_name.strip()
                and rel.source_name.strip().lower() != rel.target_name.strip().lower()
            ):
                rel.relationship_type = norm_rel
                rel.properties = sanitize_properties(rel.properties)
                valid_relationships.append(rel)

        # Check if approval is required (or if confidence is low)
        has_low_confidence = any(e.confidence < 0.85 for e in valid_entities) or any(r.confidence < 0.80 for r in valid_relationships)
        if require_approval or has_low_confidence:
            proposal = await self.repo.create_proposal(
                organization_id=organization_id,
                workspace_id=workspace_id,
                source_id=source_id,
                source_type=source_type,
                proposed_entities=[e.model_dump() for e in valid_entities],
                proposed_relationships=[r.model_dump() for r in valid_relationships],
                created_by=actor_id or uuid.uuid4(),
                project_id=project_id,
            )
            return GraphExtractResponse(
                proposal_id=proposal.id,
                entities_created=0,
                relationships_created=0,
                message="Graph change proposal created pending review.",
            )

        # Persist directly through EntityResolver and RelationshipService
        created_entities_count = 0
        resolved_name_to_id: Dict[str, uuid.UUID] = {}

        for ent in valid_entities:
            entity_resp, was_created = await self.resolver.resolve_or_create_entity(
                organization_id=organization_id,
                workspace_id=workspace_id,
                raw_name=ent.canonical_name,
                entity_type=ent.entity_type,
                description=ent.description,
                properties=ent.properties,
                source_type=source_type,
                source_id=source_id,
                content_hash=content_hash,
                project_id=project_id,
                confidence=ent.confidence,
            )
            resolved_name_to_id[normalize_entity_name(ent.canonical_name)] = entity_resp.id
            if was_created:
                created_entities_count += 1

        # Create relationships
        created_rels_count = 0
        from backend.app.services.knowledge_graph.relationship_service import RelationshipService
        from backend.app.services.knowledge_graph.schemas import RelationshipCreateRequest
        rel_service = RelationshipService(self.session)

        for rel in valid_relationships:
            s_norm = normalize_entity_name(rel.source_name)
            t_norm = normalize_entity_name(rel.target_name)

            s_id = resolved_name_to_id.get(s_norm)
            t_id = resolved_name_to_id.get(t_norm)

            if s_id and t_id and s_id != t_id:
                # Check if relationship already exists
                existing = await self.repo.get_relationship(
                    workspace_id=workspace_id,
                    source_id=s_id,
                    relationship_type=rel.relationship_type,
                    target_id=t_id,
                )
                if not existing:
                    try:
                        await rel_service.create_relationship(
                            organization_id=organization_id,
                            workspace_id=workspace_id,
                            request=RelationshipCreateRequest(
                                source_entity_id=s_id,
                                relationship_type=rel.relationship_type,
                                target_entity_id=t_id,
                                properties=rel.properties,
                                source_reference={"source_type": source_type, "source_id": source_id},
                                confidence=rel.confidence,
                                project_id=project_id,
                            ),
                            actor_id=actor_id,
                        )
                        created_rels_count += 1
                    except Exception as e:
                        logger.warning(f"[GraphExtraction] Could not create relationship {s_norm} -> {t_norm}: {e}")

        return GraphExtractResponse(
            entities_created=created_entities_count,
            relationships_created=created_rels_count,
            message=f"Successfully extracted and integrated {created_entities_count} entities and {created_rels_count} relationships.",
        )

    async def extract_from_workflow_metadata(
        self,
        organization_id: uuid.UUID,
        workspace_id: uuid.UUID,
        workflow_id: uuid.UUID,
        workflow_name: str,
        steps: List[Dict[str, Any]],
        project_id: Optional[uuid.UUID] = None,
    ) -> GraphExtractResponse:
        """
        Constructs graph entities and dependencies from trusted workflow structures.
        """
        # 1. Workflow entity
        wf_entity, _ = await self.resolver.resolve_or_create_entity(
            organization_id=organization_id,
            workspace_id=workspace_id,
            raw_name=workflow_name,
            entity_type=EntityType.WORKFLOW.value,
            description=f"Workflow orchestrator: {workflow_name}",
            source_type=SourceType.WORKFLOW.value,
            source_id=str(workflow_id),
            project_id=project_id,
        )

        from backend.app.services.knowledge_graph.relationship_service import RelationshipService
        from backend.app.services.knowledge_graph.schemas import RelationshipCreateRequest
        rel_service = RelationshipService(self.session)

        created_entities = 1
        created_rels = 0

        for step in steps:
            step_name = step.get("name") or f"Step {step.get('step_id', '')}"
            step_entity, _ = await self.resolver.resolve_or_create_entity(
                organization_id=organization_id,
                workspace_id=workspace_id,
                raw_name=f"{workflow_name} - {step_name}",
                entity_type=EntityType.WORKFLOW_STEP.value,
                description=f"Step in workflow {workflow_name}",
                properties={"step_type": step.get("step_type", "task")},
                source_type=SourceType.WORKFLOW.value,
                source_id=str(workflow_id),
                project_id=project_id,
            )
            created_entities += 1

            # workflow -> contains -> workflow_step
            existing_rel = await self.repo.get_relationship(
                workspace_id=workspace_id,
                source_id=wf_entity.id,
                relationship_type=RelationshipType.CONTAINS.value,
                target_id=step_entity.id,
            )
            if not existing_rel:
                await rel_service.create_relationship(
                    organization_id=organization_id,
                    workspace_id=workspace_id,
                    request=RelationshipCreateRequest(
                        source_entity_id=wf_entity.id,
                        relationship_type=RelationshipType.CONTAINS.value,
                        target_entity_id=step_entity.id,
                        source_reference={"workflow_id": str(workflow_id)},
                        project_id=project_id,
                    ),
                )
                created_rels += 1

            # step -> uses -> prompt (if managed prompt referenced)
            prompt_key = step.get("prompt_key") or step.get("config", {}).get("prompt_key")
            if prompt_key:
                prompt_entity, _ = await self.resolver.resolve_or_create_entity(
                    organization_id=organization_id,
                    workspace_id=workspace_id,
                    raw_name=prompt_key,
                    entity_type=EntityType.PROMPT.value,
                    description=f"Managed prompt asset: {prompt_key}",
                    source_type="prompt_registry",
                    source_id=prompt_key,
                    project_id=project_id,
                )
                created_entities += 1

                p_rel = await self.repo.get_relationship(
                    workspace_id=workspace_id,
                    source_id=step_entity.id,
                    relationship_type=RelationshipType.USES.value,
                    target_id=prompt_entity.id,
                )
                if not p_rel:
                    await rel_service.create_relationship(
                        organization_id=organization_id,
                        workspace_id=workspace_id,
                        request=RelationshipCreateRequest(
                            source_entity_id=step_entity.id,
                            relationship_type=RelationshipType.USES.value,
                            target_entity_id=prompt_entity.id,
                            source_reference={"step": step_name},
                            project_id=project_id,
                        ),
                    )
                    created_rels += 1

        return GraphExtractResponse(
            entities_created=created_entities,
            relationships_created=created_rels,
            message="Workflow metadata graph integration completed.",
        )

    async def extract_from_github_metadata(
        self,
        organization_id: uuid.UUID,
        workspace_id: uuid.UUID,
        repo_name: str,
        files: Optional[List[str]] = None,
        issues: Optional[List[Dict[str, Any]]] = None,
        pull_requests: Optional[List[Dict[str, Any]]] = None,
        project_id: Optional[uuid.UUID] = None,
    ) -> GraphExtractResponse:
        """
        Step 29 Requirement 35: Constructs graph entities and relationships from GitHub connector data.
        Entities: repository, file, issue, pull_request, person
        Relationships:
          repository -> contains -> file
          issue -> belongs_to -> repository
          pull_request -> belongs_to -> repository
          pull_request -> references -> issue
          person -> created_by -> issue
        """
        from backend.app.services.knowledge_graph.relationship_service import RelationshipService
        from backend.app.services.knowledge_graph.schemas import RelationshipCreateRequest
        rel_service = RelationshipService(self.session)

        created_entities = 0
        created_rels = 0

        # 1. Repository Entity
        repo_entity, _ = await self.resolver.resolve_or_create_entity(
            organization_id=organization_id,
            workspace_id=workspace_id,
            raw_name=repo_name,
            entity_type=EntityType.REPOSITORY.value,
            description=f"GitHub Repository {repo_name}",
            source_type=SourceType.REPOSITORY.value,
            source_id=repo_name,
            project_id=project_id,
        )
        created_entities += 1

        # 2. Files: repository -> contains -> file
        if files:
            for fpath in files:
                file_entity, _ = await self.resolver.resolve_or_create_entity(
                    organization_id=organization_id,
                    workspace_id=workspace_id,
                    raw_name=fpath,
                    entity_type=EntityType.FILE.value,
                    description=f"File in {repo_name}: {fpath}",
                    source_type=SourceType.REPOSITORY.value,
                    source_id=f"{repo_name}/{fpath}",
                    project_id=project_id,
                )
                created_entities += 1

                existing = await self.repo.get_relationship(
                    workspace_id=workspace_id,
                    source_id=repo_entity.id,
                    relationship_type=RelationshipType.CONTAINS.value,
                    target_id=file_entity.id,
                )
                if not existing:
                    await rel_service.create_relationship(
                        organization_id=organization_id,
                        workspace_id=workspace_id,
                        request=RelationshipCreateRequest(
                            source_entity_id=repo_entity.id,
                            relationship_type=RelationshipType.CONTAINS.value,
                            target_entity_id=file_entity.id,
                            source_reference={"repo": repo_name, "file": fpath},
                            project_id=project_id,
                        ),
                    )
                    created_rels += 1

        # Map to track created issue entities by issue number/id
        issue_entity_map: Dict[str, Any] = {}

        # 3. Issues: issue -> belongs_to -> repository; person -> created_by -> issue
        if issues:
            for iss in issues:
                iss_num = str(iss.get("number") or iss.get("id", ""))
                iss_title = iss.get("title") or f"Issue #{iss_num}"
                iss_entity, _ = await self.resolver.resolve_or_create_entity(
                    organization_id=organization_id,
                    workspace_id=workspace_id,
                    raw_name=f"{repo_name}#{iss_num}: {iss_title}",
                    entity_type=EntityType.ISSUE.value,
                    description=iss.get("body") or iss_title,
                    source_type=SourceType.ISSUE.value,
                    source_id=f"{repo_name}#{iss_num}",
                    project_id=project_id,
                )
                created_entities += 1
                issue_entity_map[iss_num] = iss_entity

                # issue -> belongs_to -> repository
                existing_rel = await self.repo.get_relationship(
                    workspace_id=workspace_id,
                    source_id=iss_entity.id,
                    relationship_type=RelationshipType.BELONGS_TO.value,
                    target_id=repo_entity.id,
                )
                if not existing_rel:
                    await rel_service.create_relationship(
                        organization_id=organization_id,
                        workspace_id=workspace_id,
                        request=RelationshipCreateRequest(
                            source_entity_id=iss_entity.id,
                            relationship_type=RelationshipType.BELONGS_TO.value,
                            target_entity_id=repo_entity.id,
                            source_reference={"repo": repo_name, "issue_number": iss_num},
                            project_id=project_id,
                        ),
                    )
                    created_rels += 1

                # author: person -> created_by -> issue
                author = iss.get("author") or iss.get("user")
                if author:
                    author_name = author if isinstance(author, str) else author.get("login") or str(author)
                    person_entity, _ = await self.resolver.resolve_or_create_entity(
                        organization_id=organization_id,
                        workspace_id=workspace_id,
                        raw_name=author_name,
                        entity_type=EntityType.PERSON.value,
                        description=f"Contributor {author_name}",
                        source_type="connector",
                        source_id=author_name,
                        project_id=project_id,
                    )
                    created_entities += 1

                    p_rel = await self.repo.get_relationship(
                        workspace_id=workspace_id,
                        source_id=person_entity.id,
                        relationship_type=RelationshipType.CREATED_BY.value,
                        target_id=iss_entity.id,
                    )
                    if not p_rel:
                        await rel_service.create_relationship(
                            organization_id=organization_id,
                            workspace_id=workspace_id,
                            request=RelationshipCreateRequest(
                                source_entity_id=person_entity.id,
                                relationship_type=RelationshipType.CREATED_BY.value,
                                target_entity_id=iss_entity.id,
                                source_reference={"issue": iss_num},
                                project_id=project_id,
                            ),
                        )
                        created_rels += 1

        # 4. Pull Requests: pull_request -> belongs_to -> repository; pull_request -> references -> issue
        if pull_requests:
            for pr in pull_requests:
                pr_num = str(pr.get("number") or pr.get("id", ""))
                pr_title = pr.get("title") or f"PR #{pr_num}"
                pr_entity, _ = await self.resolver.resolve_or_create_entity(
                    organization_id=organization_id,
                    workspace_id=workspace_id,
                    raw_name=f"{repo_name} PR #{pr_num}: {pr_title}",
                    entity_type=EntityType.PULL_REQUEST.value,
                    description=pr.get("body") or pr_title,
                    source_type=SourceType.PULL_REQUEST.value,
                    source_id=f"{repo_name}#pr{pr_num}",
                    project_id=project_id,
                )
                created_entities += 1

                # pr -> belongs_to -> repository
                existing_pr_rel = await self.repo.get_relationship(
                    workspace_id=workspace_id,
                    source_id=pr_entity.id,
                    relationship_type=RelationshipType.BELONGS_TO.value,
                    target_id=repo_entity.id,
                )
                if not existing_pr_rel:
                    await rel_service.create_relationship(
                        organization_id=organization_id,
                        workspace_id=workspace_id,
                        request=RelationshipCreateRequest(
                            source_entity_id=pr_entity.id,
                            relationship_type=RelationshipType.BELONGS_TO.value,
                            target_entity_id=repo_entity.id,
                            source_reference={"repo": repo_name, "pr_number": pr_num},
                            project_id=project_id,
                        ),
                    )
                    created_rels += 1

                # pr -> references -> issue
                ref_issues = pr.get("referenced_issues") or []
                for ref_num in ref_issues:
                    ref_iss_entity = issue_entity_map.get(str(ref_num))
                    if ref_iss_entity:
                        ref_rel = await self.repo.get_relationship(
                            workspace_id=workspace_id,
                            source_id=pr_entity.id,
                            relationship_type=RelationshipType.REFERENCES.value,
                            target_id=ref_iss_entity.id,
                        )
                        if not ref_rel:
                            await rel_service.create_relationship(
                                organization_id=organization_id,
                                workspace_id=workspace_id,
                                request=RelationshipCreateRequest(
                                    source_entity_id=pr_entity.id,
                                    relationship_type=RelationshipType.REFERENCES.value,
                                    target_entity_id=ref_iss_entity.id,
                                    source_reference={"pr": pr_num, "issue": str(ref_num)},
                                    project_id=project_id,
                                ),
                            )
                            created_rels += 1

        return GraphExtractResponse(
            entities_created=created_entities,
            relationships_created=created_rels,
            message="GitHub connector metadata graph integration completed.",
        )

    async def extract_from_document_metadata(
        self,
        organization_id: uuid.UUID,
        workspace_id: uuid.UUID,
        document_id: uuid.UUID,
        document_title: str,
        mentioned_entities: Optional[List[Dict[str, Any]]] = None,
        referenced_concepts: Optional[List[str]] = None,
        project_id: Optional[uuid.UUID] = None,
    ) -> GraphExtractResponse:
        """
        Step 29 Requirement 36: Constructs graph entities and relationships from processed documents.
        Relationships:
          document -> mentions -> entity
          document -> references -> concept
        """
        from backend.app.services.knowledge_graph.relationship_service import RelationshipService
        from backend.app.services.knowledge_graph.schemas import RelationshipCreateRequest
        rel_service = RelationshipService(self.session)

        created_entities = 0
        created_rels = 0

        # 1. Document Entity
        doc_entity, _ = await self.resolver.resolve_or_create_entity(
            organization_id=organization_id,
            workspace_id=workspace_id,
            raw_name=document_title,
            entity_type=EntityType.DOCUMENT.value,
            description=f"Document: {document_title}",
            source_type=SourceType.DOCUMENT.value,
            source_id=str(document_id),
            project_id=project_id,
        )
        created_entities += 1

        # 2. Document mentions entities
        if mentioned_entities:
            for ent_info in mentioned_entities:
                e_name = ent_info.get("name") or ent_info.get("canonical_name")
                e_type = ent_info.get("type") or ent_info.get("entity_type") or EntityType.CONCEPT.value
                if not e_name:
                    continue
                target_ent, _ = await self.resolver.resolve_or_create_entity(
                    organization_id=organization_id,
                    workspace_id=workspace_id,
                    raw_name=e_name,
                    entity_type=e_type,
                    description=ent_info.get("description"),
                    source_type=SourceType.DOCUMENT.value,
                    source_id=str(document_id),
                    project_id=project_id,
                )
                created_entities += 1

                existing = await self.repo.get_relationship(
                    workspace_id=workspace_id,
                    source_id=doc_entity.id,
                    relationship_type=RelationshipType.MENTIONS.value,
                    target_id=target_ent.id,
                )
                if not existing:
                    await rel_service.create_relationship(
                        organization_id=organization_id,
                        workspace_id=workspace_id,
                        request=RelationshipCreateRequest(
                            source_entity_id=doc_entity.id,
                            relationship_type=RelationshipType.MENTIONS.value,
                            target_entity_id=target_ent.id,
                            source_reference={"document_id": str(document_id)},
                            project_id=project_id,
                        ),
                    )
                    created_rels += 1

        # 3. Document references concepts
        if referenced_concepts:
            for concept_name in referenced_concepts:
                c_entity, _ = await self.resolver.resolve_or_create_entity(
                    organization_id=organization_id,
                    workspace_id=workspace_id,
                    raw_name=concept_name,
                    entity_type=EntityType.CONCEPT.value,
                    description=f"Concept: {concept_name}",
                    source_type=SourceType.DOCUMENT.value,
                    source_id=str(document_id),
                    project_id=project_id,
                )
                created_entities += 1

                existing_c = await self.repo.get_relationship(
                    workspace_id=workspace_id,
                    source_id=doc_entity.id,
                    relationship_type=RelationshipType.REFERENCES.value,
                    target_id=c_entity.id,
                )
                if not existing_c:
                    await rel_service.create_relationship(
                        organization_id=organization_id,
                        workspace_id=workspace_id,
                        request=RelationshipCreateRequest(
                            source_entity_id=doc_entity.id,
                            relationship_type=RelationshipType.REFERENCES.value,
                            target_entity_id=c_entity.id,
                            source_reference={"document_id": str(document_id)},
                            project_id=project_id,
                        ),
                    )
                    created_rels += 1

        return GraphExtractResponse(
            entities_created=created_entities,
            relationships_created=created_rels,
            message="Document metadata graph integration completed.",
        )
