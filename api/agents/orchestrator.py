"""
Orchestrator Agent — Routes messages to the correct specialist agent.

This is the brain of the multi-agent system. It:
1. Analyzes the user's message intent
2. Routes to the appropriate specialist agent
3. Saves conversation history for memory
4. Tracks which agent handled each request

Uses the FAST model (gemini-3.5-flash-lite) for routing decisions
to keep latency and costs low.
"""

import logging

from api.agents.base_agent import BaseAgent
from api.agents.planner_agent import PlannerAgent
from api.agents.assignment_agent import AssignmentAgent
from api.agents.memory_agent import MemoryAgent
from api.services.vector_store import VectorStore

logger = logging.getLogger(__name__)


class Orchestrator(BaseAgent):
    """
    Central orchestrator that routes messages to specialist agents.

    Available agents:
    - PlannerAgent: Study schedules, revision plans, time management
    - AssignmentAgent: Concept explanations, homework help, academic Q&A
    - MemoryAgent: Past conversation retrieval, context recall
    """

    def __init__(self):
        super().__init__()
        self.planner = PlannerAgent()
        self.assignment = AssignmentAgent()
        self.memory = MemoryAgent()
        self.vector_store = VectorStore()

        # Agent registry for dynamic routing
        self._agents = {
            "PlannerAgent": self.planner,
            "AssignmentAgent": self.assignment,
            "MemoryAgent": self.memory,
        }

    def get_system_prompt(self) -> str:
        return """You are a message router. Analyze the user's message and decide 
which specialist agent should handle it.

Available agents:
- PlannerAgent: Creates study schedules, plans revision, manages time, organizes study sessions
- AssignmentAgent: Explains concepts, helps with homework, answers academic questions, teaches topics
- MemoryAgent: Recalls past conversations, retrieves discussion history

Decision rules:
- Planning, scheduling, time management, "how many days", revision → PlannerAgent
- Explaining concepts, "what is", "how does", homework, code, algorithms → AssignmentAgent
- "What did we discuss", "remember when", "previously", "last time" → MemoryAgent
- General academic questions → AssignmentAgent
- When unsure → AssignmentAgent

Respond with ONLY the agent name. No explanation. Just the name."""

    async def route(self, message: str, context: dict = None) -> tuple[str, str]:
        """
        Route a message to the appropriate agent.

        Returns:
            Tuple of (response_text, agent_name_used)
        """
        context = context or {}
        self._log("Routing", f"Message: {message[:80]}...")

        # ── 1. Decide which agent ─────────────────────────────
        try:
            routing_decision = await self.llm.call(
                system_prompt=self.get_system_prompt(),
                user_message=message,
                max_tokens=50,
                temperature=0.0,
                use_fast_model=True,  # Use fast model for routing
            )
            agent_name = routing_decision.strip()
        except Exception as e:
            logger.warning(f"Routing decision failed ({e}). Defaulting to AssignmentAgent.")
            agent_name = "AssignmentAgent"

        self._log("Routed to", agent_name)

        # ── 2. Find and call the correct agent ────────────────
        agent = self._resolve_agent(agent_name)
        agent_used = agent.name

        try:
            response = await agent.run(message, context)
        except Exception as e:
            logger.error(f"Agent {agent_used} failed: {e}")
            response = (
                "I'm sorry, I encountered an error while processing your request. "
                "Could you try rephrasing your question? 🙏"
            )

        # ── 3. Save to conversation memory ────────────────────
        user_id = context.get("user_id", "default")
        try:
            self.vector_store.save_conversation(
                user_message=message,
                agent_response=response,
                user_id=user_id,
            )
        except Exception as e:
            logger.warning(f"Failed to save conversation to memory: {e}")

        return response, agent_used

    async def run(self, message: str, context: dict = None) -> str:
        """Main entry point — routes and returns just the response text."""
        response, _ = await self.route(message, context)
        return response

    def _resolve_agent(self, agent_name: str) -> BaseAgent:
        """
        Resolve the agent name from the LLM's routing decision.
        Falls back to AssignmentAgent if the name is unrecognized.
        """
        # Exact match
        if agent_name in self._agents:
            return self._agents[agent_name]

        # Fuzzy match (LLM might say "Planner" instead of "PlannerAgent")
        agent_name_lower = agent_name.lower()
        for name, agent in self._agents.items():
            if name.lower() in agent_name_lower or agent_name_lower in name.lower():
                return agent

        # Keyword fallback
        if any(kw in agent_name_lower for kw in ["plan", "schedule", "revision"]):
            return self.planner
        if any(kw in agent_name_lower for kw in ["memory", "remember", "history"]):
            return self.memory

        # Default: AssignmentAgent handles most things
        self._log("Fallback", f"Unknown agent '{agent_name}', using AssignmentAgent")
        return self.assignment
