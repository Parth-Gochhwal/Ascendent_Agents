from abc import ABC, abstractmethod
from backend.app.models.research import ResearchSession
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

    @abstractmethod
    async def execute(self, session: ResearchSession, **kwargs) -> None:
        """
        Execute the agent's core logic. Mutates the session in-place.
        Raises exceptions on failure, which the orchestrator should catch and handle.
        """
        pass
