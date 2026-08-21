import logging
from backend.app.services.agents.base import BaseAgent
from backend.app.models.research import ResearchSession, PaperAnalysis, ClaimList, MethodPipeline
from backend.app.prompts.templates import (
    PAPER_EXTRACTION_V1, CLAIM_EXTRACTION_V1, METHOD_EXTRACTION_V1, SYSTEM_PROMPT
)

logger = logging.getLogger(__name__)

class AnalysisAgent(BaseAgent):
    """
    Analyzes papers deeply to extract findings, claims, evidence, and methods.
    """
    @property
    def name(self) -> str:
        return "Paper Intelligence"

    async def execute(self, session: ResearchSession, **kwargs) -> None:
        """
        Executes analysis on all selected papers in the session.
        Note: The orchestrator handles the progress emitting, so this just processes.
        """
        selected = list(session.papers.values())
        
        for paper in selected:
            # Skip if already analyzed (e.g. from upload)
            if paper.id in session.analyses:
                continue
                
            try:
                analysis = await self._analyze_paper(paper)
                session.analyses[paper.id] = analysis
            except Exception as e:
                logger.warning(f"Analysis failed for {paper.title[:50]}: {e}")

        # Extract Claims & Evidence (Phase 5 in old pipeline)
        for analysis in session.analyses.values():
            # Avoid duplicating if already added
            for c in analysis.claims:
                if c not in session.claims:
                    session.claims.append(c)
            for e in analysis.evidence:
                if e not in session.evidence:
                    session.evidence.append(e)
            for m in analysis.methods:
                if m not in session.methods:
                    session.methods.append(m)

    async def _analyze_paper(self, paper) -> PaperAnalysis:
        full_text = ""
        if paper.sections:
            full_text = "\n".join(f"## {k}\n{v}" for k, v in paper.sections.items())

        prompt = PAPER_EXTRACTION_V1.format(
            title=paper.title,
            authors=", ".join(a.name for a in paper.authors[:5]),
            year=paper.year or "Unknown",
            venue=paper.venue or "Unknown",
            abstract=paper.abstract or "No abstract available",
            full_text_section=f"FULL TEXT:\n{full_text}" if full_text else "Full text not available."
        )
        analysis = await self.llm.structured_generate(prompt, PaperAnalysis, system_prompt=SYSTEM_PROMPT)
        analysis.paper_id = paper.id

        # Extract claims
        claims_prompt = CLAIM_EXTRACTION_V1.format(
            title=paper.title,
            abstract=paper.abstract or "",
            findings="\n".join(analysis.main_findings)
        )

        try:
            claims_result = await self.llm.structured_generate(claims_prompt, ClaimList, system_prompt=SYSTEM_PROMPT)
            for claim in claims_result.claims:
                claim.paper_id = paper.id
            analysis.claims = claims_result.claims
        except Exception as e:
            logger.warning(f"Claim extraction failed for {paper.title[:40]}: {e}")

        # Extract methods
        method_prompt = METHOD_EXTRACTION_V1.format(
            title=paper.title,
            abstract=paper.abstract or "",
            methods_section=paper.sections.get("methods", "Methods section not available")
        )
        try:
            method = await self.llm.structured_generate(method_prompt, MethodPipeline, system_prompt=SYSTEM_PROMPT)
            method.paper_id = paper.id
            analysis.methods = [method]
        except Exception as e:
            logger.warning(f"Method extraction failed for {paper.title[:40]}: {e}")

        return analysis
