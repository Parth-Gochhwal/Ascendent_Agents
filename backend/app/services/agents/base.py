from abc import ABC, abstractmethod
from backend.app.models.research import ResearchSession, StageResult
from backend.app.providers.llm_provider import LLMProvider
import logging

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    The base contract for all Nexus agents.
    Agents are responsible for specific research phases and mutate the ResearchSession state.
    """
    def __init__(self, llm: LLMProvider):
        self.llm = llm

    @property
    @abstractmethod
    def name(self) -> str:
        """The display name of the agent (e.g., 'Planning Agent')."""
        pass

    @property
    def description(self) -> str:
        """A short description of the agent's purpose."""
        return ""

    @abstractmethod
    async def execute(self, session: ResearchSession, **kwargs) -> None:
        """
        Execute the agent's core logic. Mutates the session in-place.
        Raises exceptions on failure, which the orchestrator should catch and handle.
        """
        pass

    def record_stage(self, session: ResearchSession, stage_name: str, result: StageResult,
                     warning: str = ""):
        """Record a stage result on the session for quality tracking."""
        session.stage_results[stage_name] = result.value
        if result == StageResult.FAILED:
            if session.quality_state == "complete":
                session.quality_state = "degraded"
            if warning:
                session.quality_warnings.append(warning)
        elif result == StageResult.PARTIAL:
            if session.quality_state == "complete":
                session.quality_state = "degraded"
            if warning:
                session.quality_warnings.append(warning)
