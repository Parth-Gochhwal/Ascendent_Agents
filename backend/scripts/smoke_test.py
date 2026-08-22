"""NEXUS Live System Diagnostic and Smoke Test.

Verifies connectivity and health for:
- Gemini LLM Provider
- OpenAlex API
- Semantic Scholar API
- Crossref API
- arXiv API
- FullTextRetriever & PyMuPDF extraction

Usage:
    python backend/scripts/smoke_test.py
"""
import asyncio
import os
import sys
from pathlib import Path

# Ensure workspace root is in python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from backend.app.core.config import get_settings
from backend.app.providers.academic import (
    OpenAlexProvider, SemanticScholarProvider, CrossrefProvider, ArxivProvider
)
from backend.app.providers.llm_provider import GeminiProvider
from backend.app.services.full_text import FullTextRetriever, is_valid_pdf_url


async def run_smoke_test():
    print("============================================================")
    print("🔬 NEXUS — AI Research Scientist: Live Diagnostic Smoke Test")
    print("============================================================")
    
    settings = get_settings()
    results = {}
    
    # 1. Gemini Connectivity
    if settings.gemini_api_key:
        try:
            gemini = GeminiProvider()
            is_ok = await gemini.health_check()
            results["Gemini LLM"] = "OK" if is_ok else "FAILED (health check returned False)"
        except Exception as e:
            results["Gemini LLM"] = f"FAILED ({type(e).__name__}: {str(e)[:60]})"
    else:
        results["Gemini LLM"] = "SKIPPED (GEMINI_API_KEY not configured in .env)"

    # 2. OpenAlex
    try:
        openalex = OpenAlexProvider(email=settings.openalex_email, api_key=settings.openalex_api_key)
        papers = await openalex.search("graph neural networks", max_results=1)
        if papers and len(papers) > 0:
            results["OpenAlex API"] = f"OK (retrieved: '{papers[0].title[:40]}...')"
        else:
            results["OpenAlex API"] = "WARNING (0 results returned)"
    except Exception as e:
        results["OpenAlex API"] = f"FAILED ({type(e).__name__}: {str(e)[:60]})"

    # 3. Semantic Scholar
    try:
        s2 = SemanticScholarProvider(api_key=settings.semantic_scholar_api_key)
        papers = await s2.search("transformer models", max_results=1)
        if papers and len(papers) > 0:
            results["Semantic Scholar API"] = f"OK (retrieved: '{papers[0].title[:40]}...')"
        else:
            results["Semantic Scholar API"] = "SKIPPED/EMPTY (rate limited or key required)"
    except Exception as e:
        results["Semantic Scholar API"] = f"WARNING ({type(e).__name__}: {str(e)[:60]})"

    # 4. Crossref
    try:
        crossref = CrossrefProvider(email=settings.crossref_email)
        papers = await crossref.search("retrieval augmented generation", max_results=1)
        if papers and len(papers) > 0:
            results["Crossref API"] = f"OK (retrieved: '{papers[0].title[:40]}...')"
        else:
            results["Crossref API"] = "WARNING (0 results returned)"
    except Exception as e:
        results["Crossref API"] = f"FAILED ({type(e).__name__}: {str(e)[:60]})"

    # 5. arXiv
    try:
        arxiv = ArxivProvider()
        papers = await arxiv.search("quantum computing", max_results=1)
        if papers and len(papers) > 0:
            results["arXiv API"] = f"OK (retrieved: '{papers[0].title[:40]}...')"
        else:
            results["arXiv API"] = "WARNING (0 results returned)"
    except Exception as e:
        results["arXiv API"] = f"FAILED ({type(e).__name__}: {str(e)[:60]})"

    # 6. Full-Text & PyMuPDF Engine
    try:
        import pymupdf as fitz
        retriever = FullTextRetriever()
        assert is_valid_pdf_url("https://arxiv.org/pdf/2301.00001.pdf")
        assert not is_valid_pdf_url("file:///etc/passwd")
        assert not is_valid_pdf_url("http://127.0.0.1/test.pdf")
        results["Full-Text Engine (PyMuPDF)"] = f"OK (PyMuPDF v{fitz.__version__} loaded, URL validator verified)"
    except Exception as e:
        results["Full-Text Engine (PyMuPDF)"] = f"FAILED ({type(e).__name__}: {str(e)[:60]})"

    # Print Summary Table
    print("\nDiagnostic Status Report:")
    print("------------------------------------------------------------")
    for provider, status in results.items():
        print(f"  {provider:<28} : {status}")
    print("------------------------------------------------------------")
    
    # Overall summary
    has_retrieval = any("OK" in str(v) for k, v in results.items() if "API" in k)
    if has_retrieval and "OK" in str(results.get("Full-Text Engine (PyMuPDF)", "")):
        print("✓ Core Live Academic Capabilities: OPERATIONAL")
        return 0
    else:
        print("⚠️ Core Live Capabilities: DEGRADED")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(run_smoke_test())
    sys.exit(exit_code)
