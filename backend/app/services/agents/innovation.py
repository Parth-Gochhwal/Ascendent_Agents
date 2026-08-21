import logging
from backend.app.services.agents.base import BaseAgent
from backend.app.models.research import (
    ResearchSession, GapList, MissingExperimentList, NoveltyAssessment, ExperimentProposal
)
from backend.app.prompts.templates import (
    GAP_DETECTION_V1, MISSING_EXPERIMENTS_V1, NOVELTY_ANALYSIS_V1, EXPERIMENT_DESIGN_V1, SYSTEM_PROMPT
)

logger = logging.getLogger(__name__)


def _rank_gaps(session: ResearchSession) -> list:
    """Rank gaps by evidence-backed importance signals (deterministic)."""
    gaps = list(session.gaps)
    if not gaps:
        return gaps

    def gap_score(g):
        score = 0.0
        # Importance multiplier
        importance_map = {"critical": 4.0, "high": 3.0, "medium": 2.0, "low": 1.0}
        score += importance_map.get(g.importance, 2.0)
        # Novelty potential
        novelty_map = {"high": 2.0, "medium": 1.0, "low": 0.5}
        score += novelty_map.get(g.novelty_potential, 1.0)
        # Feasibility
        feas_map = {"high": 1.5, "medium": 1.0, "low": 0.5}
        score += feas_map.get(g.feasibility, 1.0)
        # Evidence backing
        score += min(2.0, len(g.supporting_paper_ids) * 0.5)
        # Contradictions related to gap boost importance
        for c in session.contradictions:
            if any(kw in g.title.lower() for kw in c.claim_a_text.lower().split()[:5]):
                score += 1.0
                break
        return score

    gaps.sort(key=gap_score, reverse=True)
    return gaps


class InnovationAgent(BaseAgent):
    """
    Identifies evidence-driven research gaps, Cartesian missing experiments,
    assesses scientific novelty against existing corpus, and formulates rigorous experiment protocols.
    """
    @property
    def name(self) -> str:
        return "Innovation Engine"

    @property
    def description(self) -> str:
        return "Detects research gaps, assesses novelty, and designs experiments grounded in evidence and dead-end memory."

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
            
        # Phase 4: Experiment Design grounded in ranked gaps, dead ends, and reproducibility
        if session.gaps:
            try:
                session.experiment = await self._design_experiment(session)
            except Exception as e:
                logger.warning(f"Experiment design failed: {e}")

    async def _detect_gaps(self, session: ResearchSession) -> list:
        # Build context from highest-value evidence, not positional slices
        ranked_papers = sorted(
            session.papers.values(),
            key=lambda p: p.research_score or 0.0,
            reverse=True
        )
        papers_summary = "\n".join([
            f"- [{p.id}] {p.title} ({p.year or 'N/A'})"
            for p in ranked_papers[:12]
        ])

        # Select claims with strongest evidence backing
        claims_with_strength = sorted(
            session.claims,
            key=lambda c: c.strength.composite_score if c.strength else 0.0,
            reverse=True
        )
        claims_summary = "\n".join([
            f"- [{c.paper_id}] {c.statement} (strength: {c.strength.composite_score:.2f})"
            if c.strength else f"- [{c.paper_id}] {c.statement}"
            for c in claims_with_strength[:15]
        ])

        # Include all contradictions (typically small set) and ranked dead ends
        contradictions_summary = "\n".join([
            f"- {c.claim_a_text} vs {c.claim_b_text} ({c.classification.value})"
            for c in session.contradictions
        ])

        methods_summary = ", ".join(set(m.model_architecture for m in session.methods if m.model_architecture)) or "Various neural network architectures"
        datasets_summary = ", ".join(set(m.dataset for m in session.methods if m.dataset)) or "Standard evaluation datasets"

        # Include dead-end and reproducibility context
        dead_end_context = ""
        if session.dead_ends:
            dead_end_context = "\nKNOWN DEAD ENDS:\n" + "\n".join(
                f"- {de.approach}: {de.description} (status: {de.status.value})"
                for de in session.dead_ends[:5]
            )

        repro_context = ""
        low_repro = [(pid, p) for pid, p in session.reproducibility_profiles.items() if p.completeness_score < 0.5]
        if low_repro:
            repro_context = f"\nREPRODUCIBILITY CONCERNS: {len(low_repro)} papers have low reproducibility completeness."

        prompt = GAP_DETECTION_V1.format(
            question=session.question,
            papers_summary=(papers_summary or "None available") + dead_end_context + repro_context,
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
        # Select highest-ranked gap instead of gaps[0]
        ranked_gaps = _rank_gaps(session)
        top_gap_desc = (ranked_gaps[0].title + ": " + ranked_gaps[0].description) if ranked_gaps else session.question
        
        # Build deterministic comparison corpus — ranked by evidence strength
        ranked_papers = sorted(
            session.papers.values(),
            key=lambda p: p.research_score or 0.0,
            reverse=True
        )
        papers_summary = "\n".join(
            f"[{p.id}] {p.title} ({p.year or 'N/A'}) - Abstract: {(p.abstract or 'No abstract')[:200]}"
            for p in ranked_papers[:10]
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
        # Select highest-ranked gap, not gaps[0]
        ranked_gaps = _rank_gaps(session)
        gap = ranked_gaps[0]

        # Build context from highest-scored papers
        ranked_papers = sorted(
            session.papers.values(),
            key=lambda p: p.research_score or 0.0,
            reverse=True
        )
        context = "\n".join(
            f"- [{p.id}] {p.title} ({p.year or 'N/A'})" for p in ranked_papers[:10]
        )
        methods = ", ".join(set(m.model_architecture for m in session.methods if m.model_architecture))
        datasets = ", ".join(set(m.dataset for m in session.methods if m.dataset))
        metrics = ", ".join(set(m for method in session.methods for m in method.metrics))

        # Include dead-end failure memory to avoid repeated failed baselines
        dead_ends_info = ""
        if session.dead_ends:
            dead_ends_info = "\nKNOWN DEAD ENDS & FAILED APPROACHES TO AVOID:\n" + "\n".join(
                f"- {de.approach}: {de.description} (Status: {de.status.value}, Conditions: {', '.join(de.failure_conditions) if de.failure_conditions else 'General'})"
                for de in session.dead_ends
            )

        # Include reproducibility blockers
        reproducibility_risks = ""
        all_blockers = []
        for pid, prof in session.reproducibility_profiles.items():
            for blocker in prof.blockers:
                all_blockers.append(f"{blocker.category}: {blocker.evidence}")
            if prof.missing_components:
                all_blockers.extend(prof.missing_components)
        if all_blockers:
            unique_blockers = sorted(set(all_blockers))[:8]
            reproducibility_risks = f"\nKNOWN REPRODUCIBILITY PITFALLS IN LITERATURE: {', '.join(unique_blockers)}"

        # Include relevant unresolved contradictions
        contradictions_context = ""
        if session.contradictions:
            contradictions_context = "\nUNRESOLVED CONTRADICTIONS:\n" + "\n".join(
                f"- {c.claim_a_text} vs {c.claim_b_text} ({c.classification.value})"
                for c in session.contradictions[:5]
            )

        prompt = EXPERIMENT_DESIGN_V1.format(
            gap=f"{gap.title}: {gap.description}",
            context=f"{context}{dead_ends_info}{reproducibility_risks}{contradictions_context}",
            methods=methods or "Various deep learning methods",
            datasets=datasets or "Standard benchmark datasets",
            metrics=metrics or "Standard quantitative metrics (accuracy, F1, RMSE)"
        )

        proposal = await self.llm.structured_generate(prompt, ExperimentProposal, system_prompt=SYSTEM_PROMPT, use_fast=False)
        proposal.gap_id = gap.id
        proposal.addresses_gap = f"{gap.title}: {gap.description}"
        proposal.dead_end_ids = [de.id for de in session.dead_ends]
        proposal.avoids_dead_ends = [de.approach for de in session.dead_ends]
        proposal.motivated_by_evidence = [p.id for p in ranked_papers[:5]]
        return proposal
