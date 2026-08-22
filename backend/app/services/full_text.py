"""Open-Access Full-Text Retrieval and PDF Extraction Service for NEXUS.

Retrieves legitimately available open-access PDFs (arXiv, OpenAlex, Semantic Scholar,
and unpaywall endpoints), validates integrity, extracts text with PyMuPDF, detects
scholarly sections, and maintains disk cache.
"""
import asyncio
import hashlib
import io
import logging
import os
import re
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import httpx

from backend.app.core.config import get_settings
from backend.app.models.research import Paper, PaperContentStatus

logger = logging.getLogger(__name__)

# Standard academic section headings patterns
SECTION_PATTERNS = {
    "abstract": re.compile(r'^(?:abstract|summary)\b', re.IGNORECASE),
    "introduction": re.compile(r'^(?:1\.?\s*)?introduction\b', re.IGNORECASE),
    "background": re.compile(r'^(?:2\.?\s*)?(?:background|related\s+work|literature\s+review)\b', re.IGNORECASE),
    "methods": re.compile(r'^(?:\d\.?\s*)?(?:methods?|methodology|proposed\s+method|model\s+architecture|system\s+design|materials?\s+and\s+methods?)\b', re.IGNORECASE),
    "experimental_setup": re.compile(r'^(?:\d\.?\s*)?(?:experimental\s+setup|experiments?|experimental\s+design|implementation\s+details|evaluation\s+setup)\b', re.IGNORECASE),
    "results": re.compile(r'^(?:\d\.?\s*)?(?:results?|findings|experimental\s+results?|performance\s+evaluation)\b', re.IGNORECASE),
    "discussion": re.compile(r'^(?:\d\.?\s*)?discussion\b', re.IGNORECASE),
    "limitations": re.compile(r'^(?:\d\.?\s*)?(?:limitations?|threats\s+to\s+validity|potential\s+risks?)\b', re.IGNORECASE),
    "conclusion": re.compile(r'^(?:\d\.?\s*)?(?:conclusions?|concluding\s+remarks?|summary\s+and\s+conclusions?)\b', re.IGNORECASE),
    "future_work": re.compile(r'^(?:\d\.?\s*)?(?:future\s+work|future\s+directions?|open\s+challenges?)\b', re.IGNORECASE),
    "references": re.compile(r'^(?:references?|bibliography)\b', re.IGNORECASE),
}

# Max allowed download size (25MB)
MAX_PDF_SIZE_BYTES = 25 * 1024 * 1024


def is_valid_pdf_url(url: Optional[str]) -> bool:
    """Validate that a URL is a valid, safe HTTP/HTTPS URL for academic PDF fetching."""
    if not url or not isinstance(url, str):
        return False
    url = url.strip()
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False
        if not parsed.netloc or "." not in parsed.netloc:
            return False
        # Block localhost / private IP ranges
        hostname = parsed.hostname or ""
        if hostname in ("localhost", "127.0.0.1", "::1", "0.0.0.0"):
            return False
        if hostname.startswith("10.") or hostname.startswith("192.168.") or (hostname.startswith("172.") and 16 <= int(hostname.split(".")[1] or 0) <= 31):
            return False
        return True
    except Exception:
        return False


def resolve_candidate_pdf_url(paper: Paper) -> Optional[str]:
    """Derive the best legitimate Open-Access PDF URL for a paper."""
    # 1. Direct pdf_url on paper
    if paper.pdf_url and is_valid_pdf_url(paper.pdf_url):
        return paper.pdf_url.strip()

    # 2. arXiv ID derivation
    arxiv_id = paper.source_ids.get("arxiv")
    if not arxiv_id and paper.url and "arxiv.org/abs/" in paper.url:
        arxiv_id = paper.url.split("arxiv.org/abs/")[-1].strip()
    if arxiv_id:
        clean_id = re.sub(r'v\d+$', '', arxiv_id)
        return f"https://arxiv.org/pdf/{clean_id}.pdf"

    # 3. OpenAlex or Semantic Scholar open access URLs if available
    if paper.url and paper.url.lower().endswith(".pdf") and is_valid_pdf_url(paper.url):
        return paper.url.strip()

    return None


class FullTextRetriever:
    """Safely retrieves and extracts Open-Access academic paper contents."""

    def __init__(self, cache_dir: Optional[Path] = None, max_concurrent: int = 4):
        settings = get_settings()
        self.cache_dir = (cache_dir or settings.cache_dir) / "pdfs"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self._client: Optional[httpx.AsyncClient] = None

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=25.0,
                follow_redirects=True,
                headers={"User-Agent": "NEXUS-Academic-Scientist/1.0 (academic-research; mailto:nexus@research.local)"}
            )
        return self._client

    def _url_cache_path(self, url: str) -> Path:
        url_hash = hashlib.sha256(url.encode()).hexdigest()
        return self.cache_dir / f"{url_hash}.pdf"

    async def fetch_pdf_bytes(self, url: str) -> tuple[Optional[bytes], Optional[str]]:
        """Safely fetch PDF bytes with caching, timeout, magic-byte validation, and size checks."""
        if not is_valid_pdf_url(url):
            return None, "Invalid or prohibited URL format"

        cache_path = self._url_cache_path(url)
        if cache_path.exists():
            try:
                cached_bytes = cache_path.read_bytes()
                if cached_bytes.startswith(b"%PDF-"):
                    return cached_bytes, None
            except Exception as e:
                logger.warning(f"Error reading PDF cache for {url}: {e}")

        client = self._get_client()
        try:
            async with self.semaphore:
                async with client.stream("GET", url) as response:
                    if response.status_code != 200:
                        return None, f"HTTP {response.status_code} from provider"

                    # Check Content-Type header if provided
                    ct = response.headers.get("content-type", "").lower()
                    if "text/html" in ct and "pdf" not in ct:
                        return None, "Server returned HTML instead of PDF (paywall or splash page)"

                    # Stream with size limit
                    chunks = []
                    total_bytes = 0
                    async for chunk in response.aiter_bytes():
                        total_bytes += len(chunk)
                        if total_bytes > MAX_PDF_SIZE_BYTES:
                            return None, f"PDF exceeded max size of {MAX_PDF_SIZE_BYTES // (1024*1024)}MB"
                        chunks.append(chunk)

                    pdf_bytes = b"".join(chunks)

            # Validate magic bytes
            if not pdf_bytes.startswith(b"%PDF-"):
                first_kb = pdf_bytes[:1024]
                if b"%PDF-" not in first_kb:
                    return None, "File header does not contain valid PDF magic bytes (%PDF-)"

            # Save to disk cache
            try:
                cache_path.write_bytes(pdf_bytes)
            except Exception as e:
                logger.warning(f"Failed to write PDF disk cache: {e}")

            return pdf_bytes, None

        except httpx.TimeoutException:
            return None, "Connection timed out during PDF download"
        except httpx.RequestError as e:
            return None, f"Network request error: {str(e)}"
        except Exception as e:
            return None, f"Unexpected download failure: {str(e)}"

    def extract_text_and_sections(self, pdf_bytes: bytes) -> tuple[str, dict[str, str], int, Optional[str]]:
        """Extract text and detect structured sections using PyMuPDF (with fallback to pypdf)."""
        if not pdf_bytes or (not pdf_bytes.startswith(b"%PDF-") and b"%PDF-" not in pdf_bytes[:1024]):
            return "", {}, 0, "Invalid PDF: Missing %PDF- file signature"

        text = ""
        page_count = 0
        error_msg = None

        # 1. Primary: PyMuPDF
        try:
            import pymupdf as fitz
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            page_count = len(doc)
            pages_text = []
            for page in doc:
                page_text = page.get_text() or ""
                pages_text.append(page_text)
            doc.close()
            text = "\n\n".join(pages_text)
        except Exception as e:
            logger.warning(f"PyMuPDF extraction failed: {e}. Attempting pypdf fallback...")
            # 2. Secondary fallback: pypdf
            try:
                import pypdf
                stream = io.BytesIO(pdf_bytes)
                reader = pypdf.PdfReader(stream)
                page_count = len(reader.pages)
                pages_text = [p.extract_text() or "" for p in reader.pages]
                text = "\n\n".join(pages_text)
            except Exception as e2:
                logger.error(f"Both PyMuPDF and pypdf failed: {e2}")
                return "", {}, 0, f"PDF text extraction failed: {str(e2)}"

        if not text.strip():
            return "", {}, page_count, "Extracted text is empty (scanned or protected PDF)"

        # Normalize text
        text = self._normalize_extracted_text(text)

        # Detect sections heuristically
        sections = self._detect_sections(text)

        return text, sections, page_count, None

    def _normalize_extracted_text(self, text: str) -> str:
        """Clean whitespace, line breaks, and repeated page artifacts."""
        t = text.replace('\r\n', '\n').replace('\r', '\n').replace('\xa0', ' ')
        t = re.sub(r'\n{3,}', '\n\n', t)
        t = re.sub(r'[ \t]+', ' ', t)
        return t.strip()

    def _detect_sections(self, text: str) -> dict[str, str]:
        """Detect standard academic sections from text using heading heuristics."""
        lines = text.split('\n')
        sections: dict[str, list[str]] = {}
        current_section = "preamble"
        sections[current_section] = []

        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue

            matched_section = None
            if len(line_str) < 80:
                for sec_key, pattern in SECTION_PATTERNS.items():
                    if pattern.match(line_str):
                        matched_section = sec_key
                        break

            if matched_section:
                current_section = matched_section
                if current_section not in sections:
                    sections[current_section] = []
            else:
                sections[current_section].append(line)

        result: dict[str, str] = {}
        for sec_name, sec_lines in sections.items():
            content = "\n".join(sec_lines).strip()
            if content and len(content) > 20:
                result[sec_name] = content

        return result

    async def enrich_paper(self, paper: Paper) -> Paper:
        """Enrich a paper with open-access full text if available."""
        if paper.full_text_available and paper.sections:
            paper.content_status = PaperContentStatus.FULL_TEXT
            return paper

        candidate_url = resolve_candidate_pdf_url(paper)
        if not candidate_url:
            paper.content_status = (
                PaperContentStatus.ABSTRACT_ONLY if paper.abstract else PaperContentStatus.METADATA_ONLY
            )
            paper.retrieval_failure_reason = "No open-access PDF URL identified for paper"
            return paper

        paper.pdf_url = candidate_url
        pdf_bytes, err = await self.fetch_pdf_bytes(candidate_url)
        if err or not pdf_bytes:
            paper.content_status = PaperContentStatus.FULL_TEXT_FAILED
            paper.retrieval_failure_reason = err or "Download returned empty payload"
            logger.info(f"OA full-text retrieval failed for '{paper.title[:40]}': {paper.retrieval_failure_reason}")
            return paper

        full_text, sections, page_count, extract_err = self.extract_text_and_sections(pdf_bytes)
        if extract_err or not full_text:
            paper.content_status = PaperContentStatus.FULL_TEXT_FAILED
            paper.retrieval_failure_reason = extract_err or "Failed to parse text from PDF bytes"
            return paper

        paper.full_text_available = True
        paper.page_count = page_count
        paper.text_length = len(full_text)
        paper.sections = sections
        paper.sections["full_text"] = full_text[:100000]

        has_methods_or_results = bool(sections.get("methods") or sections.get("results") or sections.get("experimental_setup"))
        if has_methods_or_results:
            paper.content_status = PaperContentStatus.FULL_TEXT
        else:
            paper.content_status = PaperContentStatus.FULL_TEXT_PARTIAL

        paper.extraction_status = f"Extracted {page_count} pages, {len(sections)} sections, {len(full_text)} chars"
        logger.info(f"✓ Successfully retrieved OA full text for '{paper.title[:50]}': {paper.content_status.value} ({page_count} pages)")
        return paper

    async def enrich_papers_batch(self, papers: list[Paper]) -> list[Paper]:
        """Enrich a list of candidate papers in parallel with bounded concurrency."""
        tasks = [self.enrich_paper(p) for p in papers]
        return await asyncio.gather(*tasks)


# Singleton
_retriever: Optional[FullTextRetriever] = None


def get_full_text_retriever() -> FullTextRetriever:
    global _retriever
    if _retriever is None:
        _retriever = FullTextRetriever()
    return _retriever
