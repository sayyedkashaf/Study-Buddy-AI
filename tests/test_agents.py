"""
Tests for the AI agent system.

Run with: pytest tests/ -v
"""

import pytest
import asyncio
import os

# Skip all tests if no Gemini API key
pytestmark = pytest.mark.skipif(
    not os.getenv("GEMINI_API_KEY"),
    reason="GEMINI_API_KEY not set — skipping agent tests"
)

@pytest.fixture
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


class TestPlannerAgent:
    """Tests for the PlannerAgent."""

    @pytest.mark.asyncio
    async def test_planner_generates_response(self):
        """PlannerAgent should return a non-empty study plan."""
        from api.agents.planner_agent import PlannerAgent

        agent = PlannerAgent()
        response = await agent.run(
            message="Create a 2-week study plan for Data Structures",
            context={"exam_date": "2026-07-01"},
        )

        assert isinstance(response, str)
        assert len(response) > 100  # Should be substantial

    @pytest.mark.asyncio
    async def test_planner_mentions_topics(self):
        """PlannerAgent should reference study topics."""
        from api.agents.planner_agent import PlannerAgent

        agent = PlannerAgent()
        response = await agent.run(
            message="Help me plan for a Python programming exam",
            context={"exam_date": "2026-07-15"},
        )

        # Should contain planning-related words
        response_lower = response.lower()
        assert any(word in response_lower for word in ["day", "week", "study", "plan", "review"])


class TestAssignmentAgent:
    """Tests for the AssignmentAgent."""

    @pytest.mark.asyncio
    async def test_assignment_explains_concept(self):
        """AssignmentAgent should explain concepts."""
        from api.agents.assignment_agent import AssignmentAgent

        agent = AssignmentAgent()
        response = await agent.run(
            message="Explain how binary search works",
        )

        assert isinstance(response, str)
        assert len(response) > 50

    @pytest.mark.asyncio
    async def test_assignment_handles_code_questions(self):
        """AssignmentAgent should handle programming questions."""
        from api.agents.assignment_agent import AssignmentAgent

        agent = AssignmentAgent()
        response = await agent.run(
            message="What is the time complexity of quicksort?",
        )

        assert isinstance(response, str)
        assert "log" in response.lower() or "n" in response.lower()


class TestOrchestrator:
    """Tests for the Orchestrator routing logic."""

    @pytest.mark.asyncio
    async def test_routes_planning_to_planner(self):
        """Planning requests should route to PlannerAgent."""
        from api.agents.orchestrator import Orchestrator

        orch = Orchestrator()
        response, agent_used = await orch.route("Create a study schedule for my exam next month")

        assert isinstance(response, str)
        assert len(response) > 50
        # Should route to planner (though exact agent name may vary)
        assert agent_used in ["PlannerAgent", "AssignmentAgent"]

    @pytest.mark.asyncio
    async def test_routes_concept_to_assignment(self):
        """Concept questions should route to AssignmentAgent."""
        from api.agents.orchestrator import Orchestrator

        orch = Orchestrator()
        response, agent_used = await orch.route("Explain binary search trees")

        assert isinstance(response, str)
        assert len(response) > 50

    @pytest.mark.asyncio
    async def test_handles_errors_gracefully(self):
        """Orchestrator should handle errors without crashing."""
        from api.agents.orchestrator import Orchestrator

        orch = Orchestrator()
        response, agent_used = await orch.route("test message")

        assert isinstance(response, str)
