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

    @property
    def description(self) -> str:
        return "Extracts structured scientific claims, methods, and quantitative evidence from literature."

    async def execute(self, session: ResearchSession, **kwargs) -> None:
        """
        Executes analysis on all selected papers in the session with truthful degradation tracking.
        """
        from backend.app.models.research import StageResult

        selected = list(session.papers.values())
        if not selected:
            self.record_stage(session, "analysis", StageResult.SKIPPED, "No papers available for analysis")
            return

        failed_papers = []
        for paper in selected:
            # Skip if already analyzed (e.g. from upload)
            if paper.id in session.analyses:
                continue
                
            try:
                analysis = await self._analyze_paper(paper)
                session.analyses[paper.id] = analysis
            except Exception as e:
                logger.warning(f"Analysis failed for {paper.title[:50]}: {e}")
                failed_papers.append(paper.id)

        # Extract Claims & Evidence
        for analysis in session.analyses.values():
            for c in analysis.claims:
                if c not in session.claims:
                    session.claims.append(c)
            for e in analysis.evidence:
                if e not in session.evidence:
                    session.evidence.append(e)
            for m in analysis.methods:
                if m not in session.methods:
                    session.methods.append(m)

        if len(session.analyses) == len(selected) and session.claims:
            self.record_stage(session, "analysis", StageResult.SUCCESS)
        elif len(session.analyses) > 0:
            self.record_stage(session, "analysis", StageResult.PARTIAL,
                              f"Analyzed {len(session.analyses)}/{len(selected)} papers ({len(failed_papers)} failed)")
        else:
            self.record_stage(session, "analysis", StageResult.FAILED,
                              "Zero papers could be successfully analyzed")

    async def _analyze_paper(self, paper) -> PaperAnalysis:
        from backend.app.models.research import Evidence, EvidenceConfidence

        # Build evidence-aware context from extracted sections
        if paper.sections:
            priority_sections = ["methods", "methodology", "experimental_setup", "results", "discussion", "limitations", "conclusion"]
            section_blocks = []
            for sec in priority_sections:
                if sec in paper.sections:
                    title_display = sec.replace("_", " ").upper()
                    section_blocks.append(f"### {title_display}\n{paper.sections[sec][:8000]}")
            
            # If no priority sections were detected, use general full_text slice
            if not section_blocks and "full_text" in paper.sections:
                section_blocks.append(f"### EXTRACTED TEXT\n{paper.sections['full_text'][:15000]}")

            status_header = f"[FULL TEXT ANALYZED — {paper.page_count or 'N/A'} Pages]" if paper.full_text_available else "[PARTIAL TEXT]"
            full_text = f"{status_header}\n\n" + "\n\n".join(section_blocks)
        else:
            full_text = "[ABSTRACT-ONLY ANALYSIS] Full text PDF was unavailable or not open access."

        prompt = PAPER_EXTRACTION_V1.format(
            title=paper.title,
            authors=", ".join(a.name for a in paper.authors[:5]),
            year=paper.year or "Unknown",
            venue=paper.venue or "Unknown",
            abstract=paper.abstract or "No abstract available",
            full_text_section=f"EXTRACTED CONTENT:\n{full_text}"
        )
        analysis = await self.llm.structured_generate(prompt, PaperAnalysis, system_prompt=SYSTEM_PROMPT, use_fast=True)
        analysis.paper_id = paper.id

        # Extract claims
        claims_prompt = CLAIM_EXTRACTION_V1.format(
            title=paper.title,
            abstract=paper.abstract or "",
            findings="\n".join(analysis.main_findings)
        )

        try:
            claims_result = await self.llm.structured_generate(claims_prompt, ClaimList, system_prompt=SYSTEM_PROMPT, use_fast=True)
            for claim in claims_result.claims:
                claim.paper_id = paper.id
                if not claim.source_section:
                    claim.source_section = "Results / Findings" if paper.full_text_available else "Abstract"
            analysis.claims = claims_result.claims
        except Exception as e:
            logger.warning(f"Claim extraction failed for {paper.title[:40]}: {e}")

        # Build grounded Evidence items for extracted claims to preserve provenance
        analysis.evidence = []
        for claim in analysis.claims:
            loc = f"{paper.title} [{claim.source_section or ('Full Text' if paper.full_text_available else 'Abstract')}]"
            ev = Evidence(
                claim_id=claim.id,
                paper_id=paper.id,
                evidence_type="empirical" if (claim.evidence_value or claim.metric) else "observational",
                description=f"{claim.statement}" + (f" ({claim.metric}: {claim.evidence_value})" if claim.evidence_value else ""),
                quantitative_value=claim.evidence_value,
                metric=claim.metric,
                conditions=claim.conditions,
                confidence=claim.confidence,
                source_location=loc
            )
            analysis.evidence.append(ev)

        # Extract methods
        methods_context = (
            paper.sections.get("methods")
            or paper.sections.get("methodology")
            or paper.sections.get("experimental_setup")
            or paper.abstract
            or "Methods section not available"
        )
        method_prompt = METHOD_EXTRACTION_V1.format(
            title=paper.title,
            abstract=paper.abstract or "",
            methods_section=methods_context[:10000]
        )
        try:
            method = await self.llm.structured_generate(method_prompt, MethodPipeline, system_prompt=SYSTEM_PROMPT, use_fast=True)
            method.paper_id = paper.id
            analysis.methods = [method]
        except Exception as e:
            logger.warning(f"Method extraction failed for {paper.title[:40]}: {e}")

        return analysis

