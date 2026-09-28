from typing import Optional
from uuid import UUID
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.logging import logger
from backend.app.db.models.document import Document
from backend.app.db.models.document_chunk import DocumentChunk
from backend.app.services.chunking.chunker import DocumentChunker
from backend.app.services.embeddings.base import BaseEmbeddingProvider
from backend.app.services.embeddings.factory import get_embedding_provider
from backend.app.services.extraction.factory import ExtractorFactory, get_extractor_factory
from backend.app.services.storage.base import FileStorage
from backend.app.services.storage.factory import get_file_storage


class DocumentIngestionPipeline:
    """
    Orchestrates the asynchronous document ingestion pipeline:
    Storage Download -> Text Extraction -> Normalization -> Chunking -> Batch Embedding -> Indexing & Persistence.
    """

    def __init__(
        self,
        storage: Optional[FileStorage] = None,
        extractor_factory: Optional[ExtractorFactory] = None,
        chunker: Optional[DocumentChunker] = None,
        embedding_provider: Optional[BaseEmbeddingProvider] = None,
    ) -> None:
        self.storage = storage or get_file_storage()
        self.extractor_factory = extractor_factory or get_extractor_factory()
        self.chunker = chunker or DocumentChunker()
        self.embedding_provider = embedding_provider or get_embedding_provider()

    async def process_document(self, document_id: UUID, session: AsyncSession) -> Document:
        """
        Executes end-to-end ingestion processing for a single document.
        """
        # 1. Fetch document
        stmt = select(Document).where(Document.id == document_id)
        res = await session.execute(stmt)
        document = res.scalar_one_or_none()

        if not document:
            logger.error(f"[IngestionPipeline] Document {document_id} not found.")
            raise ValueError(f"Document {document_id} not found.")

        try:
            logger.info(f"[IngestionPipeline] Starting ingestion for document '{document.filename}' ({document_id})")
            document.status = "processing"
            document.error_message = None
            await session.commit()
            await session.refresh(document)

            # 2. Download raw file from storage
            file_bytes = await self.storage.download(document.storage_key)

            # 3. Extract text
            extractor = self.extractor_factory.get_extractor(
                mime_type=document.mime_type,
                filename=document.filename,
            )
            extracted_doc = extractor.extract(
                data=file_bytes,
                filename=document.filename,
                mime_type=document.mime_type,
            )

            # 4. Chunk document
            raw_chunks = self.chunker.chunk_document(extracted_doc)

            # Clean existing chunks if reprocessing
            await session.execute(
                delete(DocumentChunk).where(DocumentChunk.document_id == document.id)
            )

            if not raw_chunks:
                logger.warning(f"[IngestionPipeline] Document {document_id} yielded no extractable text chunks.")
                document.status = "ready"
                document.chunk_count = 0
                await session.commit()
                await session.refresh(document)
                return document

            # 5. Batch Embed Chunks
            chunk_texts = [c.content for c in raw_chunks]
            embeddings = await self.embedding_provider.embed_batch(chunk_texts)

            # 6. Index & Persist DocumentChunk records
            chunk_records = []
            for i, raw in enumerate(raw_chunks):
                emb = embeddings[i] if i < len(embeddings) else None
                chunk_records.append(
                    DocumentChunk(
                        document_id=document.id,
                        workspace_id=document.workspace_id,
                        project_id=document.project_id,
                        chunk_index=raw.chunk_index,
                        content=raw.content,
                        token_count=raw.token_count,
                        embedding=emb,
                        page_number=raw.page_number,
                        metadata_json=raw.metadata,
                    )
                )

            session.add_all(chunk_records)

            # 7. Mark Document Ready
            document.status = "ready"
            document.chunk_count = len(chunk_records)
            document.error_message = None

            await session.commit()
            await session.refresh(document)
            logger.info(
                f"[IngestionPipeline] Successfully ingested '{document.filename}' ({document_id}): "
                f"{len(chunk_records)} chunks indexed."
            )
            return document

        except Exception as e:
            logger.error(f"[IngestionPipeline] Failed ingesting document {document_id}: {str(e)}", exc_info=True)
            await session.rollback()

            # Mark as failed in separate transaction
            try:
                document.status = "failed"
                document.error_message = str(e)
                session.add(document)
                await session.commit()
            except Exception as commit_err:
                logger.error(f"[IngestionPipeline] Could not update failed status for document {document_id}: {commit_err}")

            raise


_global_pipeline: Optional[DocumentIngestionPipeline] = None


def get_ingestion_pipeline() -> DocumentIngestionPipeline:
    """Dependency injector / factory function for DocumentIngestionPipeline."""
    global _global_pipeline
    if _global_pipeline is None:
        _global_pipeline = DocumentIngestionPipeline()
    return _global_pipeline
