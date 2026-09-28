import pytest
import io
from pypdf import PdfWriter
import docx

from backend.app.core.errors import UnsupportedMediaTypeError
from backend.app.services.extraction.extractors.docx import DOCXExtractor
from backend.app.services.extraction.extractors.markdown import MarkdownExtractor
from backend.app.services.extraction.extractors.pdf import PDFExtractor
from backend.app.services.extraction.extractors.text import TextExtractor
from backend.app.services.extraction.factory import ExtractorFactory, get_extractor_factory


def test_text_extractor():
    extractor = TextExtractor()
    assert extractor.can_handle("text/plain", "sample.txt")
    assert not extractor.can_handle("application/pdf", "sample.pdf")

    sample_text = "Hello world!\nThis is a plain text file for RAG ingestion."
    data = sample_text.encode("utf-8")
    doc = extractor.extract(data, "sample.txt", "text/plain")

    assert doc.filename == "sample.txt"
    assert doc.mime_type == "text/plain"
    assert "Hello world!" in doc.text
    assert doc.char_count == len(sample_text)
    assert len(doc.pages) == 1
    assert doc.pages[0].page_number == 1


def test_markdown_extractor():
    extractor = MarkdownExtractor()
    assert extractor.can_handle("text/markdown", "guide.md")
    assert extractor.can_handle("text/x-markdown", "readme.markdown")

    md_content = "# System Architecture\n\n## Subsystem A\nThis handles hybrid retrieval.\n\n- Vector search\n- Keyword search"
    data = md_content.encode("utf-8")
    doc = extractor.extract(data, "guide.md", "text/markdown")

    assert doc.filename == "guide.md"
    assert "System Architecture" in doc.text
    assert "hybrid retrieval" in doc.text
    assert doc.metadata.get("headings_count") == 2
    assert len(doc.pages) == 1


def test_pdf_extractor():
    extractor = PDFExtractor()
    assert extractor.can_handle("application/pdf", "report.pdf")

    # Generate a valid binary PDF with pypdf
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    pdf_buf = io.BytesIO()
    writer.write(pdf_buf)
    pdf_bytes = pdf_buf.getvalue()

    doc = extractor.extract(pdf_bytes, "report.pdf", "application/pdf")
    assert doc.filename == "report.pdf"
    assert doc.mime_type == "application/pdf"
    assert len(doc.pages) == 1
    assert doc.pages[0].page_number == 1


def test_docx_extractor():
    extractor = DOCXExtractor()
    assert extractor.can_handle("application/vnd.openxmlformats-officedocument.wordprocessingml.document", "doc.docx")

    # Generate a valid binary DOCX with python-docx
    doc_file = docx.Document()
    doc_file.add_heading("AI Work Layer Overview", level=1)
    doc_file.add_paragraph("This document outlines the Context Engine and Hybrid RAG architecture.")
    docx_buf = io.BytesIO()
    doc_file.save(docx_buf)
    docx_bytes = docx_buf.getvalue()

    extracted = extractor.extract(docx_bytes, "doc.docx")
    assert extracted.filename == "doc.docx"
    assert "AI Work Layer Overview" in extracted.text
    assert "Hybrid RAG architecture" in extracted.text
    assert len(extracted.pages) == 1


def test_extractor_factory():
    factory = get_extractor_factory()

    txt_ext = factory.get_extractor("text/plain", "file.txt")
    assert isinstance(txt_ext, TextExtractor)

    md_ext = factory.get_extractor("text/markdown", "notes.md")
    assert isinstance(md_ext, MarkdownExtractor)

    pdf_ext = factory.get_extractor("application/pdf", "manual.pdf")
    assert isinstance(pdf_ext, PDFExtractor)

    docx_ext = factory.get_extractor("application/vnd.openxmlformats-officedocument.wordprocessingml.document", "spec.docx")
    assert isinstance(docx_ext, DOCXExtractor)

    with pytest.raises(UnsupportedMediaTypeError):
        factory.get_extractor("application/x-executable", "binary.exe")
