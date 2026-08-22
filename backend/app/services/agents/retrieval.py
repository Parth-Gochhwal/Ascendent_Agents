import asyncio
import logging
import re
import math
from typing import List

from backend.app.services.agents.base import BaseAgent
from backend.app.models.research import ResearchSession, SearchResult, Paper
from backend.app.providers.academic import AcademicSearchProvider

logger = logging.getLogger(__name__)

class RetrievalAgent(BaseAgent):
    """
    Handles literature discovery, deduplication, and relevance ranking.
    """
    def __init__(self, llm, providers: List[AcademicSearchProvider], max_papers: int = 15):
        super().__init__(llm)
        self.providers = providers
        self.max_papers = max_papers

    @property
    def name(self) -> str:
        return "Literature Discovery"

    @property
    def description(self) -> str:
        return "Discovers academic literature, deduplicates by DOI/title, and computes relevance scores."

    async def execute(self, session: ResearchSession, **kwargs) -> None:
        """
        Executes search, dedup, and ranking with degradation tracking.
        """
        from backend.app.models.research import StageResult

        if not session.plan or not session.plan.search_queries:
            logger.warning("No search queries found in plan. Falling back to main question.")
            queries = [session.question]
        else:
            queries = session.plan.search_queries[:6]

        all_papers = []
        failed_providers = []
        for query in queries[:4]:
            tasks = [provider.search(query, max_results=10) for provider in self.providers]
            results_lists = await asyncio.gather(*tasks, return_exceptions=True)
            for provider, res in zip(self.providers, results_lists):
                if isinstance(res, Exception):
                    logger.warning(f"Search failed ({provider.provider_name}): {res}")
                    failed_providers.append(f"{provider.provider_name}: {res}")
                elif isinstance(res, list):
                    all_papers.extend(res)
                    session.searches.append(SearchResult(
                        query=query, provider=provider.provider_name,
                        papers_found=len(res),
                        paper_ids=[p.id for p in res]
                    ))

        # Deduplicate
        deduped = self._deduplicate_papers(all_papers)
        
        # Rank
        ranked = self._rank_papers(deduped, session.question)
        
        # Select top N
        selected = ranked[:self.max_papers]
        
        # Enrich selected papers with Open-Access Full Text
        from backend.app.services.full_text import get_full_text_retriever
        retriever = get_full_text_retriever()
        enriched_selected = await retriever.enrich_papers_batch(selected)
        
        for p in enriched_selected:
            session.papers[p.id] = p
            
        full_text_count = sum(1 for p in enriched_selected if p.full_text_available)
        abstract_only_count = sum(1 for p in enriched_selected if not p.full_text_available)
        logger.info(f"Retrieval complete: {len(enriched_selected)} papers selected ({full_text_count} full-text, {abstract_only_count} abstract-only)")

        if len(selected) == 0:
            self.record_stage(session, "retrieval", StageResult.FAILED,
                              "No papers retrieved from academic providers — downstream analysis cannot proceed")
        elif failed_providers:
            self.record_stage(session, "retrieval", StageResult.PARTIAL,
                              f"Retrieved {len(selected)} papers ({full_text_count} full text), but some searches failed ({', '.join(failed_providers[:2])})")
        else:
            self.record_stage(session, "retrieval", StageResult.SUCCESS)

        return len(all_papers), len(deduped), len(selected)

    def _deduplicate_papers(self, papers: list[Paper]) -> list[Paper]:
        """Deduplicate papers by DOI and normalized title."""
        seen_dois = set()
        seen_titles = set()
        unique = []
        for p in papers:
            # DOI-based dedup
            if p.doi:
                doi_lower = p.doi.lower().strip()
                if doi_lower in seen_dois:
                    continue
                seen_dois.add(doi_lower)

            # Title-based dedup
            norm_title = self._normalize_title(p.title)
            if norm_title in seen_titles:
                continue
            seen_titles.add(norm_title)
            unique.append(p)
        return unique

    def _normalize_title(self, title: str) -> str:
        """Normalize title for deduplication."""
        t = title.lower().strip()
        t = re.sub(r'[^\w\s]', '', t)
        t = re.sub(r'\s+', ' ', t)
        return t

    def _rank_papers(self, papers: list[Paper], question: str) -> list[Paper]:
        """Rank papers using a deterministic hybrid scoring heuristic."""
        q_clean = re.sub(r'[^\w\s]', '', question.lower())
        q_words = [w for w in q_clean.split() if len(w) > 3]
        if not q_words:
            q_words = q_clean.split()

        for p in papers:
            title_clean = re.sub(r'[^\w\s]', '', p.title.lower())
            abstract_clean = re.sub(r'[^\w\s]', '', (p.abstract or "").lower())
            
            exact_phrase_score = 0.0
            if q_clean and q_clean in title_clean:
                exact_phrase_score += 1.0
            if q_clean and q_clean in abstract_clean:
                exact_phrase_score += 0.5
                
            title_matches = sum(1 for w in q_words if w in title_clean.split())
            abstract_matches = sum(1 for w in q_words if w in abstract_clean.split())
            
            title_overlap = title_matches / max(len(q_words), 1)
            abstract_overlap = min(1.0, abstract_matches / max(len(q_words), 1))
            
            relevance = min(1.0, (0.5 * title_overlap) + (0.3 * abstract_overlap) + (0.2 * exact_phrase_score))

            # Recency
            recency = 0.0
            if p.year:
                recency = min(1.0, max(0.0, (p.year - 2018) / 7))

            # Citation influence (log scale)
            citation_score = 0.0
            if p.citation_count and p.citation_count > 0:
                citation_score = min(1.0, math.log(p.citation_count + 1) / 6)

            # Completeness
            completeness = 0.5 if p.abstract else 0.0

            # Composite score
            p.relevance_score = round(relevance, 3)
            p.research_score = round(
                0.40 * relevance + 0.25 * recency + 0.20 * citation_score + 0.15 * completeness,
                3
            )
            p.score_components = {
                "relevance": round(relevance, 3),
                "recency": round(recency, 3),
                "citation_influence": round(citation_score, 3),
                "completeness": round(completeness, 3),
            }

        papers.sort(key=lambda p: p.research_score, reverse=True)
        return papers
