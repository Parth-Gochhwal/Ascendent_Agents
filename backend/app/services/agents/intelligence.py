import logging
from backend.app.services.agents.base import BaseAgent
from backend.app.models.research import ResearchSession
from backend.app.services import research_intelligence as ri

logger = logging.getLogger(__name__)

class IntelligenceAgent(BaseAgent):
    """
    Executes the pure deterministic research intelligence computations (no LLM).
    This handles citation graph, claim propagations, citation echoes, dead ends, 
    reproducibility, evidence strength, and integrity auditing.
    """
    @property
    def name(self) -> str:
        return "Deterministic Intelligence"

    async def execute(self, session: ResearchSession, phase: str = "all", **kwargs) -> None:
        """
        Executes deterministic intelligence phases. 
        `phase` allows splitting execution (e.g. "pre_synthesis" vs "post_synthesis").
        """
        if phase in ("pre_synthesis", "all"):
            # Citation Graph
            session.citations = ri._build_citation_graph(session) if hasattr(ri, '_build_citation_graph') else self._build_citation_graph(session)
            
            # Dead-End Atlas
            session.dead_ends = ri.detect_dead_ends(session)
            
            # Reproducibility Profiler
            for pid, paper in session.papers.items():
                analysis = session.analyses.get(pid)
                profile = ri.compute_reproducibility_profile(paper, analysis)
                session.reproducibility_profiles[pid] = profile
                
            # ClaimLine Tracker
            session.claim_propagations = ri.build_claim_propagations(session)
            
            # Citation Echo Detector
            session.citation_echoes = ri.detect_citation_echoes(session)
            
            # Evidence Strength Engine
            for claim in session.claims:
                paper = session.papers.get(claim.paper_id)
                if paper:
                    claim.strength = ri.compute_evidence_strength(claim, session.evidence, paper, session)
                    
        if phase in ("post_synthesis", "all"):
            # Apply independence weighting to consensus findings (runs after consensus)
            for i, finding in enumerate(session.consensus):
                session.consensus[i] = ri.compute_consensus_independence(finding, session)
                
            # Integrity Audit (runs at the very end)
            session.audit = ri.run_deterministic_audit(session)


    def _build_citation_graph(self, session: ResearchSession):
        """Fallback citation graph builder if not exposed by ri."""
        from backend.app.models.research import CitationEdge
        import re
        
        def normalize_title(title: str) -> str:
            t = title.lower().strip()
            t = re.sub(r'[^\w\s]', '', t)
            t = re.sub(r'\s+', ' ', t)
            return t
            
        edges = []
        paper_titles = {normalize_title(p.title): p.id for p in session.papers.values()}
        for pid, paper in session.papers.items():
            text = (paper.abstract or "").lower()
            for title_norm, ref_id in paper_titles.items():
                if ref_id != pid and title_norm in text:
                    edges.append(CitationEdge(
                        source_paper_id=pid, target_paper_id=ref_id,
                        is_inferred=True, context="Inferred from textual overlap in abstract"
                    ))
        return edges
