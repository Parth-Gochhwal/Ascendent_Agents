"""Comprehensive unit tests for Open-Access Full-Text Retrieval and Extraction."""
import io
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

from backend.app.models.research import Paper, PaperContentStatus
from backend.app.services.full_text import (
    FullTextRetriever, is_valid_pdf_url, resolve_candidate_pdf_url
)


def create_minimal_pdf(text: str = "Abstract\nThis is a test paper.\n\nMethods\nWe used standard deep learning models.\n\nResults\nThe proposed method achieves 95% accuracy.\n\nLimitations\nThe sample size is limited.\n\nConclusion\nIn conclusion, our method works.") -> bytes:
    """Create a minimal valid PDF byte sequence using PyMuPDF."""
    import pymupdf as fitz
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 72), text)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def test_is_valid_pdf_url():
    """Verify safe and valid PDF URL checking."""
    assert is_valid_pdf_url("https://arxiv.org/pdf/2301.00001.pdf") is True
    assert is_valid_pdf_url("http://example.com/paper.pdf") is True
    assert is_valid_pdf_url("https://openaccess.thecvf.com/content/paper.pdf") is True
    
    # Reject invalid / dangerous URLs
    assert is_valid_pdf_url("file:///etc/passwd") is False
    assert is_valid_pdf_url("ftp://example.com/paper.pdf") is False
    assert is_valid_pdf_url("http://localhost/secret.pdf") is False
    assert is_valid_pdf_url("http://127.0.0.1:8000/test.pdf") is False
    assert is_valid_pdf_url("http://10.0.0.1/doc.pdf") is False
    assert is_valid_pdf_url("http://192.168.1.1/doc.pdf") is False
    assert is_valid_pdf_url("") is False
    assert is_valid_pdf_url(None) is False
    assert is_valid_pdf_url("not-a-url") is False


def test_resolve_candidate_pdf_url():
    """Verify OA URL resolution for different provider metadata formats."""
    # Direct PDF URL
    p1 = Paper(id="p1", title="Paper 1", pdf_url="https://arxiv.org/pdf/2401.00001.pdf")
    assert resolve_candidate_pdf_url(p1) == "https://arxiv.org/pdf/2401.00001.pdf"

    # arXiv ID derivation
    p2 = Paper(id="p2", title="Paper 2", source_ids={"arxiv": "2402.12345v1"})
    assert resolve_candidate_pdf_url(p2) == "https://arxiv.org/pdf/2402.12345.pdf"

    # arXiv URL in paper.url
    p3 = Paper(id="p3", title="Paper 3", url="https://arxiv.org/abs/2403.54321")
    assert resolve_candidate_pdf_url(p3) == "https://arxiv.org/pdf/2403.54321.pdf"

    # Direct PDF in URL
    p4 = Paper(id="p4", title="Paper 4", url="https://example.org/downloads/paper.pdf")
    assert resolve_candidate_pdf_url(p4) == "https://example.org/downloads/paper.pdf"

    # Non-OA paper
    p5 = Paper(id="p5", title="Paper 5", url="https://doi.org/10.1000/182")
    assert resolve_candidate_pdf_url(p5) is None


def test_pdf_extraction_and_section_detection():
    """Test text and section extraction on real generated PDF bytes."""
    retriever = FullTextRetriever()
    pdf_bytes = create_minimal_pdf()
    assert pdf_bytes.startswith(b"%PDF-")

    text, sections, page_count, err = retriever.extract_text_and_sections(pdf_bytes)
    assert err is None
    assert page_count == 1
    assert "Abstract" in text or "test paper" in text
    assert len(sections) > 0
    assert "methods" in sections or "results" in sections or "abstract" in sections or "conclusion" in sections


def test_invalid_pdf_bytes_rejected():
    """Verify non-PDF files (e.g. HTML 403 splash page) are rejected."""
    retriever = FullTextRetriever()
    html_bytes = b"<html><body>Access Denied - Paywall Required</body></html>"
    text, sections, page_count, err = retriever.extract_text_and_sections(html_bytes)
    assert err is not None or text == ""


@pytest.mark.anyio
async def test_enrich_paper_success(tmp_path):
    """Test paper enrichment when OA PDF download succeeds."""
    retriever = FullTextRetriever(cache_dir=tmp_path)
    pdf_bytes = create_minimal_pdf()

    paper = Paper(
        id="p1",
        title="GATs for Battery RUL",
        pdf_url="https://arxiv.org/pdf/2401.00001.pdf",
        abstract="Short abstract."
    )

    with patch.object(retriever, "fetch_pdf_bytes", AsyncMock(return_value=(pdf_bytes, None))):
        enriched = await retriever.enrich_paper(paper)
        assert enriched.full_text_available is True
        assert enriched.content_status in (PaperContentStatus.FULL_TEXT, PaperContentStatus.FULL_TEXT_PARTIAL)
        assert enriched.page_count == 1
        assert enriched.text_length > 0
        assert "full_text" in enriched.sections


@pytest.mark.anyio
async def test_enrich_paper_download_failure_falls_back(tmp_path):
    """Test that download failure gracefully marks FULL_TEXT_FAILED without crashing."""
    retriever = FullTextRetriever(cache_dir=tmp_path)

    paper = Paper(
        id="p2",
        title="Paywalled Nature Paper",
        pdf_url="https://publisher.com/locked.pdf",
        abstract="Abstract of locked paper."
    )

    with patch.object(retriever, "fetch_pdf_bytes", AsyncMock(return_value=(None, "HTTP 403 Forbidden"))):
        enriched = await retriever.enrich_paper(paper)
        assert enriched.full_text_available is False
        assert enriched.content_status == PaperContentStatus.FULL_TEXT_FAILED
        assert "403" in (enriched.retrieval_failure_reason or "")


@pytest.mark.anyio
async def test_enrich_paper_abstract_only_when_no_pdf_url(tmp_path):
    """Test paper without PDF URL is marked ABSTRACT_ONLY."""
    retriever = FullTextRetriever(cache_dir=tmp_path)

    paper = Paper(
        id="p3",
        title="Conference Abstract Only",
        abstract="Only the abstract was published."
    )

    enriched = await retriever.enrich_paper(paper)
    assert enriched.full_text_available is False
    assert enriched.content_status == PaperContentStatus.ABSTRACT_ONLY
    assert "No open-access" in (enriched.retrieval_failure_reason or "")
