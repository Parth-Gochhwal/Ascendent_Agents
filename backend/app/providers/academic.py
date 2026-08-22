"""Academic search provider abstraction and implementations.

Supports OpenAlex, Semantic Scholar, Crossref, and arXiv.
Each provider normalizes results to the common Paper model.
"""
import asyncio
import logging
import re
from abc import ABC, abstractmethod
from typing import Optional

import httpx

from backend.app.models.research import Author, Paper

logger = logging.getLogger(__name__)


class AcademicSearchProvider(ABC):
    """Abstract academic search provider."""

    @abstractmethod
    async def search(self, query: str, max_results: int = 25) -> list[Paper]:
        ...

    @abstractmethod
    async def get_paper(self, paper_id: str) -> Optional[Paper]:
        ...

    @property
    @abstractmethod
    def provider_name(self) -> str:
        ...


class OpenAlexProvider(AcademicSearchProvider):
    """OpenAlex API provider — free, with optional API key for higher rate limits."""

    BASE_URL = "https://api.openalex.org"

    def __init__(self, email: str = "", api_key: str = ""):
        self.email = email
        self.api_key = api_key
        self._client = httpx.AsyncClient(timeout=30.0, follow_redirects=True)

    @property
    def provider_name(self) -> str:
        return "openalex"

    def _params(self) -> dict:
        params = {}
        if self.email:
            params["mailto"] = self.email
        if self.api_key:
            params["api_key"] = self.api_key
        return params

    def _parse_paper(self, work: dict) -> Paper:
        authors = []
        for authorship in work.get("authorships", [])[:10]:
            author_info = authorship.get("author", {})
            name = author_info.get("display_name", "Unknown")
            inst = ""
            insts = authorship.get("institutions", [])
            if insts:
                inst = insts[0].get("display_name", "")
            authors.append(Author(name=name, affiliation=inst or None,
                                  orcid=author_info.get("orcid")))

        doi = work.get("doi", "")
        if doi and doi.startswith("https://doi.org/"):
            doi = doi[16:]

        oa = work.get("open_access", {})
        pdf_url = (
            oa.get("oa_url")
            or work.get("primary_location", {}).get("pdf_url")
            or (work.get("best_oa_location") or {}).get("pdf_url")
        )
        is_oa = bool(oa.get("is_oa") or pdf_url)
        abstract = self._reconstruct_abstract(work.get("abstract_inverted_index"))

        from backend.app.models.research import PaperContentStatus
        initial_status = (
            PaperContentStatus.ABSTRACT_ONLY if abstract else PaperContentStatus.METADATA_ONLY
        )

        return Paper(
            title=work.get("display_name", work.get("title", "Unknown")),
            authors=authors,
            year=work.get("publication_year"),
            venue=work.get("primary_location", {}).get("source", {}).get("display_name") if work.get("primary_location") else None,
            doi=doi or None,
            url=work.get("doi") or work.get("id"),
            abstract=abstract,
            citation_count=work.get("cited_by_count", 0),
            source_provider=self.provider_name,
            source_ids={"openalex": work.get("id", "")},
            open_access=is_oa,
            pdf_url=pdf_url,
            content_status=initial_status,
        )

    def _reconstruct_abstract(self, inverted_index: Optional[dict]) -> Optional[str]:
        if not inverted_index:
            return None
        word_positions = []
        for word, positions in inverted_index.items():
            for pos in positions:
                word_positions.append((pos, word))
        word_positions.sort()
        return " ".join(w for _, w in word_positions) if word_positions else None

    async def search(self, query: str, max_results: int = 25) -> list[Paper]:
        clean_query = re.sub(r'[?#<>\r\n]+', ' ', query).strip()
        if not clean_query:
            return []
        params = self._params()
        params.update({
            "search": clean_query,
            "per_page": min(max_results, 50),
            "select": "id,display_name,title,authorships,publication_year,doi,cited_by_count,primary_location,open_access,abstract_inverted_index",
        })
        try:
            resp = await self._client.get(f"{self.BASE_URL}/works", params=params)
            resp.raise_for_status()
            data = resp.json()
            results = data.get("results", [])
            return [self._parse_paper(w) for w in results]
        except Exception as e:
            logger.error(f"OpenAlex search error: {e}")
            return []

    async def get_paper(self, paper_id: str) -> Optional[Paper]:
        try:
            params = self._params()
            resp = await self._client.get(f"{self.BASE_URL}/works/{paper_id}", params=params)
            resp.raise_for_status()
            return self._parse_paper(resp.json())
        except Exception as e:
            logger.error(f"OpenAlex get_paper error: {e}")
            return None


class SemanticScholarProvider(AcademicSearchProvider):
    """Semantic Scholar API provider."""

    BASE_URL = "https://api.semanticscholar.org/graph/v1"

    def __init__(self, api_key: str = ""):
        self.api_key = api_key
        headers = {}
        if api_key:
            headers["x-api-key"] = api_key
        self._client = httpx.AsyncClient(timeout=30.0, headers=headers, follow_redirects=True)

    @property
    def provider_name(self) -> str:
        return "semantic_scholar"

    def _parse_paper(self, data: dict) -> Paper:
        authors = [
            Author(name=a.get("name", "Unknown"))
            for a in data.get("authors", [])[:10]
        ]
        ext_ids = data.get("externalIds") or {}
        doi = ext_ids.get("DOI")
        arxiv_id = ext_ids.get("ArXiv") or ext_ids.get("arXiv")
        
        pdf_url = data.get("openAccessPdf", {}).get("url") if data.get("openAccessPdf") else None
        if not pdf_url and arxiv_id:
            pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"

        source_ids = {"semantic_scholar": data.get("paperId", "")}
        if arxiv_id:
            source_ids["arxiv"] = arxiv_id

        abstract = data.get("abstract")
        from backend.app.models.research import PaperContentStatus
        initial_status = (
            PaperContentStatus.ABSTRACT_ONLY if abstract else PaperContentStatus.METADATA_ONLY
        )

        return Paper(
            title=data.get("title", "Unknown"),
            authors=authors,
            year=data.get("year"),
            venue=data.get("venue") or data.get("publicationVenue", {}).get("name") if data.get("publicationVenue") else data.get("venue"),
            doi=doi,
            url=data.get("url"),
            abstract=abstract,
            citation_count=data.get("citationCount", 0),
            source_provider=self.provider_name,
            source_ids=source_ids,
            open_access=bool(data.get("isOpenAccess") or pdf_url),
            pdf_url=pdf_url,
            content_status=initial_status,
        )

    async def search(self, query: str, max_results: int = 25) -> list[Paper]:
        params = {
            "query": query,
            "limit": min(max_results, 100),
            "fields": "title,authors,year,venue,externalIds,abstract,citationCount,url,isOpenAccess,openAccessPdf,publicationVenue",
        }
        try:
            resp = await self._client.get(f"{self.BASE_URL}/paper/search", params=params)
            resp.raise_for_status()
            data = resp.json()
            return [self._parse_paper(p) for p in data.get("data", [])]
        except Exception as e:
            logger.error(f"Semantic Scholar search error: {e}")
            return []

    async def get_paper(self, paper_id: str) -> Optional[Paper]:
        try:
            params = {"fields": "title,authors,year,venue,externalIds,abstract,citationCount,url,isOpenAccess,openAccessPdf,publicationVenue,references"}
            resp = await self._client.get(f"{self.BASE_URL}/paper/{paper_id}", params=params)
            resp.raise_for_status()
            return self._parse_paper(resp.json())
        except Exception as e:
            logger.error(f"Semantic Scholar get_paper error: {e}")
            return None


class CrossrefProvider(AcademicSearchProvider):
    """Crossref API provider."""

    BASE_URL = "https://api.crossref.org"

    def __init__(self, email: str = ""):
        self.email = email
        headers = {"User-Agent": f"NEXUS/1.0 (mailto:{email})" if email else "NEXUS/1.0"}
        self._client = httpx.AsyncClient(timeout=30.0, headers=headers, follow_redirects=True)

    @property
    def provider_name(self) -> str:
        return "crossref"

    def _parse_paper(self, item: dict) -> Paper:
        authors = []
        for a in item.get("author", [])[:10]:
            name = f"{a.get('given', '')} {a.get('family', '')}".strip()
            if name:
                authors.append(Author(name=name, affiliation=a.get("affiliation", [{}])[0].get("name") if a.get("affiliation") else None))

        title = item.get("title", ["Unknown"])[0] if item.get("title") else "Unknown"
        year = None
        if item.get("published-print"):
            parts = item["published-print"].get("date-parts", [[None]])[0]
            year = parts[0] if parts else None
        elif item.get("published-online"):
            parts = item["published-online"].get("date-parts", [[None]])[0]
            year = parts[0] if parts else None

        venue = None
        if item.get("container-title"):
            venue = item["container-title"][0] if item["container-title"] else None

        abstract = self._clean_abstract(item.get("abstract", ""))
        from backend.app.models.research import PaperContentStatus
        initial_status = (
            PaperContentStatus.ABSTRACT_ONLY if abstract else PaperContentStatus.METADATA_ONLY
        )

        return Paper(
            title=title,
            authors=authors,
            year=year,
            venue=venue,
            doi=item.get("DOI"),
            url=item.get("URL"),
            abstract=abstract,
            citation_count=item.get("is-referenced-by-count", 0),
            source_provider=self.provider_name,
            source_ids={"crossref": item.get("DOI", "")},
            content_status=initial_status,
        )

    def _clean_abstract(self, abstract: str) -> Optional[str]:
        if not abstract:
            return None
        # Remove JATS XML tags
        clean = re.sub(r"<[^>]+>", "", abstract)
        return clean.strip() or None

    async def search(self, query: str, max_results: int = 25) -> list[Paper]:
        clean_query = re.sub(r'[?#<>\r\n]+', ' ', query).strip()
        if not clean_query:
            return []
        params = {
            "query": clean_query,
            "rows": min(max_results, 50),
            "sort": "relevance",
            "select": "DOI,title,author,published-print,published-online,container-title,abstract,is-referenced-by-count,URL",
        }
        try:
            resp = await self._client.get(f"{self.BASE_URL}/works", params=params)
            resp.raise_for_status()
            data = resp.json()
            items = data.get("message", {}).get("items", [])
            return [self._parse_paper(item) for item in items]
        except Exception as e:
            logger.error(f"Crossref search error: {e}")
            return []

    async def get_paper(self, paper_id: str) -> Optional[Paper]:
        try:
            resp = await self._client.get(f"{self.BASE_URL}/works/{paper_id}")
            resp.raise_for_status()
            data = resp.json()
            return self._parse_paper(data.get("message", {}))
        except Exception as e:
            logger.error(f"Crossref get_paper error: {e}")
            return None


class ArxivProvider(AcademicSearchProvider):
    """arXiv API provider."""

    BASE_URL = "https://export.arxiv.org/api/query"

    def __init__(self):
        self._client = httpx.AsyncClient(timeout=30.0, follow_redirects=True)

    @property
    def provider_name(self) -> str:
        return "arxiv"

    def _parse_entry(self, entry: dict) -> Paper:
        authors = []
        entry_authors = entry.get("authors", [])
        if isinstance(entry_authors, str):
            entry_authors = [entry_authors]
        for a in entry_authors[:10]:
            if isinstance(a, dict):
                authors.append(Author(name=a.get("name", "Unknown")))
            else:
                authors.append(Author(name=str(a)))

        year = None
        published = entry.get("published", "")
        if published and len(published) >= 4:
            try:
                year = int(published[:4])
            except ValueError:
                pass

        arxiv_id = entry.get("id", "")
        if "arxiv.org/abs/" in arxiv_id:
            arxiv_id = arxiv_id.split("arxiv.org/abs/")[-1]

        pdf_url = entry.get("pdf_url")
        if not pdf_url and arxiv_id:
            pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"

        abstract = entry.get("summary", "").replace("\n", " ").strip() or None
        from backend.app.models.research import PaperContentStatus
        initial_status = (
            PaperContentStatus.ABSTRACT_ONLY if abstract else PaperContentStatus.METADATA_ONLY
        )

        return Paper(
            title=entry.get("title", "Unknown").replace("\n", " ").strip(),
            authors=authors,
            year=year,
            venue="arXiv",
            doi=entry.get("doi"),
            url=entry.get("id"),
            abstract=abstract,
            source_provider=self.provider_name,
            source_ids={"arxiv": arxiv_id},
            open_access=True,
            pdf_url=pdf_url,
            content_status=initial_status,
        )

    async def search(self, query: str, max_results: int = 25) -> list[Paper]:
        import xml.etree.ElementTree as ET
        clean_query = re.sub(r'[?#<>\r\n]+', ' ', query).strip()
        if not clean_query:
            return []
        params = {
            "search_query": f"all:{clean_query}",
            "start": 0,
            "max_results": min(max_results, 50),
            "sortBy": "relevance",
            "sortOrder": "descending",
        }
        try:
            resp = await self._client.get(self.BASE_URL, params=params)
            resp.raise_for_status()
            root = ET.fromstring(resp.text)
            ns = {"atom": "http://www.w3.org/2005/Atom"}
            papers = []
            for entry in root.findall("atom:entry", ns):
                title = entry.findtext("atom:title", "", ns).replace("\n", " ").strip()
                summary = entry.findtext("atom:summary", "", ns).replace("\n", " ").strip()
                entry_id = entry.findtext("atom:id", "", ns)
                published = entry.findtext("atom:published", "", ns)
                authors = []
                for author in entry.findall("atom:author", ns):
                    name = author.findtext("atom:name", "Unknown", ns)
                    authors.append(Author(name=name))

                year = None
                if published and len(published) >= 4:
                    try:
                        year = int(published[:4])
                    except ValueError:
                        pass

                arxiv_id = entry_id
                if "arxiv.org/abs/" in entry_id:
                    arxiv_id = entry_id.split("arxiv.org/abs/")[-1]

                pdf_url = None
                for link in entry.findall("atom:link", ns):
                    if link.get("title") == "pdf":
                        pdf_url = link.get("href")

                doi = None
                arxiv_doi = entry.find("{http://arxiv.org/schemas/atom}doi")
                if arxiv_doi is not None and arxiv_doi.text:
                    doi = arxiv_doi.text

                papers.append(Paper(
                    title=title,
                    authors=authors,
                    year=year,
                    venue="arXiv",
                    doi=doi,
                    url=entry_id,
                    abstract=summary or None,
                    source_provider=self.provider_name,
                    source_ids={"arxiv": arxiv_id},
                    open_access=True,
                    pdf_url=pdf_url,
                ))
            return papers
        except Exception as e:
            logger.error(f"arXiv search error: {e}")
            return []

    async def get_paper(self, paper_id: str) -> Optional[Paper]:
        results = await self.search(f"id:{paper_id}", max_results=1)
        return results[0] if results else None
