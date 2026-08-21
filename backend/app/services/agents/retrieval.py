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

    async def execute(self, session: ResearchSession, **kwargs) -> None:
        """
        Executes search, dedup, and ranking.
        """
        if not session.plan or not session.plan.search_queries:
            logger.warning("No search queries found in plan. Falling back to main question.")
            queries = [session.question]
        else:
            queries = session.plan.search_queries[:6]

        all_papers = []
        for query in queries:
            for provider in self.providers:
                try:
                    results = await provider.search(query, max_results=15)
                    all_papers.extend(results)
                    session.searches.append(SearchResult(
                        query=query, provider=provider.provider_name,
                        papers_found=len(results),
                        paper_ids=[p.id for p in results]
                    ))
                except Exception as e:
                    logger.warning(f"Search failed ({provider.provider_name}): {e}")
            await asyncio.sleep(0.5)  # Rate limiting between queries

        # Deduplicate
        deduped = self._deduplicate_papers(all_papers)
        
        # Rank
        ranked = self._rank_papers(deduped, session.question)
        
        # Select top N
        selected = ranked[:self.max_papers]
        for p in selected:
            session.papers[p.id] = p
            
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
