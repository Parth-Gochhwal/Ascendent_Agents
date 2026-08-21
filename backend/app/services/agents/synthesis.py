import logging
from backend.app.services.agents.base import BaseAgent
from backend.app.models.research import ResearchSession, ContradictionList, ConsensusList
from backend.app.prompts.templates import (
    CONTRADICTION_ANALYSIS_V1, CONSENSUS_ANALYSIS_V1, SYSTEM_PROMPT
)

logger = logging.getLogger(__name__)

class SynthesisAgent(BaseAgent):
    """
    Synthesizes extracted evidence to detect contradictions and build consensus clusters.
    """
    @property
    def name(self) -> str:
        return "Synthesis Engine"

    async def execute(self, session: ResearchSession, **kwargs) -> None:
        """
        Executes contradiction and consensus analysis.
        """
        # Contradictions
        try:
            session.contradictions = await self._detect_contradictions(session)
        except Exception as e:
            logger.warning(f"Contradiction analysis failed: {e}")
            
        # Consensus
        try:
            session.consensus = await self._analyze_consensus(session)
        except Exception as e:
            logger.warning(f"Consensus analysis failed: {e}")


    async def _detect_contradictions(self, session: ResearchSession):
        contradictions = []
        claims = session.claims
        if len(claims) < 2:
            return contradictions

        # Use ri's contradiction candidate generator if available, otherwise fallback
        from backend.app.services import research_intelligence as ri
        
        pairs_to_check = ri.generate_contradiction_candidates(claims, session.papers)
        
        # Limit pairs for API budget
        pairs_to_check = pairs_to_check[:10]

        for claim_a, claim_b in pairs_to_check:
            paper_a = session.papers.get(claim_a.paper_id)
            paper_b = session.papers.get(claim_b.paper_id)
            if not paper_a or not paper_b:
                continue

            prompt = CONTRADICTION_ANALYSIS_V1.format(
                paper_a_title=paper_a.title, paper_a_year=paper_a.year or "Unknown",
                claim_a=claim_a.statement, conditions_a=", ".join(claim_a.conditions),
                metric_a=claim_a.metric or "N/A", evidence_a=claim_a.evidence_value or "N/A",
                paper_b_title=paper_b.title, paper_b_year=paper_b.year or "Unknown",
                claim_b=claim_b.statement, conditions_b=", ".join(claim_b.conditions),
                metric_b=claim_b.metric or "N/A", evidence_b=claim_b.evidence_value or "N/A",
            )
            try:
                res = await self.llm.structured_generate(prompt, ContradictionList, system_prompt=SYSTEM_PROMPT)
                for c in res.contradictions:
                    c.claim_a_id = claim_a.id
                    c.claim_b_id = claim_b.id
                    c.paper_a_id = paper_a.id
                    c.paper_b_id = paper_b.id
                    contradictions.append(c)
            except Exception as e:
                logger.warning(f"Failed to analyze contradiction pair: {e}")

        return contradictions

    async def _analyze_consensus(self, session: ResearchSession):
        claims_summary = "\n".join(
            f"- [{c.paper_id}] {c.statement}" for c in session.claims
        )
        prompt = CONSENSUS_ANALYSIS_V1.format(claims=claims_summary)
        result = await self.llm.structured_generate(prompt, ConsensusList, system_prompt=SYSTEM_PROMPT)
        return result.findings if result else []
