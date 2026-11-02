"""
Planner Agent — Creates personalized study schedules.

Capabilities:
- Searches syllabus for relevant topics (via ChromaDB)
- Calculates days until exam
- Generates weighted study plans
- Saves plans to database
"""

import logging
from datetime import datetime

from api.agents.base_agent import BaseAgent
from api.services.vector_store import VectorStore
from api.services.cache_service import CacheService
from api.services.study_planner import generate_study_plan

logger = logging.getLogger(__name__)


class PlannerAgent(BaseAgent):
    """AI agent specialized in creating study schedules and plans."""

    def __init__(self):
        super().__init__()
        self.vector_store = VectorStore()
        self.cache = CacheService()

    def get_system_prompt(self) -> str:
        return """You are an expert study planning assistant for university students. 
Given a list of topics from their syllabus and an exam date, create a realistic, 
day-by-day study schedule.

Rules:
- Allocate more days to complex/high-weight topics
- Leave 2-3 days before the exam for revision and practice
- Assume 2-3 hours of focused study per day
- Be specific about what to cover each day
- Include practical tips (practice problems, flashcards, etc.)
- Format as a clear daily breakdown with dates
- Use emoji for visual clarity (📅 for dates, ✅ for milestones)
- If topics overlap, mention connections between them
- End with motivational tips and exam-day advice

Remember: You're helping a real student. Be encouraging but realistic."""

    async def run(self, message: str, context: dict = None) -> str:
        """
        Generate a study plan based on the user's request and syllabus.

        Context can include:
        - exam_date: ISO date string (YYYY-MM-DD)
        - subject: Subject name to filter search
        """
        context = context or {}
        self._log("Starting", f"Message: {message[:80]}...")

        # ── 1. Check cache ────────────────────────────────────
        cache_key = self.cache.cache_key("plan", message + str(context))
        cached = self.cache.get(cache_key)
        if cached:
            self._log("Cache hit", cache_key)
            return cached

        # ── 2. Search syllabus for relevant topics ────────────
        search_results = self.vector_store.search(message, top_k=10)
        topics_text = "\n".join(
            doc for doc in search_results["documents"][0]
        ) if search_results["documents"][0] else "No syllabus uploaded yet."

        # ── 3. Calculate days until exam ──────────────────────
        exam_date_str = context.get("exam_date", "")
        days_info = ""
        if exam_date_str:
            try:
                exam_date = datetime.strptime(exam_date_str, "%Y-%m-%d")
                days_until = (exam_date - datetime.now()).days
                days_info = f"\nDays until exam: {days_until} days (Exam: {exam_date_str})"
            except ValueError:
                days_info = "\n(Could not parse exam date)"

        # ── 4. Build prompt with all context ──────────────────
        user_prompt = f"""Create a detailed study plan based on this request:
"{message}"

📚 Available topics from syllabus:
{topics_text}
{days_info}

Generate a comprehensive day-by-day study schedule. Include:
1. Daily topics with specific sub-topics to cover
2. Recommended study techniques for each topic
3. Practice problem suggestions
4. Milestone checkpoints
5. Revision strategy for the final days"""

        # ── 5. Call Gemini LLM ───────────────────────────────
        self._log("Calling LLM", f"Prompt length: {len(user_prompt)} chars")
        plan = await self.llm.call(
            system_prompt=self.get_system_prompt(),
            user_message=user_prompt,
            max_tokens=2048,
            temperature=0.7,
        )

        # ── 6. Cache the result ───────────────────────────────
        self.cache.set(cache_key, plan, ttl=3600)
        self._log("Complete", f"Response: {len(plan)} chars")

        return plan
