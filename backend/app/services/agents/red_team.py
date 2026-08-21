import logging
from backend.app.services.agents.base import BaseAgent
from backend.app.models.research import ResearchSession, RedTeamResult
from backend.app.prompts.templates import RED_TEAM_V1, SYSTEM_PROMPT

logger = logging.getLogger(__name__)

class RedTeamAgent(BaseAgent):
    """
    Adversarial agent that critiques the research synthesis, finding unsupported claims,
    citation echoes, bias, and methodological weaknesses.
    """
    @property
    def name(self) -> str:
        return "Red Team"

    async def execute(self, session: ResearchSession, **kwargs) -> None:
        """
        Executes red team analysis on the final synthesis.
        """
        # We need a summarized synthesis to review
        conclusions = "\n".join([f"- {c.statement}" for c in session.consensus])
        experiment = session.experiment.hypothesis if session.experiment else "None proposed"
        gaps = "\n".join([f"- {g.title}" for g in session.gaps])
        
        prompt = RED_TEAM_V1.format(
            question=session.question,
            conclusions=conclusions or "No conclusions generated.",
            gaps=gaps or "No gaps generated.",
            experiment=experiment
        )
        
        try:
            result = await self.llm.structured_generate(prompt, RedTeamResult, system_prompt=SYSTEM_PROMPT)
            session.red_team = result
        except Exception as e:
            logger.warning(f"Red team analysis failed: {e}")
