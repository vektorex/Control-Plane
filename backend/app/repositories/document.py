from typing import List, Optional, Tuple
from uuid import UUID
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.errors import DatabaseError, NotFoundError
from backend.app.db.models.document import Document
from backend.app.db.models.document_chunk import DocumentChunk
from backend.app.db.models.workspace import Workspace


class DocumentRepository:
    """
    Repository handling multi-tenant CRUD persistence logic for Documents and DocumentChunks.
    Strictly guarantees that all operations are scoped to workspaces owned by the authenticated user.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id_and_owner(self, document_id: UUID, owner_user_id: UUID) -> Optional[Document]:
        """
        Retrieves a document by ID only if it belongs to a workspace owned by owner_user_id.
        """
        stmt = (
            select(Document)
            .join(Workspace, Document.workspace_id == Workspace.id)
            .where(
                Document.id == document_id,
                Workspace.owner_user_id == owner_user_id,
            )
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def get_by_id_and_owner_or_raise(self, document_id: UUID, owner_user_id: UUID) -> Document:
        doc = await self.get_by_id_and_owner(document_id, owner_user_id)
        if not doc:
            raise NotFoundError(f"Document with id '{document_id}' not found or access denied.")
        return doc

    async def list_by_workspace_and_owner(
        self,
        workspace_id: UUID,
        owner_user_id: UUID,
        project_id: Optional[UUID] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[Document], int]:
        """
        Lists documents within a workspace owned by owner_user_id, with optional project and status filters.
        """
        base_where = [
            Document.workspace_id == workspace_id,
            Workspace.owner_user_id == owner_user_id,
        ]
        if project_id is not None:
            base_where.append(Document.project_id == project_id)
        if status is not None:
            base_where.append(Document.status == status)

        # Count total
        count_stmt = (
            select(func.count(Document.id))
            .join(Workspace, Document.workspace_id == Workspace.id)
            .where(*base_where)
        )
        count_res = await self.session.execute(count_stmt)
        total = count_res.scalar_one() or 0

        # Fetch items
        stmt = (
            select(Document)
            .join(Workspace, Document.workspace_id == Workspace.id)
            .where(*base_where)
            .order_by(Document.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        res = await self.session.execute(stmt)
        documents = list(res.scalars().all())
        return documents, total

    async def list_chunks_by_document(
        self,
        document_id: UUID,
        owner_user_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[DocumentChunk], int]:
        """
        Lists chunks for a document, verifying multi-tenant ownership.
        """
        # First verify document ownership
        await self.get_by_id_and_owner_or_raise(document_id, owner_user_id)

        count_stmt = select(func.count(DocumentChunk.id)).where(DocumentChunk.document_id == document_id)
        count_res = await self.session.execute(count_stmt)
        total = count_res.scalar_one() or 0

        stmt = (
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.chunk_index.asc())
            .offset(skip)
            .limit(limit)
        )
        res = await self.session.execute(stmt)
        chunks = list(res.scalars().all())
        return chunks, total

    async def create(self, document: Document) -> Document:
        """Persists a new document record."""
        self.session.add(document)
        try:
            await self.session.flush()
            await self.session.refresh(document)
            return document
        except Exception as e:
            await self.session.rollback()
            raise DatabaseError("Failed to persist document.", details=str(e))

    async def delete(self, document_id: UUID, owner_user_id: UUID) -> Optional[Document]:
        """
        Deletes a document and all associated chunks if owned by owner_user_id.
        Returns the deleted Document model (containing storage_key for file cleanup).
        """
        document = await self.get_by_id_and_owner_or_raise(document_id, owner_user_id)

        # Delete chunks first (or let DB cascade delete)
        await self.session.execute(
            delete(DocumentChunk).where(DocumentChunk.document_id == document_id)
        )
        await self.session.delete(document)
        try:
            await self.session.flush()
            return document
        except Exception as e:
            await self.session.rollback()
            raise DatabaseError(f"Failed to delete document '{document_id}'.", details=str(e))
