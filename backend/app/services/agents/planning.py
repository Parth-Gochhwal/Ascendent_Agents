from backend.app.services.agents.base import BaseAgent
from backend.app.models.research import ResearchSession, ResearchPlan
from backend.app.prompts.templates import PLANNER_V1, SYSTEM_PROMPT

class PlanningAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "Planning Agent"

    async def execute(self, session: ResearchSession, **kwargs) -> None:
        """
        Uses the LLM to generate a structured research plan from the session's question.
        Mutates the session to attach the plan.
        """
        prompt = PLANNER_V1.format(question=session.question)
        plan = await self.llm.structured_generate(
            prompt, ResearchPlan, system_prompt=SYSTEM_PROMPT
        )
        session.plan = plan
