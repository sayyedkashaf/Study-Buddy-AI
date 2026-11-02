"""
Assignment Agent — Helps students understand concepts and homework.

Capabilities:
- Searches syllabus for relevant course content (RAG)
- Retrieves past conversations for continuity
- Explains concepts step-by-step (doesn't do homework FOR them)
- References which unit/topic from syllabus is relevant
"""

import logging

from api.agents.base_agent import BaseAgent
from api.services.vector_store import VectorStore
from api.services.cache_service import CacheService

logger = logging.getLogger(__name__)


class AssignmentAgent(BaseAgent):
    """AI agent specialized in explaining concepts and helping with homework."""

    def __init__(self):
        super().__init__()
        self.vector_store = VectorStore()
        self.cache = CacheService()

    def get_system_prompt(self) -> str:
        return """You are an expert academic tutor for university students. 
You help students understand concepts from their coursework.

Rules:
- ALWAYS search their syllabus first before answering
- Help them UNDERSTAND concepts — don't write complete solutions for them
- For algorithms/concepts: explain the intuition first, then the details
- If it's a standard algorithm/concept, you CAN show examples and code
- If it's their specific assignment, GUIDE them through the approach
- Reference which unit/topic from their syllabus is relevant
- Use this format: Concept → Intuition → Explanation → Example → Practice

Formatting:
- Use markdown headers (##) for sections
- Use code blocks (```) for any code examples
- Use bullet points for key takeaways
- Include time complexity for algorithms
- End with a practice suggestion or follow-up question

Tone: Encouraging, patient, like a knowledgeable study partner.
Never condescending. If they're struggling, break it down further."""

    async def run(self, message: str, context: dict = None) -> str:
        """
        Help the student understand a concept or solve a problem.

        Context can include:
        - subject: Subject name to filter search
        - user_id: For retrieving conversation history
        """
        context = context or {}
        self._log("Starting", f"Message: {message[:80]}...")

        # ── 1. Check cache ────────────────────────────────────
        cache_key = self.cache.cache_key("assignment", message)
        cached = self.cache.get(cache_key)
        if cached:
            self._log("Cache hit", cache_key)
            return cached

        # ── 2. Search syllabus for relevant content ───────────
        syllabus_results = self.vector_store.search(message, top_k=5)
        syllabus_context = "\n".join(
            syllabus_results["documents"][0]
        ) if syllabus_results["documents"][0] else ""

        # ── 3. Search conversation memory ─────────────────────
        user_id = context.get("user_id", "default")
        past_conversations = self.vector_store.search_memory(message, user_id=user_id, top_k=3)
        memory_context = "\n".join(past_conversations) if past_conversations else ""

        # ── 4. Build enriched prompt ──────────────────────────
        context_sections = []

        if syllabus_context:
            context_sections.append(
                f"📚 Relevant content from their syllabus:\n{syllabus_context}"
            )
        else:
            context_sections.append(
                "📚 No syllabus uploaded for this topic. Use your general knowledge."
            )

        if memory_context:
            context_sections.append(
                f"💭 Previous relevant discussions with this student:\n{memory_context}"
            )

        context_text = "\n\n".join(context_sections)

        user_prompt = f"""Student question: {message}

{context_text}

Explain this concept to help them learn. If the topic is in their syllabus, 
reference the relevant section. If you've discussed related topics before, 
build on that context."""

        # ── 5. Call Gemini LLM ───────────────────────────────
        self._log("Calling LLM", f"Context: {len(context_text)} chars")
        response = await self.llm.call(
            system_prompt=self.get_system_prompt(),
            user_message=user_prompt,
            max_tokens=1500,
            temperature=0.7,
        )

        # ── 6. Cache and return ───────────────────────────────
        self.cache.set(cache_key, response, ttl=1800)  # Cache for 30 min
        self._log("Complete", f"Response: {len(response)} chars")

        return response
