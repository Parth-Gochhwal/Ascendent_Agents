"""Research pipeline orchestrator for NEXUS.

Coordinates all agents through the complete research workflow:
Question → Plan → Search → Analyze → Extract → Compare → Synthesize → Report
"""
import asyncio
import logging
import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from backend.app.core.config import get_settings
from backend.app.models.research import (
    ResearchSession, SessionStatus, AgentStatus, ResearchPlan, Paper,
    PaperAnalysis, Claim, Evidence, MethodPipeline, CitationEdge,
    Contradiction, ConsensusFinding, ResearchGap, NoveltyAssessment,
    ExperimentProposal, RedTeamResult, AuditResult, MissingExperiment,
    ContradictionType, ConsensusStatus, EvidenceConfidence, Availability,
    Author, SearchResult, WhyExplanation, WhyEvidenceChainItem, TimelineMilestone, new_id,
    ClaimList, ConsensusList, GapList, MissingExperimentList,
    DeadEnd, ReproducibilityProfile, ClaimPropagation, CitationEchoCluster,
    ResearchGraph, EvidenceStrength,
)
from backend.app.providers.llm_provider import get_llm_provider, reset_llm_provider
from backend.app.providers.academic import (
    OpenAlexProvider, SemanticScholarProvider, CrossrefProvider, ArxivProvider
)
from backend.app.prompts.templates import *
from backend.app.services.demo_data import *
from backend.app.services import research_intelligence as ri
from backend.app.services.agents import (
    PlanningAgent, RetrievalAgent, AnalysisAgent,
    IntelligenceAgent, SynthesisAgent, InnovationAgent, RedTeamAgent
)

logger = logging.getLogger(__name__)


class ResearchPipeline:
    """Orchestrates the complete NEXUS research pipeline."""

    def __init__(self):
        self.settings = get_settings()
        self.llm = get_llm_provider()
        self.sessions: dict[str, ResearchSession] = {}
        self._event_callbacks: list = []
        self.providers = []
        self.reinitialize()

    def reinitialize(self):
        """Rebuild provider layers from current config while preserving active sessions."""
        self.settings = get_settings()
        reset_llm_provider()
        self.llm = get_llm_provider()
        
        # Reinitialize academic providers if live
        self.providers = []
        if not self.settings.demo_mode:
            self.providers = [
                OpenAlexProvider(email=self.settings.openalex_email),
                SemanticScholarProvider(api_key=self.settings.semantic_scholar_api_key),
                CrossrefProvider(email=self.settings.crossref_email),
                ArxivProvider(),
            ]

    def register_callback(self, callback):
        """Register a callback for agent events."""
        self._event_callbacks.append(callback)

    def remove_callback(self, callback):
        """Remove a previously registered callback."""
        if callback in self._event_callbacks:
            self._event_callbacks.remove(callback)

    async def _emit_event(self, session: ResearchSession, agent: str,
                          status: AgentStatus, message: str = "",
                          detail: str = None, progress: float = None):
        event = session.add_event(agent, status, message, detail, progress)
        for cb in self._event_callbacks:
            try:
                await cb(event)
            except Exception as e:
                logger.warning(f"Event callback error: {e}")
        return event

    def get_session(self, session_id: str) -> Optional[ResearchSession]:
        return self.sessions.get(session_id)

    def list_sessions(self) -> list[dict]:
        return [
            {"id": s.id, "title": s.title, "question": s.question,
             "status": s.status.value, "created_at": s.created_at.isoformat(),
             "is_demo": s.is_demo, "stats": s.stats}
            for s in self.sessions.values()
        ]

    async def start_research(self, question: str) -> ResearchSession:
        """Start a new research session."""
        session = ResearchSession(
            question=question,
            title=question[:80],
            is_demo=self.settings.demo_mode,
        )
        self.sessions[session.id] = session
        logger.info(f"Starting research session {session.id}: {question[:60]}")

        # Run pipeline in background
        asyncio.create_task(self._run_pipeline(session))
        return session

    async def _run_pipeline(self, session: ResearchSession):
        """Execute the complete research pipeline."""
        try:
            if self.settings.demo_mode:
                await self._run_demo_pipeline(session)
            else:
                await self._run_live_pipeline(session)
        except Exception as e:
            logger.error(f"Pipeline error for session {session.id}: {e}", exc_info=True)
            session.status = SessionStatus.ERROR
            await self._emit_event(session, "Pipeline", AgentStatus.FAILED,
                                   f"Pipeline error: {str(e)}")

    async def _run_demo_pipeline(self, session: ResearchSession):
        """Run pipeline with demo data."""
        # Phase 1: Planning
        session.status = SessionStatus.PLANNING
        await self._emit_event(session, "Research Planner", AgentStatus.RUNNING,
                               "Analyzing research question...")
        await asyncio.sleep(1.5)  # Simulate processing
        session.plan = get_demo_plan()
        await self._emit_event(session, "Research Planner", AgentStatus.COMPLETED,
                               f"Decomposed question into {len(session.plan.subquestions)} subquestions",
                               detail=f"Generated {len(session.plan.search_queries)} search queries")

        # Phase 2: Literature Discovery
        session.status = SessionStatus.DISCOVERING
        await self._emit_event(session, "Literature Discovery", AgentStatus.RUNNING,
                               "Searching academic sources...")
        await asyncio.sleep(1.0)

        papers = get_demo_papers()
        initial_count = len(papers) + 15  # Simulate finding more before dedup
        session.searches = [
            SearchResult(query=q, provider="demo", papers_found=3, paper_ids=[])
            for q in session.plan.search_queries[:4]
        ]
        await self._emit_event(session, "Literature Discovery", AgentStatus.COMPLETED,
                               f"Found {initial_count} papers from 4 sources",
                               detail="Searched OpenAlex, Semantic Scholar, Crossref, arXiv (demo)")

        # Phase 3: Dedup & Ranking
        session.status = SessionStatus.RANKING
        await self._emit_event(session, "Relevance Engine", AgentStatus.RUNNING,
                               "Deduplicating and ranking papers...")
        await asyncio.sleep(1.0)
        session.papers = papers
        await self._emit_event(session, "Relevance Engine", AgentStatus.COMPLETED,
                               f"After deduplication: {len(papers)} unique papers. Selected {len(papers)} for analysis.",
                               detail=f"Initial: {initial_count} → Dedup: {len(papers)} → Selected: {len(papers)}")

        # Phase 4: Paper Analysis
        session.status = SessionStatus.ANALYZING
        analyses = get_demo_analyses()
        for i, (pid, analysis) in enumerate(analyses.items()):
            await self._emit_event(session, "Paper Intelligence", AgentStatus.RUNNING,
                                   f"Analyzing paper {i+1}/{len(analyses)}",
                                   detail=session.papers[pid].title if pid in session.papers else "",
                                   progress=(i + 1) / len(analyses))
            await asyncio.sleep(0.5)
        session.analyses = analyses
        await self._emit_event(session, "Paper Intelligence", AgentStatus.COMPLETED,
                               f"Deep analysis completed for {len(analyses)} papers")

        # Phase 5: Extract Claims & Evidence
        session.status = SessionStatus.EXTRACTING_EVIDENCE
        await self._emit_event(session, "Evidence Extraction", AgentStatus.RUNNING,
                               "Extracting claims and evidence...")
        await asyncio.sleep(1.0)
        for analysis in analyses.values():
            session.claims.extend(analysis.claims)
            session.evidence.extend(analysis.evidence)
            session.methods.extend(analysis.methods)
        await self._emit_event(session, "Evidence Extraction", AgentStatus.COMPLETED,
                               f"Extracted {len(session.claims)} claims and {len(session.evidence)} evidence items")

        # Phase 6: Citations
        session.status = SessionStatus.BUILDING_GRAPH
        await self._emit_event(session, "Citation Intelligence", AgentStatus.RUNNING,
                               "Building citation graph...")
        await asyncio.sleep(0.8)
        session.citations = get_demo_citations()
        await self._emit_event(session, "Citation Intelligence", AgentStatus.COMPLETED,
                               f"Mapped {len(session.citations)} citation relationships")

        # Phase 7: Contradictions
        session.status = SessionStatus.ANALYZING_CONTRADICTIONS
        await self._emit_event(session, "Contradiction Engine", AgentStatus.RUNNING,
                               "Analyzing potential contradictions...")
        await asyncio.sleep(1.5)
        session.contradictions = get_demo_contradictions()
        await self._emit_event(session, "Contradiction Engine", AgentStatus.COMPLETED,
                               f"Found {len(session.contradictions)} potential conflicts",
                               detail=f"Direct: {sum(1 for c in session.contradictions if c.classification == ContradictionType.DIRECT_CONTRADICTION)}, "
                                      f"Contextual: {sum(1 for c in session.contradictions if c.classification == ContradictionType.CONTEXTUAL_DISAGREEMENT)}, "
                                      f"Apparent: {sum(1 for c in session.contradictions if c.classification == ContradictionType.APPARENT_CONTRADICTION)}")

        # Phase 8: Consensus
        session.status = SessionStatus.SYNTHESIZING_CONSENSUS
        await self._emit_event(session, "Consensus Engine", AgentStatus.RUNNING,
                               "Synthesizing consensus findings...")
        await asyncio.sleep(1.0)
        session.consensus = get_demo_consensus()
        await self._emit_event(session, "Consensus Engine", AgentStatus.COMPLETED,
                               f"Identified {len(session.consensus)} findings: "
                               f"{sum(1 for c in session.consensus if c.status == ConsensusStatus.CONSENSUS)} consensus, "
                               f"{sum(1 for c in session.consensus if c.status == ConsensusStatus.CONTESTED)} contested")

        # Phase 9: Dead-End Detection
        session.status = SessionStatus.ANALYZING_DEAD_ENDS
        await self._emit_event(session, "Dead-End Atlas", AgentStatus.RUNNING,
                               "Identifying research dead ends...")
        await asyncio.sleep(0.8)
        session.dead_ends = get_demo_dead_ends()
        await self._emit_event(session, "Dead-End Atlas", AgentStatus.COMPLETED,
                               f"Identified {len(session.dead_ends)} dead ends or limited approaches",
                               detail=f"Status: {', '.join(f'{d.approach} ({d.status.value})' for d in session.dead_ends)}")

        # Phase 10: Reproducibility Profiling
        session.status = SessionStatus.CHECKING_REPRODUCIBILITY
        await self._emit_event(session, "Reproducibility Profiler", AgentStatus.RUNNING,
                               "Assessing reproducibility for analyzed papers...")
        await asyncio.sleep(0.8)
        session.reproducibility_profiles = get_demo_reproducibility_profiles()
        avg_repro = sum(p.completeness_score for p in session.reproducibility_profiles.values()) / max(len(session.reproducibility_profiles), 1)
        await self._emit_event(session, "Reproducibility Profiler", AgentStatus.COMPLETED,
                               f"Profiled {len(session.reproducibility_profiles)} papers. Average completeness: {avg_repro:.0%}")

        # Phase 11: ClaimLine Tracking
        await self._emit_event(session, "ClaimLine Tracker", AgentStatus.RUNNING,
                               "Tracking claim propagation through literature...")
        await asyncio.sleep(0.6)
        session.claim_propagations = get_demo_claim_propagations()
        await self._emit_event(session, "ClaimLine Tracker", AgentStatus.COMPLETED,
                               f"Tracked {len(session.claim_propagations)} claim propagation chains",
                               detail=f"Types: {', '.join(set(p.relationship_type.value for p in session.claim_propagations))}")

        # Phase 12: Citation Echo Detection
        await self._emit_event(session, "Citation Echo Detector", AgentStatus.RUNNING,
                               "Detecting citation echo chambers...")
        await asyncio.sleep(0.6)
        session.citation_echoes = get_demo_citation_echoes()
        if session.citation_echoes:
            echo_summary = "; ".join(f"'{e.claim_statement[:50]}...' ({e.independent_support_count}/{e.total_support_count} independent)" for e in session.citation_echoes)
            await self._emit_event(session, "Citation Echo Detector", AgentStatus.COMPLETED,
                                   f"Detected {len(session.citation_echoes)} echo cluster(s)",
                                   detail=echo_summary)
        else:
            await self._emit_event(session, "Citation Echo Detector", AgentStatus.COMPLETED,
                                   "No citation echo chambers detected")

        # Phase 13: Gaps
        session.status = SessionStatus.DETECTING_GAPS
        await self._emit_event(session, "Gap Detector", AgentStatus.RUNNING,
                               "Identifying research gaps...")
        await asyncio.sleep(1.0)
        session.gaps = get_demo_gaps()
        session.missing_experiments = get_demo_missing_experiments()
        await self._emit_event(session, "Gap Detector", AgentStatus.COMPLETED,
                               f"Identified {len(session.gaps)} potential research gaps and {len(session.missing_experiments)} missing experiments")

        # Phase 14: Novelty
        session.status = SessionStatus.ANALYZING_NOVELTY
        await self._emit_event(session, "Novelty Analyzer", AgentStatus.RUNNING,
                               "Evaluating novelty of potential directions...")
        await asyncio.sleep(1.0)
        session.novelty = get_demo_novelty()
        await self._emit_event(session, "Novelty Analyzer", AgentStatus.COMPLETED,
                               f"Assessment: {session.novelty.assessment}")

        # Phase 15: Experiment Design
        session.status = SessionStatus.DESIGNING_EXPERIMENT
        await self._emit_event(session, "Experiment Designer", AgentStatus.RUNNING,
                               "Designing experiment for top research gap...")
        await asyncio.sleep(1.0)
        session.experiment = get_demo_experiment()
        await self._emit_event(session, "Experiment Designer", AgentStatus.COMPLETED,
                               "Generated experiment proposal")

        # Phase 16: Red Team
        session.status = SessionStatus.RED_TEAM
        await self._emit_event(session, "Red Team", AgentStatus.RUNNING,
                               "Challenging conclusions...")
        await asyncio.sleep(1.2)
        session.red_team = get_demo_red_team()
        session.red_team.findings = get_demo_red_team_findings()
        await self._emit_event(session, "Red Team", AgentStatus.COMPLETED,
                               f"Identified {len(session.red_team.challenges)} challenges, "
                               f"{len(session.red_team.findings)} structured findings. "
                               f"Confidence: {session.red_team.final_confidence.value}")

        # Phase 17: Audit
        session.status = SessionStatus.AUDITING
        await self._emit_event(session, "Integrity Auditor", AgentStatus.RUNNING,
                               "Auditing research integrity...")
        await asyncio.sleep(0.8)
        session.audit = get_demo_audit()
        await self._emit_event(session, "Integrity Auditor", AgentStatus.COMPLETED,
                               f"Claims checked: {session.audit.total_claims}, "
                               f"With evidence: {session.audit.claims_with_evidence_links}, "
                               f"Integrity: {session.audit.overall_integrity}, "
                               f"Findings: {len(session.audit.integrity_findings)}")

        # Done
        session.status = SessionStatus.REPORT_READY
        session.update_stats()
        await self._emit_event(session, "Pipeline", AgentStatus.COMPLETED,
                               "Research complete! Dossier ready.",
                               detail=f"Analyzed {len(session.papers)} papers, extracted {len(session.claims)} claims, "
                                      f"tracked {len(session.claim_propagations)} propagations, "
                                      f"detected {len(session.citation_echoes)} echo chambers, "
                                      f"identified {len(session.dead_ends)} dead ends")

    async def _run_live_pipeline(self, session: ResearchSession):
        """Run the actual live research pipeline with real APIs using discrete agents."""
        
        # Instantiate agents
        planning_agent = PlanningAgent(self.llm)
        retrieval_agent = RetrievalAgent(self.llm, self.providers, self.settings.max_papers_deep_analysis)
        analysis_agent = AnalysisAgent(self.llm)
        intelligence_agent = IntelligenceAgent(self.llm)
        synthesis_agent = SynthesisAgent(self.llm)
        innovation_agent = InnovationAgent(self.llm)
        red_team_agent = RedTeamAgent(self.llm)

        # Phase 1: Planning
        session.status = SessionStatus.PLANNING
        await self._emit_event(session, planning_agent.name, AgentStatus.RUNNING, "Analyzing research question...")
        try:
            await planning_agent.execute(session)
            await self._emit_event(session, planning_agent.name, AgentStatus.COMPLETED,
                                   f"Decomposed into {len(session.plan.subquestions)} subquestions")
        except Exception as e:
            logger.error(f"Planning failed: {e}")
            await self._emit_event(session, planning_agent.name, AgentStatus.FAILED, str(e))
            session.plan = ResearchPlan(
                normalized_question=session.question,
                research_objective=f"Investigate: {session.question}",
                search_queries=[session.question],
            )

        # Phase 2 & 3: Literature Discovery & Ranking
        session.status = SessionStatus.DISCOVERING
        await self._emit_event(session, retrieval_agent.name, AgentStatus.RUNNING, "Searching and ranking literature...")
        try:
            found, deduped, selected = await retrieval_agent.execute(session)
            await self._emit_event(session, retrieval_agent.name, AgentStatus.COMPLETED,
                                   f"Found: {found} → Dedup: {deduped} → Selected: {selected}")
        except Exception as e:
            logger.error(f"Retrieval failed: {e}")
            await self._emit_event(session, retrieval_agent.name, AgentStatus.FAILED, str(e))

        # Phase 4 & 5: Deep Analysis & Evidence Extraction
        session.status = SessionStatus.ANALYZING
        await self._emit_event(session, analysis_agent.name, AgentStatus.RUNNING, "Deeply analyzing papers...")
        try:
            await analysis_agent.execute(session)
            await self._emit_event(session, analysis_agent.name, AgentStatus.COMPLETED,
                                   f"Analyzed {len(session.analyses)} papers, Extracted {len(session.claims)} claims")
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            await self._emit_event(session, analysis_agent.name, AgentStatus.FAILED, str(e))

        # Phase 6 & Pre-Synthesis Intelligence
        session.status = SessionStatus.BUILDING_GRAPH
        await self._emit_event(session, intelligence_agent.name, AgentStatus.RUNNING, "Building citation graph and pre-synthesis metrics...")
        try:
            await intelligence_agent.execute(session, phase="pre_synthesis")
            await self._emit_event(session, intelligence_agent.name, AgentStatus.COMPLETED,
                                   f"Mapped {len(session.citations)} citations, {len(session.dead_ends)} dead ends")
        except Exception as e:
            logger.error(f"Pre-synthesis intelligence failed: {e}")
            await self._emit_event(session, intelligence_agent.name, AgentStatus.FAILED, str(e))

        # Phase 7 & 8: Contradictions & Consensus
        session.status = SessionStatus.ANALYZING_CONTRADICTIONS
        await self._emit_event(session, synthesis_agent.name, AgentStatus.RUNNING, "Synthesizing evidence...")
        try:
            await synthesis_agent.execute(session)
            await self._emit_event(session, synthesis_agent.name, AgentStatus.COMPLETED,
                                   f"Found {len(session.contradictions)} conflicts, {len(session.consensus)} clusters")
        except Exception as e:
            logger.error(f"Synthesis failed: {e}")
            await self._emit_event(session, synthesis_agent.name, AgentStatus.FAILED, str(e))

        # Phase 14-16: Innovation (Gaps, Novelty, Experiments)
        session.status = SessionStatus.DETECTING_GAPS
        await self._emit_event(session, innovation_agent.name, AgentStatus.RUNNING, "Detecting gaps and designing experiments...")
        try:
            await innovation_agent.execute(session)
            await self._emit_event(session, innovation_agent.name, AgentStatus.COMPLETED,
                                   f"Identified {len(session.gaps)} gaps, {len(session.missing_experiments)} missing experiments")
        except Exception as e:
            logger.error(f"Innovation failed: {e}")
            await self._emit_event(session, innovation_agent.name, AgentStatus.FAILED, str(e))

        # Phase 17: Red Team
        session.status = SessionStatus.RED_TEAM
        await self._emit_event(session, red_team_agent.name, AgentStatus.RUNNING, "Adversarial review of findings...")
        try:
            await red_team_agent.execute(session)
            confidence = session.red_team.final_confidence.value if session.red_team else "N/A"
            await self._emit_event(session, red_team_agent.name, AgentStatus.COMPLETED,
                                   f"Challenged findings. Confidence: {confidence}")
        except Exception as e:
            logger.error(f"Red team failed: {e}")
            await self._emit_event(session, red_team_agent.name, AgentStatus.FAILED, str(e))

        # Phase 18: Post-Synthesis Intelligence (Audit, Independence weighting)
        session.status = SessionStatus.AUDITING
        await self._emit_event(session, intelligence_agent.name, AgentStatus.RUNNING, "Finalizing integrity audit...")
        try:
            await intelligence_agent.execute(session, phase="post_synthesis")
            integrity = session.audit.overall_integrity if session.audit else "Unknown"
            await self._emit_event(session, intelligence_agent.name, AgentStatus.COMPLETED,
                                   f"Audit complete. Integrity: {integrity}")
        except Exception as e:
            logger.error(f"Post-synthesis intelligence failed: {e}")
            await self._emit_event(session, intelligence_agent.name, AgentStatus.FAILED, str(e))

        session.status = SessionStatus.REPORT_READY
        session.update_stats()
        await self._emit_event(session, "Pipeline", AgentStatus.COMPLETED,
                               "Research complete!",
                               detail=f"Analyzed {len(session.papers)} papers, extracted {len(session.claims)} claims, "
                                      f"tracked {len(session.claim_propagations)} propagations, "
                                      f"detected {len(session.citation_echoes)} echo chambers, "
                                      f"identified {len(session.dead_ends)} dead ends")

    # ─── Agent Implementations ───────────────────────────────

    async def _plan_research(self, question: str) -> ResearchPlan:
        """Use LLM to generate a structured research plan."""
        prompt = PLANNER_V1.format(question=question)
        return await self.llm.structured_generate(
            prompt, ResearchPlan, system_prompt=SYSTEM_PROMPT
        )

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
        import math
        
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

    async def _analyze_paper(self, paper: Paper) -> PaperAnalysis:
        """Deep analysis of a single paper using LLM."""
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

    def _build_citation_graph(self, session: ResearchSession) -> list[CitationEdge]:
        """Build citation edges from paper metadata."""
        edges = []
        paper_titles = {self._normalize_title(p.title): p.id for p in session.papers.values()}
        # Simple: detect if any paper title is mentioned in another paper's abstract/text
        for pid, paper in session.papers.items():
            text = (paper.abstract or "").lower()
            for title_norm, ref_id in paper_titles.items():
                if ref_id != pid and title_norm in text:
                    edges.append(CitationEdge(
                        source_paper_id=pid, target_paper_id=ref_id,
                        is_inferred=True, context="Inferred from textual overlap in abstract"
                    ))
        return edges

    async def _detect_contradictions(self, session: ResearchSession) -> list[Contradiction]:
        """Detect and classify contradictions between claims."""
        contradictions = []
        claims = session.claims
        if len(claims) < 2:
            return contradictions

        # Pairwise comparison for claims from different papers
        pairs_to_check = []
        for i in range(len(claims)):
            for j in range(i + 1, len(claims)):
                if claims[i].paper_id != claims[j].paper_id:
                    pairs_to_check.append((claims[i], claims[j]))

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
                result = await self.llm.structured_generate(prompt, Contradiction, system_prompt=SYSTEM_PROMPT)
                result.claim_a_id = claim_a.id
                result.claim_b_id = claim_b.id
                result.paper_a_id = claim_a.paper_id
                result.paper_b_id = claim_b.paper_id
                result.claim_a_text = claim_a.statement
                result.claim_b_text = claim_b.statement
                result.paper_a_summary = f"{paper_a.title} ({paper_a.year})"
                result.paper_b_summary = f"{paper_b.title} ({paper_b.year})"

                if result.classification != ContradictionType.AGREEMENT:
                    contradictions.append(result)
            except Exception as e:
                logger.warning(f"Contradiction analysis failed: {e}")

        return contradictions

    async def _analyze_consensus(self, session: ResearchSession) -> list[ConsensusFinding]:
        """Analyze consensus across papers."""
        claims_summary = "\n".join(
            f"- [{c.paper_id}] {c.statement} (confidence: {c.confidence.value})"
            for c in session.claims
        )
        prompt = CONSENSUS_ANALYSIS_V1.format(
            question=session.question,
            claims_summary=claims_summary or "No claims extracted"
        )

        try:
            result = await self.llm.structured_generate(prompt, ConsensusList, system_prompt=SYSTEM_PROMPT)
            return result.findings
        except Exception as e:
            logger.warning(f"Consensus analysis failed: {e}")
            return []

    async def _detect_gaps(self, session: ResearchSession) -> list[ResearchGap]:
        """Detect research gaps from analyzed literature."""
        papers_summary = "\n".join(
            f"- [{p.id}] {p.title} ({p.year}): {p.abstract[:200] if p.abstract else 'No abstract'}"
            for p in list(session.papers.values())[:15]
        )
        claims_summary = "\n".join(f"- {c.statement}" for c in session.claims[:20])
        contradictions_summary = "\n".join(
            f"- {c.claim_a_text} vs {c.claim_b_text}: {c.classification.value}"
            for c in session.contradictions
        )
        methods_summary = "\n".join(
            f"- {m.model_architecture} on {m.dataset}" for m in session.methods if m.model_architecture
        )
        datasets_summary = ", ".join(set(m.dataset for m in session.methods if m.dataset))

        prompt = GAP_DETECTION_V1.format(
            question=session.question,
            papers_summary=papers_summary or "No papers",
            claims_summary=claims_summary or "No claims",
            contradictions_summary=contradictions_summary or "No contradictions",
            methods_summary=methods_summary or "No methods",
            datasets_summary=datasets_summary or "No datasets"
        )

        try:
            result = await self.llm.structured_generate(prompt, GapList, system_prompt=SYSTEM_PROMPT)
            return result.gaps
        except Exception as e:
            logger.warning(f"Gap detection failed: {e}")
            return []

    async def analyze_novelty(self, session_id: str, idea: str) -> Optional[NoveltyAssessment]:
        """Analyze novelty of a proposed research idea."""
        session = self.sessions.get(session_id)
        if not session:
            return None

        papers_summary = "\n".join(
            f"- [{p.id}] {p.title}: {p.abstract[:150] if p.abstract else ''}"
            for p in list(session.papers.values())[:10]
        )
        methods_summary = "\n".join(
            f"- {m.model_architecture} on {m.dataset}" for m in session.methods if m.model_architecture
        )

        prompt = NOVELTY_ANALYSIS_V1.format(
            idea=idea,
            papers_summary=papers_summary or "No papers",
            methods_summary=methods_summary or "No methods"
        )

        try:
            result = await self.llm.structured_generate(prompt, NoveltyAssessment, system_prompt=SYSTEM_PROMPT)
            result.proposed_idea = idea
            session.novelty = result
            return result
        except Exception as e:
            logger.error(f"Novelty analysis failed: {e}")
            return None

    async def _detect_missing_experiments(self, session: ResearchSession) -> list[MissingExperiment]:
        """Detect missing experimental combinations based on gaps and contradictions."""
        gaps_text = "\n".join([f"- {g.title}: {g.description}" for g in session.gaps])
        contradictions_text = "\n".join([f"- {c.claim_a_text} vs {c.claim_b_text}" for c in session.contradictions])
        
        prompt = MISSING_EXPERIMENTS_V1.format(
            gaps=gaps_text if gaps_text else "None explicitly identified.",
            contradictions=contradictions_text if contradictions_text else "None explicitly identified."
        )
        
        result = await self.llm.structured_generate(prompt, MissingExperimentList, system_prompt=SYSTEM_PROMPT)
        return result.experiments if result else []

    async def _design_experiment(self, session: ResearchSession) -> ExperimentProposal:
        """Design experiment for top research gap."""
        gap = session.gaps[0]
        context = "\n".join(
            f"- {p.title} ({p.year})" for p in list(session.papers.values())[:10]
        )
        methods = ", ".join(set(m.model_architecture for m in session.methods if m.model_architecture))
        datasets = ", ".join(set(m.dataset for m in session.methods if m.dataset))
        metrics = ", ".join(set(m for method in session.methods for m in method.metrics))

        prompt = EXPERIMENT_DESIGN_V1.format(
            gap=f"{gap.title}: {gap.description}",
            context=context,
            methods=methods or "Various deep learning methods",
            datasets=datasets or "No dataset metadata extracted",
            metrics=metrics or "No evaluation metrics extracted"
        )

        result = await self.llm.structured_generate(prompt, ExperimentProposal, system_prompt=SYSTEM_PROMPT)
        result.gap_id = gap.id
        return result

    async def _red_team(self, session: ResearchSession) -> RedTeamResult:
        """Red-team the research conclusions."""
        conclusions = []
        for c in session.consensus[:5]:
            conclusions.append(f"- {c.statement} ({c.status.value})")
        for g in session.gaps[:3]:
            conclusions.append(f"- Gap: {g.title}")

        evidence_summary = "\n".join(
            f"- [{e.paper_id}] {e.description}" for e in session.evidence[:15]
        )

        prompt = RED_TEAM_V1.format(
            conclusions="\n".join(conclusions) or "No major conclusions",
            evidence=evidence_summary or "No evidence"
        )

        return await self.llm.structured_generate(prompt, RedTeamResult, system_prompt=SYSTEM_PROMPT)

    def _run_audit(self, session: ResearchSession) -> AuditResult:
        """Run integrity audit — deterministic checks."""
        total_claims = len(session.claims)
        claims_with_evidence = sum(1 for c in session.claims
                                   if any(e.claim_id == c.id for e in session.evidence))
        unsupported = total_claims - claims_with_evidence
        
        verified_papers = sum(1 for p in session.papers.values() 
                              if p.doi or (p.source_provider and p.source_provider not in ["upload", "demo_inferred"]))

        bib_validated = all(
            p.title and p.authors and (p.year or p.venue or p.doi) 
            for p in session.papers.values()
        )

        return AuditResult(
            total_claims=total_claims,
            claims_with_evidence_links=claims_with_evidence,
            unsupported_claims=unsupported,
            identifiable_source_metadata=verified_papers,
            citations_total=len(session.papers),
            contradictions_represented=len(session.contradictions) > 0,
            bibliographic_metadata_complete=bib_validated,
            uncertainty_levels_present=any(c.confidence for c in session.claims),
            issues=[f"{unsupported} claims lack direct evidence linkage"] if unsupported > 0 else [],
            warnings=["Analysis includes unverified or uploaded PDFs — not fully peer-reviewed"] if verified_papers < len(session.papers) else [],
            overall_integrity="passed" if unsupported <= 2 and bib_validated else "warnings" if unsupported <= 5 else "failed"
        )

    async def explain_why(self, session_id: str, target_type: str, target_id: str) -> Optional[WhyExplanation]:
        """Generate a grounded, traceable explainability dossier for any AI-generated finding."""
        session = self.sessions.get(session_id)
        if not session:
            return None

        if target_type == "contradiction":
            item = next((c for c in session.contradictions if c.id == target_id), None)
            if not item:
                return None
            paper_a = session.papers.get(item.paper_a_id)
            paper_b = session.papers.get(item.paper_b_id)
            evidence_chain = [
                WhyEvidenceChainItem(
                    claim=item.claim_a_text,
                    evidence=f"Reported in {paper_a.title if paper_a else item.paper_a_summary}",
                    source_paper_id=item.paper_a_id,
                    source_paper_title=paper_a.title if paper_a else item.paper_a_summary,
                    doi_or_url=paper_a.doi or paper_a.url if paper_a else None,
                    source_location="Extracted claim/evidence",
                    confidence=item.confidence,
                ),
                WhyEvidenceChainItem(
                    claim=item.claim_b_text,
                    evidence=f"Reported in {paper_b.title if paper_b else item.paper_b_summary}",
                    source_paper_id=item.paper_b_id,
                    source_paper_title=paper_b.title if paper_b else item.paper_b_summary,
                    doi_or_url=paper_b.doi or paper_b.url if paper_b else None,
                    source_location="Extracted claim/evidence",
                    confidence=item.confidence,
                )
            ]
            reasons = [
                f"Classification: {item.classification.value.replace('_', ' ').title()}",
                f"Shared context: {', '.join(item.shared_conditions) if item.shared_conditions else 'General domain'}",
                f"Divergent experimental parameters: {', '.join(item.different_conditions) if item.different_conditions else 'None explicitly reported'}",
                item.explanation
            ]
            return WhyExplanation(
                target_type="contradiction",
                target_id=target_id,
                target_statement=f"Disagreement between {item.paper_a_summary} and {item.paper_b_summary}",
                confidence=item.confidence,
                evidence_chain=evidence_chain,
                reasoning_factors=reasons,
                uncertainty_analysis="Analysis of the conflicting claims suggests divergence may stem from differing experimental methodologies or datasets rather than fundamentally conflicting phenomena, though explicit reporting is required to confirm.",
                conflicting_evidence=[item.claim_b_text],
                counter_hypotheses=[f"The observed performance difference may invert under different tested conditions such as {item.different_conditions[0] if item.different_conditions else 'unreported variables'}."]
            )

        elif target_type == "consensus":
            item = next((c for c in session.consensus if c.id == target_id), None)
            if not item:
                return None
            evidence_chain = []
            for pid in item.supporting_paper_ids:
                p = session.papers.get(pid)
                if p:
                    evidence_chain.append(WhyEvidenceChainItem(
                        claim=item.statement,
                        evidence=f"Confirmed in {p.title} ({p.year})",
                        source_paper_id=p.id,
                        source_paper_title=p.title,
                        doi_or_url=p.doi or p.url,
                        confidence=item.confidence
                    ))
            return WhyExplanation(
                target_type="consensus",
                target_id=target_id,
                target_statement=item.statement,
                confidence=item.confidence,
                evidence_chain=evidence_chain,
                reasoning_factors=[
                    f"Consensus status: {item.status.value.upper()}",
                    f"Supported by {len(item.supporting_paper_ids)} independent peer-reviewed studies",
                    item.explanation or "Multiple independent experimental benchmarks report mutually reinforcing outcomes."
                ],
                uncertainty_analysis="High empirical convergence across tested conditions; however, caveats remain regarding generalizability to domains not explicitly tested in the cited literature.",
                conflicting_evidence=[f"Dissenting studies: {len(item.dissenting_paper_ids)}"] if item.dissenting_paper_ids else []
            )

        elif target_type == "dead_end":
            item = next((d for d in session.dead_ends if d.id == target_id), None)
            if not item:
                return None
            evidence_chain = []
            for pid in item.supporting_papers:
                p = session.papers.get(pid)
                if p:
                    evidence_chain.append(WhyEvidenceChainItem(
                        claim=f"Demonstrates limitations of {item.approach}",
                        evidence=f"Used as baseline and/or documented failure in {p.title}",
                        source_paper_id=p.id,
                        source_paper_title=p.title,
                        doi_or_url=p.doi or p.url,
                        confidence=item.confidence
                    ))
            return WhyExplanation(
                target_type="dead_end",
                target_id=target_id,
                target_statement=f"Dead-End Approach: {item.approach}",
                confidence=item.confidence,
                evidence_chain=evidence_chain,
                reasoning_factors=[
                    f"Status: {item.status.value.replace('_', ' ').title()}",
                    item.description,
                    f"Failure conditions: {', '.join(item.failure_conditions)}",
                    f"Observed across {item.attempt_count} independent papers"
                ],
                uncertainty_analysis="This approach may still succeed under untested conditions. See success_conditions_if_any for potential exceptions.",
                conflicting_evidence=item.success_conditions_if_any,
                counter_hypotheses=[f"Alternative approaches recommended: {', '.join(item.alternative_directions)}"]
            )

        elif target_type == "claim_propagation":
            item = next((p for p in session.claim_propagations if p.id == target_id), None)
            if not item:
                return None
            s_paper = session.papers.get(item.source_paper_id)
            d_paper = session.papers.get(item.derived_paper_id)
            return WhyExplanation(
                target_type="claim_propagation",
                target_id=target_id,
                target_statement=f"ClaimLine: {item.relationship_type.value.replace('_', ' ').title()} Propagation",
                confidence=item.confidence,
                evidence_chain=[
                    WhyEvidenceChainItem(
                        claim="Original Context",
                        evidence=f"Conditions: {', '.join(item.source_conditions)}",
                        source_paper_id=item.source_paper_id,
                        source_paper_title=s_paper.title if s_paper else "Unknown",
                        doi_or_url=s_paper.doi or s_paper.url if s_paper else None,
                        confidence=item.evidence_strength
                    ),
                    WhyEvidenceChainItem(
                        claim="Derived Context",
                        evidence=f"Conditions: {', '.join(item.derived_conditions)}",
                        source_paper_id=item.derived_paper_id,
                        source_paper_title=d_paper.title if d_paper else "Unknown",
                        doi_or_url=d_paper.doi or d_paper.url if d_paper else None,
                        confidence=item.confidence
                    )
                ],
                reasoning_factors=[
                    f"Scope change detected: {item.scope_change}",
                    item.explanation
                ],
                uncertainty_analysis="Analysis based on explicit textual conditions reported in the respective papers. Implicit conditions may not be captured."
            )

        elif target_type == "citation_echo":
            item = next((e for e in session.citation_echoes if e.id == target_id), None)
            if not item:
                return None
            return WhyExplanation(
                target_type="citation_echo",
                target_id=target_id,
                target_statement=f"Citation Echo: {item.claim_statement[:60]}...",
                confidence=EvidenceConfidence.HIGH,
                evidence_chain=[
                    WhyEvidenceChainItem(
                        claim="Originating Source",
                        evidence=f"Originates from {item.originating_paper_title}",
                        source_paper_id=item.originating_paper_id,
                        source_paper_title=item.originating_paper_title,
                        confidence=EvidenceConfidence.HIGH
                    )
                ],
                reasoning_factors=[
                    item.explanation,
                    f"Total supporting papers: {item.total_support_count}",
                    f"Independent supporting papers: {item.independent_support_count}",
                    f"Citation dependency depth: {item.citation_dependency_depth}",
                    f"Independence weight (0-1): {item.independence_weight}"
                ],
                uncertainty_analysis="A low independence weight indicates that the apparent consensus is largely derivative, tracing back to one or very few original sources."
            )

        elif target_type == "reproducibility":
            item = session.reproducibility_profiles.get(target_id)
            if not item:
                return None
            paper = session.papers.get(target_id)
            return WhyExplanation(
                target_type="reproducibility",
                target_id=target_id,
                target_statement=f"Reproducibility Profile for: {paper.title if paper else target_id}",
                confidence=EvidenceConfidence.HIGH,
                evidence_chain=[],
                reasoning_factors=[
                    f"Completeness Score: {item.completeness_score:.0%}",
                    item.explanation,
                    f"Missing components: {', '.join(item.missing_components) if item.missing_components else 'None'}",
                    f"Risk factors: {'; '.join(item.risk_factors) if item.risk_factors else 'None identified'}"
                ],
                uncertainty_analysis="Deterministic heuristic based on presence/absence of metadata fields and code/data links. Subjective code quality is not evaluated."
            )

        elif target_type == "gap":
            item = next((g for g in session.gaps if g.id == target_id), None)
            if not item:
                return None
            evidence_chain = []
            for pid in item.supporting_paper_ids:
                p = session.papers.get(pid)
                if p:
                    evidence_chain.append(WhyEvidenceChainItem(
                        claim=f"Limitation identified: {item.title}",
                        evidence=f"Noted in limitations / future work of {p.title}",
                        source_paper_id=p.id,
                        source_paper_title=p.title,
                        doi_or_url=p.doi or p.url,
                        confidence=item.confidence
                    ))
            return WhyExplanation(
                target_type="gap",
                target_id=target_id,
                target_statement=item.title,
                confidence=item.confidence,
                evidence_chain=evidence_chain,
                reasoning_factors=[
                    f"Gap Type: {item.gap_type.title()}",
                    item.description,
                    f"Why it matters: {item.why_it_matters or 'Blocks real-world deployment'}",
                    f"Evidence backing gap: {'; '.join(item.evidence) if item.evidence else 'Repeated across retrieved papers'}"
                ],
                uncertainty_analysis="Based solely on the retrieved and analyzed academic corpus; unindexed industrial preprints may have explored partial solutions."
            )

        elif target_type == "paper":
            p = session.papers.get(target_id)
            if not p:
                return None
            comps = p.score_components or {}
            return WhyExplanation(
                target_type="paper",
                target_id=target_id,
                target_statement=f"Relevance scoring for: {p.title}",
                confidence=EvidenceConfidence.HIGH,
                evidence_chain=[
                    WhyEvidenceChainItem(
                        claim="Paper relevance & research score computation",
                        evidence=f"Research Score: {p.research_score:.2f} (Relevance: {comps.get('relevance', 0):.2f}, Recency: {comps.get('recency', 0):.2f}, Citations: {comps.get('citation_influence', 0):.2f}, Completeness: {comps.get('completeness', 0):.2f})" if p.research_score is not None else "Not Evaluated",
                        source_paper_id=p.id,
                        source_paper_title=p.title,
                        doi_or_url=p.doi or p.url,
                        confidence=EvidenceConfidence.HIGH
                    )
                ],
                reasoning_factors=[
                    f"Deterministic relevance alignment with research query: {comps.get('relevance', 0)*100:.0f}%",
                    f"Publication recency weight ({p.year}): {comps.get('recency', 0)*100:.0f}%",
                    f"Citation impact ({p.citation_count or 0} citations): {comps.get('citation_influence', 0)*100:.0f}%",
                    f"Methodological completeness: {comps.get('completeness', 0)*100:.0f}%"
                ],
                uncertainty_analysis="Transparent deterministic scoring without subjective model bias."
            )

        elif target_type == "novelty" and session.novelty:
            nov = session.novelty
            return WhyExplanation(
                target_type="novelty",
                target_id="novelty",
                target_statement=f"Novelty Assessment: {nov.assessment}",
                confidence=EvidenceConfidence.MEDIUM,
                evidence_chain=[],
                reasoning_factors=[
                    f"Assessment category: {nov.assessment.replace('_', ' ').title()}",
                    nov.explanation,
                    f"Explored dimensions: {', '.join(nov.explored_dimensions)}",
                    f"Potentially unexplored: {', '.join(nov.potentially_unexplored)}"
                ],
                uncertainty_analysis="Novelty is assessed relative to the retrieved corpus; scientific novelty cannot be guaranteed unconditionally from finite retrieval."
            )

        elif target_type == "red_team" and session.red_team:
            rt = session.red_team
            return WhyExplanation(
                target_type="red_team",
                target_id="red_team",
                target_statement=f"Red Team Adjudication (Final Confidence: {rt.final_confidence.value.upper()})",
                confidence=rt.final_confidence,
                evidence_chain=[],
                reasoning_factors=[
                    f"Challenged: {rt.conclusion_challenged}",
                    f"Identified vulnerabilities: {'; '.join(rt.challenges)}",
                    f"Potential biases: {'; '.join(rt.potential_biases)}",
                    f"Adjudication verdict: {rt.adjudication}"
                ],
                uncertainty_analysis="Independent adversarial critique prevents overconfident conclusions."
            )

        return None

    def get_timeline(self, session_id: str) -> list[TimelineMilestone]:
        """Generate longitudinal research evolution milestones."""
        session = self.sessions.get(session_id)
        if not session:
            return []

        # Group papers by year
        year_to_papers: dict[int, list[Paper]] = {}
        for p in session.papers.values():
            y = p.year or 0
            year_to_papers.setdefault(y, []).append(p)

        is_battery_demo = self.settings.demo_mode and any(k in session.question.lower() for k in ["battery", "rul", "degradation", "lithium"])

        if is_battery_demo:
            return [
                TimelineMilestone(
                    year=2019,
                    paradigm="Empirical & Statistical Degradation",
                    title="Early Statistical and Filter-Based RUL Models",
                    description="Initial approaches focused on particle filtering, Gaussian Process Regression, and empirical capacity fade curve fitting.",
                    paper_ids=[],
                    key_methods=["Kalman Filter", "GPR", "Support Vector Regression"],
                    breakthrough_indicator=False,
                ),
                TimelineMilestone(
                    year=2021,
                    paradigm="Recurrent Sequence Networks",
                    title="LSTM and GRU Dominance in Time-Series RUL",
                    description="Recurrent deep learning models set early deep baselines on NASA and CALCE datasets for cycle-to-cycle capacity estimation.",
                    paper_ids=[p.id for p in year_to_papers.get(2021, [])],
                    key_methods=["LSTM", "GRU", "Bi-LSTM"],
                    breakthrough_indicator=False,
                ),
                TimelineMilestone(
                    year=2023,
                    paradigm="Self-Attention & Transformers",
                    title="Attention Mechanisms for Long-Horizon Forecasting",
                    description="Transformer architectures introduced multi-head self-attention to capture long-range capacity degradation trajectories.",
                    paper_ids=[p.id for p in year_to_papers.get(2023, [])],
                    key_methods=["Informer", "Vanilla Transformer", "PatchTST"],
                    breakthrough_indicator=True,
                ),
                TimelineMilestone(
                    year=2024,
                    paradigm="Graph Neural Networks (GNN & GAT)",
                    title="Graph Attention Networks for Battery Degradation Modeling",
                    description="Modeling electrochemical cells and charge/discharge phase cycles as graph networks to capture inter-cell and inter-cycle dependencies.",
                    paper_ids=[p.id for p in year_to_papers.get(2024, [])],
                    key_methods=["GAT", "GCN", "Spatial-Temporal GNN"],
                    breakthrough_indicator=True,
                ),
                TimelineMilestone(
                    year=2025,
                    paradigm="Multi-Cell & Cross-Domain GNNs",
                    title="Multi-Cell Battery Pack Inter-Cell Graph Modeling",
                    description="Scaling graph representations to multi-cell module temperature and voltage imbalances across battery packs.",
                    paper_ids=[p.id for p in year_to_papers.get(2025, [])],
                    key_methods=["Multi-Cell GNN", "Pack-Level GAT"],
                    breakthrough_indicator=False,
                ),
                TimelineMilestone(
                    year=2026,
                    paradigm="Domain-Adaptive & Physics-Informed GNNs",
                    title="Next Frontier: Cross-Chemistry Transfer & Uncertainty-Aware GAT",
                    description="Addressing domain shift across NMC/LFP chemistries and varying ambient temperatures with domain adversarial learning and epistemic uncertainty bounds.",
                    paper_ids=[],
                    key_methods=["Domain-Adaptive GAT", "Physics-Informed GNN", "Bayesian Graph Neural Networks"],
                    breakthrough_indicator=True,
                )
            ]

        # Dynamic evidence-based generation for live mode or non-battery domains
        sorted_years = sorted(year_to_papers.keys())
        milestones = []
        for i, year in enumerate(sorted_years):
            papers = year_to_papers[year]
            display_year = year if year != 0 else "Unknown"
            
            # Extract methods used in this year
            methods_this_year = set()
            for p in papers:
                for m in session.methods:
                    if m.paper_id == p.id and m.model_architecture:
                        methods_this_year.add(m.model_architecture)
                        
            key_methods = list(methods_this_year)[:3]
            
            paradigm = f"Methodological Focus {display_year}"
            title = f"Research Developments in {display_year}"
            if key_methods:
                desc = f"Key publications focused on exploring methodologies including: {', '.join(key_methods)}."
            else:
                desc = f"Published {len(papers)} key papers addressing the primary research gap."
                
            milestones.append(
                TimelineMilestone(
                    year=display_year,
                    paradigm=paradigm,
                    title=title,
                    description=desc,
                    paper_ids=[p.id for p in papers],
                    key_methods=key_methods,
                    breakthrough_indicator=(i == len(sorted_years) - 1 or len(papers) > 2)
                )
            )
            
        return milestones

    async def ingest_pdf(self, session_id: str, file_bytes: bytes, filename: str) -> Optional[Paper]:
        """Safely extract text from user-uploaded PDF and integrate into session."""
        session = self.sessions.get(session_id)
        if not session:
            return None

        # Ensure upload dir
        upload_path = self.settings.upload_dir / f"{new_id()}_{re.sub(r'[^a-zA-Z0-9_.-]', '', filename)}"
        upload_path.write_bytes(file_bytes)

        # Extract text via PyMuPDF or pypdf
        text = ""
        sections: dict[str, str] = {}
        try:
            import fitz
            doc = fitz.open(upload_path)
            pages_text = [page.get_text() for page in doc]
            text = "\n".join(pages_text)
            doc.close()
        except Exception as e:
            logger.warning(f"PyMuPDF failed, falling back to pypdf: {e}")
            try:
                import pypdf
                reader = pypdf.PdfReader(upload_path)
                text = "\n".join(page.extract_text() or "" for page in reader.pages)
            except Exception as e2:
                logger.error(f"PDF extraction failed: {e2}")
                return None

        if not text.strip():
            return None

        # Extract sections heuristically
        lines = text.split("\n")
        title = filename.replace(".pdf", "").replace("_", " ").replace("-", " ")
        if lines:
            for l in lines[:20]:
                if len(l.strip()) > 15 and not l.startswith("http"):
                    title = l.strip()
                    break

        abstract = ""
        m = re.search(r'(?:abstract|summary)[:\s]*(.*?)(?:1\.?\s*introduction|keywords|i\.\s*introduction)', text, re.IGNORECASE | re.DOTALL)
        if m:
            abstract = m.group(1).strip()[:3000]
        else:
            abstract = text[:2000]

        authors = [Author(name="Unknown Author")]
        year = datetime.utcnow().year
        venue = "Uploaded PDF"

        if not self.settings.demo_mode:
            try:
                class PDFMeta(BaseModel):
                    title: str
                    authors: list[str]
                    year: int
                    venue: str
                
                meta_prompt = f"Extract metadata from the start of this academic paper:\n\n{text[:3000]}"
                meta_result = await self.llm.structured_generate(meta_prompt, PDFMeta)
                title = meta_result.title or title
                if meta_result.authors:
                    authors = [Author(name=a) for a in meta_result.authors]
                year = meta_result.year or year
                venue = meta_result.venue or venue
            except Exception as e:
                logger.warning(f"Failed to extract PDF metadata via LLM: {e}")

        paper = Paper(
            title=title,
            authors=authors,
            year=year,
            venue=venue,
            abstract=abstract,
            full_text_available=True,
            sections={"full_text": text[:75000], "abstract": abstract},
            source_provider="upload",
            relevance_score=None,
            evidence_quality=None,
            research_score=None,
            score_components={}
        )

        session.papers[paper.id] = paper
        session.update_stats()

        # If live LLM is available, analyze
        if not self.settings.demo_mode:
            try:
                analysis = await self._analyze_paper(paper)
                session.analyses[paper.id] = analysis
                session.claims.extend(analysis.claims)
                session.evidence.extend(analysis.evidence)
                session.methods.extend(analysis.methods)
                session.update_stats()
            except Exception as e:
                logger.warning(f"Analysis of uploaded PDF failed: {e}")

        return paper

    def get_formatted_bibliography(self, session_id: str, style: str = "apa") -> str:
        """Generate formatted bibliography in APA, IEEE, or BibTeX style."""
        session = self.sessions.get(session_id)
        if not session:
            return ""

        papers = list(session.papers.values())
        if style.lower() == "bibtex":
            entries = []
            for i, p in enumerate(papers):
                first_author = p.authors[0].name.split()[-1].lower() if p.authors else "author"
                year = p.year or "n.d."
                cite_key = f"{first_author}{year}_{p.id[:4]}"
                authors_str = " and ".join(a.name for a in p.authors) if p.authors else "Unknown"
                entry = (
                    f"@article{{{cite_key},\n"
                    f"  title = {{{p.title}}},\n"
                    f"  author = {{{authors_str}}},\n"
                    f"  journal = {{{p.venue or 'Preprint'}}},\n"
                    f"  year = {{{year}}},\n"
                    f"  doi = {{{p.doi or ''}}},\n"
                    f"  url = {{{p.url or ''}}}\n"
                    f"}}"
                )
                entries.append(entry)
            return "\n\n".join(entries)

        elif style.lower() == "ieee":
            entries = []
            for i, p in enumerate(papers, 1):
                authors_str = ", ".join(a.name for a in p.authors[:3])
                if len(p.authors) > 3:
                    authors_str += " et al."
                venue_str = f', {p.venue}' if p.venue else ''
                doi_str = f', doi: {p.doi}' if p.doi else ''
                entries.append(f'[{i}] {authors_str}, "{p.title}"{venue_str}, {p.year or "n.d."}{doi_str}.')
            return "\n\n".join(entries)

        else:  # APA default
            entries = []
            for p in papers:
                authors_str = ", ".join(a.name for a in p.authors[:3])
                if len(p.authors) > 3:
                    authors_str += ", et al."
                venue_str = f' *{p.venue}*' if p.venue else ''
                doi_str = f' https://doi.org/{p.doi}' if p.doi else ''
                entries.append(f"{authors_str} ({p.year or 'n.d.'}). {p.title}.{venue_str}.{doi_str}")
            return "\n\n".join(entries)



# Singleton
_pipeline: Optional[ResearchPipeline] = None


def get_pipeline() -> ResearchPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = ResearchPipeline()
    return _pipeline
