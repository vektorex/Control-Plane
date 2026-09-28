import re
from typing import Any, Dict, List, Optional
from backend.app.services.chunking.models import RawChunk
from backend.app.services.context.token_estimator import estimate_tokens
from backend.app.services.extraction.base import ExtractedDocument


class DocumentChunker:
    """
    Configurable, structure-aware text chunking service.
    Splits document text along semantic boundaries (paragraphs, lines, sentences)
    while preserving page metadata and chunk order.
    """

    def __init__(
        self,
        chunk_size: int = 500,  # approximate token size
        chunk_overlap: int = 50,  # approximate token overlap
    ) -> None:
        self.chunk_size = max(chunk_size, 50)
        self.chunk_overlap = max(min(chunk_overlap, self.chunk_size // 2), 0)
        # Approximate 4 characters per token
        self.target_char_len = self.chunk_size * 4
        self.overlap_char_len = self.chunk_overlap * 4

    def _split_text_with_overlap(self, text: str) -> List[str]:
        """
        Splits a continuous text block into overlapping chunks respecting structural delimiters.
        """
        if not text or not text.strip():
            return []

        text = text.strip()
        if len(text) <= self.target_char_len:
            return [text]

        # Break text into structural paragraphs / segments
        paragraphs = re.split(r"(\n\n+|\r\n\r\n+)", text)
        segments: List[str] = []
        for p in paragraphs:
            if not p:
                continue
            if len(p) > self.target_char_len:
                # If paragraph itself is oversized, split on sentences / linebreaks
                sub_parts = re.split(r"((?<=[.?!])\s+|\n)", p)
                segments.extend([s for s in sub_parts if s and s.strip()])
            else:
                segments.append(p)

        chunks: List[str] = []
        current_chunk: List[str] = []
        current_len = 0

        for segment in segments:
            seg_len = len(segment)

            if current_len + seg_len > self.target_char_len and current_chunk:
                chunk_str = "".join(current_chunk).strip()
                if chunk_str:
                    chunks.append(chunk_str)

                # Overlap retention: keep tail segments that fit into overlap buffer
                overlap_accum: List[str] = []
                overlap_len = 0
                for s in reversed(current_chunk):
                    if overlap_len + len(s) <= self.overlap_char_len:
                        overlap_accum.insert(0, s)
                        overlap_len += len(s)
                    else:
                        break

                current_chunk = overlap_accum
                current_len = overlap_len

            current_chunk.append(segment)
            current_len += seg_len

        if current_chunk:
            final_str = "".join(current_chunk).strip()
            if final_str and (not chunks or final_str != chunks[-1]):
                chunks.append(final_str)

        return chunks

    def chunk_document(self, doc: ExtractedDocument) -> List[RawChunk]:
        """
        Chunks an ExtractedDocument object preserving page numbers where available.
        """
        raw_chunks: List[RawChunk] = []
        global_index = 0

        # If document has discrete pages (e.g. PDF)
        if doc.pages and len(doc.pages) > 1:
            for page in doc.pages:
                if not page.text or not page.text.strip():
                    continue

                page_text_chunks = self._split_text_with_overlap(page.text)
                for chunk_text in page_text_chunks:
                    tokens = estimate_tokens(chunk_text)
                    raw_chunks.append(
                        RawChunk(
                            chunk_index=global_index,
                            content=chunk_text,
                            token_count=tokens,
                            page_number=page.page_number,
                            metadata={
                                "filename": doc.filename,
                                "mime_type": doc.mime_type,
                                "page_number": page.page_number,
                                "char_count": len(chunk_text),
                                **doc.metadata,
                            },
                        )
                    )
                    global_index += 1
        else:
            # Single continuous text block (TXT, Markdown, DOCX)
            text_to_chunk = doc.text or (doc.pages[0].text if doc.pages else "")
            text_chunks = self._split_text_with_overlap(text_to_chunk)

            for chunk_text in text_chunks:
                tokens = estimate_tokens(chunk_text)
                raw_chunks.append(
                    RawChunk(
                        chunk_index=global_index,
                        content=chunk_text,
                        token_count=tokens,
                        page_number=1,
                        metadata={
                            "filename": doc.filename,
                            "mime_type": doc.mime_type,
                            "char_count": len(chunk_text),
                            **doc.metadata,
                        },
                    )
                )
                global_index += 1

        return raw_chunks
