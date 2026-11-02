"""
Memory Agent — Retrieves and summarizes past conversation context.

Capabilities:
- Searches conversation history semantically
- Summarizes relevant past interactions
- Provides continuity across chat sessions
"""

import logging

from api.agents.base_agent import BaseAgent
from api.services.vector_store import VectorStore

logger = logging.getLogger(__name__)


class MemoryAgent(BaseAgent):
    """AI agent specialized in retrieving and contextualizing past conversations."""

    def __init__(self):
        super().__init__()
        self.vector_store = VectorStore()

    def get_system_prompt(self) -> str:
        return """You are a memory retrieval assistant. Your job is to:
1. Search past conversations for relevant context
2. Summarize what was previously discussed about a topic
3. Identify connections between current and past questions
4. Help the student build on prior knowledge

When presenting past context:
- Clearly label it as "from our previous conversation"
- Highlight what was covered vs what's new
- Suggest how past knowledge connects to the current question

If no relevant past conversations are found, say so honestly and 
offer to help from scratch."""

    async def run(self, message: str, context: dict = None) -> str:
        """
        Search and summarize relevant past conversations.

        Context can include:
        - user_id: To scope memory search to this user
        """
        context = context or {}
        user_id = context.get("user_id", "default")
        self._log("Searching memory", f"Query: {message[:80]}...")

        # ── 1. Search conversation memory ─────────────────────
        past_conversations = self.vector_store.search_memory(
            query=message,
            user_id=user_id,
            top_k=5,
        )

        if not past_conversations:
            return (
                "I don't have any previous conversations about this topic. "
                "Would you like me to help you with this from scratch? 😊"
            )

        # ── 2. Build context for summarization ────────────────
        memory_text = "\n\n---\n\n".join(past_conversations)

        user_prompt = f"""The student is asking about: "{message}"

Here are relevant past conversations:

{memory_text}

Summarize what we've previously discussed about this topic and how it 
connects to their current question. Be concise and helpful."""

        # ── 3. Summarize with LLM ─────────────────────────────
        response = await self.llm.call(
            system_prompt=self.get_system_prompt(),
            user_message=user_prompt,
            max_tokens=800,
            temperature=0.5,
        )

        self._log("Complete", f"Found {len(past_conversations)} relevant conversations")
        return response
