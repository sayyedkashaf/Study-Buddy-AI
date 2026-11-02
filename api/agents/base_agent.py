"""
Base Agent — Abstract base class for all AI agents.

Every agent follows the same pattern:
1. Build context (from tools, memory, database)
2. Construct prompt (system + user + context)
3. Call LLM (via Google Gemini)
4. Return response

Subclasses override get_system_prompt() and run().
"""

from abc import ABC, abstractmethod
import logging

from api.services.llm_service import LLMService

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Abstract base class for all Study Buddy agents."""

    def __init__(self):
        self.llm = LLMService()
        self.name = self.__class__.__name__

    @abstractmethod
    def get_system_prompt(self) -> str:
        """
        Return the system prompt that defines this agent's behavior.
        Override in every subclass.
        """
        return "You are a helpful AI assistant."

    @abstractmethod
    async def run(self, message: str, context: dict = None) -> str:
        """
        Main agent execution method.

        Args:
            message: The user's input message.
            context: Optional additional context (exam dates, user info, etc.).

        Returns:
            Agent's text response.
        """
        pass

    async def _call_llm(self, user_message: str, max_tokens: int = 1024, temperature: float = 0.7) -> str:
        """Convenience wrapper for LLM calls with this agent's system prompt."""
        return await self.llm.call(
            system_prompt=self.get_system_prompt(),
            user_message=user_message,
            max_tokens=max_tokens,
            temperature=temperature,
        )

    def _log(self, action: str, detail: str = ""):
        """Structured logging for agent actions."""
        logger.info(f"[{self.name}] {action}: {detail}")
