import hashlib
import os
import re
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import settings
from backend.app.core.auth import get_current_user
from backend.app.core.errors import BadRequestError, UnsupportedMediaTypeError
from backend.app.core.logging import logger
from backend.app.db.database import AsyncSessionLocal, get_db
from backend.app.db.models.document import Document
from backend.app.db.models.user import User
from backend.app.repositories.document import DocumentRepository
from backend.app.repositories.project import ProjectRepository
from backend.app.repositories.workspace import WorkspaceRepository
from backend.app.schemas.document import (
    DocumentChunkListResponse,
    DocumentChunkResponse,
    DocumentListResponse,
    DocumentResponse,
)
from backend.app.services.ingestion.pipeline import get_ingestion_pipeline
from backend.app.services.storage.factory import get_file_storage

router = APIRouter(tags=["Documents"])

ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md", ".markdown", ".docx"}
ALLOWED_MIME_PREFIXES = {
    "application/pdf",
    "text/plain",
    "text/markdown",
    "text/x-markdown",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/octet-stream",  # Sometimes reported by browsers for md/txt
}


def _sanitize_filename(filename: str) -> str:
    """Strips path components and unsafe characters from uploaded filename."""
    base = os.path.basename(filename).strip()
    clean = re.sub(r"[^\w\.\-\_]", "_", base)
    return clean or "document"


async def _process_document_in_background(document_id: UUID) -> None:
    """
    Background worker task executing text extraction, chunking, and embedding
    without holding open the client's HTTP upload connection.
    """
    pipeline = get_ingestion_pipeline()
    async with AsyncSessionLocal() as session:
        try:
            await pipeline.process_document(document_id, session)
        except Exception as e:
            logger.error(f"[BackgroundIngestion] Failed for document {document_id}: {str(e)}", exc_info=True)


# --- Workspace-scoped Document Endpoints ---

@router.post(
    "/workspaces/{workspace_id}/documents",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    workspace_id: UUID,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    project_id: Optional[UUID] = Form(None),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> DocumentResponse:
    """
    Upload a document (PDF, TXT, Markdown, DOCX) to a workspace owned by the authenticated user.
    Validates ownership, file size, format, and launches non-blocking background ingestion.
    """
    # 1. Verify workspace ownership
    ws_repo = WorkspaceRepository(session)
    await ws_repo.get_by_id_and_owner_or_raise(workspace_id, user.id)

    # 2. Verify project ownership if project_id is provided
    if project_id:
        proj_repo = ProjectRepository(session)
        proj = await proj_repo.get_by_id_and_owner_or_raise(project_id, user.id)
        if proj.workspace_id != workspace_id:
            raise BadRequestError(f"Project '{project_id}' does not belong to workspace '{workspace_id}'.")

    # 3. Validate filename and extension
    raw_filename = file.filename or "uploaded_file"
    safe_filename = _sanitize_filename(raw_filename)
    _, ext = os.path.splitext(safe_filename.lower())

    if ext not in ALLOWED_EXTENSIONS:
        raise UnsupportedMediaTypeError(
            f"Unsupported file extension '{ext}'. Allowed formats: PDF (.pdf), Plain Text (.txt), Markdown (.md), Word (.docx)."
        )

    # 4. Read content & validate file size
    max_bytes = settings.MAX_DOCUMENT_SIZE_MB * 1024 * 1024
    content = await file.read()
    file_size = len(content)

    if file_size == 0:
        raise BadRequestError("Uploaded file is empty (0 bytes).")

    if file_size > max_bytes:
        raise BadRequestError(
            f"File size ({file_size / (1024 * 1024):.1f}MB) exceeds max permitted size of {settings.MAX_DOCUMENT_SIZE_MB}MB."
        )

    # 5. Compute checksum and resolve MIME type
    checksum = hashlib.sha256(content).hexdigest()
    mime_type = file.content_type or "application/octet-stream"

    # 6. Upload to file storage abstraction
    storage = get_file_storage()
    storage_key = f"workspaces/{workspace_id}/docs/{checksum[:12]}_{safe_filename}"
    await storage.upload(storage_key, content, content_type=mime_type)

    # 7. Persist Document record
    doc_repo = DocumentRepository(session)
    doc = Document(
        workspace_id=workspace_id,
        project_id=project_id,
        filename=safe_filename,
        original_filename=raw_filename,
        mime_type=mime_type,
        file_size=file_size,
        storage_key=storage_key,
        checksum=checksum,
        status="pending",
        chunk_count=0,
        metadata_json={
            "extension": ext,
            "uploaded_by_user_id": str(user.id),
        },
    )
    doc = await doc_repo.create(doc)
    await session.commit()
    await session.refresh(doc)

    # 8. Dispatch non-blocking background ingestion
    background_tasks.add_task(_process_document_in_background, doc.id)

    return DocumentResponse.model_validate(doc)


@router.get("/workspaces/{workspace_id}/documents", response_model=DocumentListResponse)
async def list_workspace_documents(
    workspace_id: UUID,
    project_id: Optional[UUID] = Query(None, description="Filter documents by project"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status (pending, processing, ready, failed)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> DocumentListResponse:
    """
    List documents in a workspace owned by the current authenticated user.
    """
    ws_repo = WorkspaceRepository(session)
    await ws_repo.get_by_id_and_owner_or_raise(workspace_id, user.id)

    doc_repo = DocumentRepository(session)
    docs, total = await doc_repo.list_by_workspace_and_owner(
        workspace_id=workspace_id,
        owner_user_id=user.id,
        project_id=project_id,
        status=status_filter,
        skip=skip,
        limit=limit,
    )

    return DocumentListResponse(
        items=[DocumentResponse.model_validate(d) for d in docs],
        total=total,
    )


# --- Single Document Endpoints ---

@router.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> DocumentResponse:
    """
    Retrieve document status, metadata, and chunk count for an owned document.
    """
    doc_repo = DocumentRepository(session)
    doc = await doc_repo.get_by_id_and_owner_or_raise(document_id, user.id)
    return DocumentResponse.model_validate(doc)


@router.get("/documents/{document_id}/chunks", response_model=DocumentChunkListResponse)
async def get_document_chunks(
    document_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> DocumentChunkListResponse:
    """
    List indexed chunks for an owned document (useful for RAG transparency and inspection).
    """
    doc_repo = DocumentRepository(session)
    chunks, total = await doc_repo.list_chunks_by_document(
        document_id=document_id,
        owner_user_id=user.id,
        skip=skip,
        limit=limit,
    )
    return DocumentChunkListResponse(
        items=[DocumentChunkResponse.model_validate(c) for c in chunks],
        total=total,
    )


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """
    Delete an owned document, all of its vector chunks, and its stored file.
    """
    doc_repo = DocumentRepository(session)
    deleted_doc = await doc_repo.delete(document_id, user.id)
    await session.commit()

    if deleted_doc and deleted_doc.storage_key:
        storage = get_file_storage()
        try:
            await storage.delete(deleted_doc.storage_key)
        except Exception as e:
            logger.warning(f"[DocumentDelete] Could not delete stored file '{deleted_doc.storage_key}': {e}")

    return None


@router.post("/documents/{document_id}/reprocess", response_model=DocumentResponse)
async def reprocess_document(
    document_id: UUID,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> DocumentResponse:
    """
    Trigger manual re-ingestion / chunking / embedding for an existing owned document.
    """
    doc_repo = DocumentRepository(session)
    doc = await doc_repo.get_by_id_and_owner_or_raise(document_id, user.id)

    doc.status = "pending"
    doc.error_message = None
    await session.commit()
    await session.refresh(doc)

    background_tasks.add_task(_process_document_in_background, doc.id)
    return DocumentResponse.model_validate(doc)
