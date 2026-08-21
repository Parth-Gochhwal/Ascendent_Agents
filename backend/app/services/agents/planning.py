from backend.app.services.agents.base import BaseAgent
from backend.app.models.research import ResearchSession, ResearchPlan
from backend.app.prompts.templates import PLANNER_V1, SYSTEM_PROMPT

class PlanningAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "Planning Agent"

    @property
    def description(self) -> str:
        return "Decomposes research questions into structured subquestions, entities, and search queries."

    async def execute(self, session: ResearchSession, **kwargs) -> None:
        """
        Uses the LLM to generate a structured research plan from the session's question.
        Mutates the session to attach the plan with degradation tracking.
        """
        from backend.app.models.research import StageResult

        try:
            prompt = PLANNER_V1.format(question=session.question)
            plan = await self.llm.structured_generate(
                prompt, ResearchPlan, system_prompt=SYSTEM_PROMPT
            )
            session.plan = plan
            self.record_stage(session, "planning", StageResult.SUCCESS)
        except Exception as e:
            session.plan = ResearchPlan(
                normalized_question=session.question,
                research_objective=f"Investigate: {session.question}",
                search_queries=[session.question],
            )
            self.record_stage(session, "planning", StageResult.PARTIAL,
                              f"Planning LLM failed ({e}) — generated single-query fallback plan")
