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
    Identifies research gaps, missing experiments, assesses novelty, and designs new experiments.
    """
    @property
    def name(self) -> str:
        return "Innovation Engine"

    async def execute(self, session: ResearchSession, **kwargs) -> None:
        """
        Executes gap detection, novelty analysis, and experiment design.
        """
        # Gaps
        try:
            session.gaps = await self._detect_gaps(session)
        except Exception as e:
            logger.warning(f"Gap detection failed: {e}")
            
        # Missing Experiments
        try:
            session.missing_experiments = await self._detect_missing_experiments(session)
        except Exception as e:
            logger.warning(f"Missing experiment detection failed: {e}")
            
        # Experiment Design
        if session.gaps:
            try:
                session.experiment = await self._design_experiment(session)
            except Exception as e:
                logger.warning(f"Experiment design failed: {e}")

    async def _detect_gaps(self, session: ResearchSession):
        conclusions = "\n".join([f"- {c.statement}" for c in session.consensus])
        contradictions = "\n".join([f"- {c.claim_a_text} vs {c.claim_b_text}" for c in session.contradictions])
        
        prompt = GAP_DETECTION_V1.format(
            question=session.question,
            conclusions=conclusions or "None identified",
            contradictions=contradictions or "None identified"
        )
        result = await self.llm.structured_generate(prompt, GapList, system_prompt=SYSTEM_PROMPT)
        return result.gaps if result else []

    async def _detect_missing_experiments(self, session: ResearchSession):
        gaps_text = "\n".join([f"- {g.title}: {g.description}" for g in session.gaps])
        contradictions_text = "\n".join([f"- {c.claim_a_text} vs {c.claim_b_text}" for c in session.contradictions])
        
        prompt = MISSING_EXPERIMENTS_V1.format(
            gaps=gaps_text if gaps_text else "None explicitly identified.",
            contradictions=contradictions_text if contradictions_text else "None explicitly identified."
        )
        
        result = await self.llm.structured_generate(prompt, MissingExperimentList, system_prompt=SYSTEM_PROMPT)
        return result.experiments if result else []

    async def _design_experiment(self, session: ResearchSession):
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
