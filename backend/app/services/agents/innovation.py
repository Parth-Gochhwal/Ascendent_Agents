import logging
from backend.app.services.agents.base import BaseAgent
from backend.app.models.research import (
    ResearchSession, GapList, MissingExperimentList, NoveltyAssessment, ExperimentProposal
)
from backend.app.prompts.templates import (
    GAP_DETECTION_V1, MISSING_EXPERIMENTS_V1, NOVELTY_ANALYSIS_V1, EXPERIMENT_DESIGN_V1, SYSTEM_PROMPT
)

logger = logging.getLogger(__name__)

class InnovationAgent(BaseAgent):
    """
    Identifies evidence-driven research gaps, Cartesian missing experiments,
    assesses scientific novelty against existing corpus, and formulates rigorous experiment protocols.
    """
    @property
    def name(self) -> str:
        return "Innovation Engine"

    async def execute(self, session: ResearchSession, **kwargs) -> None:
        """
        Executes gap detection, novelty analysis, and experiment design.
        """
        # Phase 1: Research Gaps
        try:
            session.gaps = await self._detect_gaps(session)
        except Exception as e:
            logger.warning(f"Gap detection failed: {e}")
            
        # Phase 2: Missing Experiments (Cartesian holes)
        try:
            session.missing_experiments = await self._detect_missing_experiments(session)
        except Exception as e:
            logger.warning(f"Missing experiment detection failed: {e}")

        # Phase 3: Novelty Assessment against literature corpus
        try:
            session.novelty = await self._assess_novelty(session)
        except Exception as e:
            logger.warning(f"Novelty analysis failed: {e}")
            
        # Phase 4: Experiment Design grounded in gaps, dead ends, and reproducibility
        if session.gaps:
            try:
                session.experiment = await self._design_experiment(session)
            except Exception as e:
                logger.warning(f"Experiment design failed: {e}")

    async def _detect_gaps(self, session: ResearchSession) -> list:
        papers_summary = "\n".join([f"- [{p.id}] {p.title} ({p.year or 'N/A'})" for p in list(session.papers.values())[:10]])
        claims_summary = "\n".join([f"- [{c.paper_id}] {c.statement}" for c in session.claims[:15]])
        contradictions_summary = "\n".join([f"- {c.claim_a_text} vs {c.claim_b_text}" for c in session.contradictions[:5]])
        methods_summary = ", ".join(set(m.model_architecture for m in session.methods if m.model_architecture)) or "Various neural network architectures"
        datasets_summary = ", ".join(set(m.dataset for m in session.methods if m.dataset)) or "Standard evaluation datasets"

        prompt = GAP_DETECTION_V1.format(
            question=session.question,
            papers_summary=papers_summary or "None available",
            claims_summary=claims_summary or "None available",
            contradictions_summary=contradictions_summary or "None identified",
            methods_summary=methods_summary,
            datasets_summary=datasets_summary
        )
        result = await self.llm.structured_generate(prompt, GapList, system_prompt=SYSTEM_PROMPT, use_fast=False)
        return result.gaps if result else []

    async def _detect_missing_experiments(self, session: ResearchSession) -> list:
        gaps_text = "\n".join([f"- {g.title}: {g.description}" for g in session.gaps])
        contradictions_text = "\n".join([f"- {c.claim_a_text} vs {c.claim_b_text}" for c in session.contradictions])
        
        prompt = MISSING_EXPERIMENTS_V1.format(
            gaps=gaps_text if gaps_text else "None explicitly identified.",
            contradictions=contradictions_text if contradictions_text else "None explicitly identified."
        )
        
        result = await self.llm.structured_generate(prompt, MissingExperimentList, system_prompt=SYSTEM_PROMPT, use_fast=True)
        return result.experiments if result else []

    async def _assess_novelty(self, session: ResearchSession) -> NoveltyAssessment:
        top_gap_desc = session.gaps[0].title + ": " + session.gaps[0].description if session.gaps else session.question
        
        # Build deterministic comparison corpus
        papers_summary = "\n".join(
            f"[{p.id}] {p.title} ({p.year or 'N/A'}) - Abstract: {(p.abstract or 'No abstract')[:200]}"
            for p in list(session.papers.values())[:10]
        )
        methods_summary = "\n".join(
            f"- Model: {m.model_architecture or 'N/A'}, Dataset: {m.dataset or 'N/A'}, Optimizer: {m.optimizer or 'N/A'}"
            for m in session.methods[:8]
        )
        
        prompt = NOVELTY_ANALYSIS_V1.format(
            idea=top_gap_desc,
            papers_summary=papers_summary or "No papers retrieved.",
            methods_summary=methods_summary or "No explicit method pipelines extracted."
        )
        
        novelty = await self.llm.structured_generate(prompt, NoveltyAssessment, system_prompt=SYSTEM_PROMPT, use_fast=False)
        novelty.proposed_idea = top_gap_desc
        return novelty

    async def _design_experiment(self, session: ResearchSession) -> ExperimentProposal:
        gap = session.gaps[0]
        context = "\n".join(
            f"- [{p.id}] {p.title} ({p.year or 'N/A'})" for p in list(session.papers.values())[:10]
        )
        methods = ", ".join(set(m.model_architecture for m in session.methods if m.model_architecture))
        datasets = ", ".join(set(m.dataset for m in session.methods if m.dataset))
        metrics = ", ".join(set(m for method in session.methods for m in method.metrics))

        # Include dead-end failure memory to avoid repeated failed baselines
        dead_ends_info = ""
        if session.dead_ends:
            dead_ends_info = "\nKNOWN DEAD ENDS & FAILED APPROACHES TO AVOID:\n" + "\n".join(
                f"- {de.approach}: {de.description} (Failure conditions: {', '.join(de.failure_conditions) if de.failure_conditions else 'General'})"
                for de in session.dead_ends
            )

        # Include reproducibility requirements from profiler
        reproducibility_risks = ""
        missing_repro_details = []
        for pid, prof in session.reproducibility_profiles.items():
            if prof.missing_components:
                missing_repro_details.extend(prof.missing_components)
        if missing_repro_details:
            reproducibility_risks = f"\nKNOWN REPRODUCIBILITY PITFALLS IN LITERATURE: Missing {', '.join(set(missing_repro_details)[:5])}"

        prompt = EXPERIMENT_DESIGN_V1.format(
            gap=f"{gap.title}: {gap.description}",
            context=f"{context}{dead_ends_info}{reproducibility_risks}",
            methods=methods or "Various deep learning methods",
            datasets=datasets or "Standard benchmark datasets",
            metrics=metrics or "Standard quantitative metrics (accuracy, F1, RMSE)"
        )

        proposal = await self.llm.structured_generate(prompt, ExperimentProposal, system_prompt=SYSTEM_PROMPT, use_fast=False)
        proposal.gap_id = gap.id
        proposal.addresses_gap = f"{gap.title}: {gap.description}"
        proposal.dead_end_ids = [de.id for de in session.dead_ends]
        proposal.avoids_dead_ends = [de.approach for de in session.dead_ends]
        proposal.motivated_by_evidence = list(session.papers.keys())[:5]
        return proposal

