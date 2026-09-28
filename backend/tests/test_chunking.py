from backend.app.services.chunking.chunker import DocumentChunker
from backend.app.services.extraction.base import ExtractedDocument, ExtractedPage


def test_chunking_single_document():
    chunker = DocumentChunker(chunk_size=100, chunk_overlap=20)
    # Long text with paragraphs
    paragraphs = [f"Paragraph {i}: " + ("This is detailed contextual knowledge for RAG retrieval. " * 5) for i in range(10)]
    full_text = "\n\n".join(paragraphs)

    doc = ExtractedDocument(
        filename="test.txt",
        mime_type="text/plain",
        text=full_text,
        char_count=len(full_text),
    )

    chunks = chunker.chunk_document(doc)
    assert len(chunks) > 1

    # Verify chunk structure
    for i, c in enumerate(chunks):
        assert c.chunk_index == i
        assert len(c.content) > 0
        assert c.token_count > 0
        assert c.metadata["filename"] == "test.txt"
        assert c.page_number == 1


def test_chunking_multi_page_document():
    chunker = DocumentChunker(chunk_size=50, chunk_overlap=10)
    pages = [
        ExtractedPage(page_number=1, text="Page 1: Introduction to Work Orchestration Layer."),
        ExtractedPage(page_number=2, text="Page 2: Vector embeddings and keyword search fusion mechanics."),
        ExtractedPage(page_number=3, text="Page 3: Conclusion and verification procedures."),
    ]
    doc = ExtractedDocument(
        filename="multipage.pdf",
        mime_type="application/pdf",
        text="All pages combined",
        pages=pages,
    )

    chunks = chunker.chunk_document(doc)
    assert len(chunks) == 3
    assert chunks[0].page_number == 1
    assert "Page 1" in chunks[0].content
    assert chunks[1].page_number == 2
    assert "Page 2" in chunks[1].content
    assert chunks[2].page_number == 3
    assert "Page 3" in chunks[2].content


def test_chunking_empty_document():
    chunker = DocumentChunker()
    doc = ExtractedDocument(
        filename="empty.txt",
        mime_type="text/plain",
        text="",
        pages=[],
    )
    chunks = chunker.chunk_document(doc)
    assert len(chunks) == 0
