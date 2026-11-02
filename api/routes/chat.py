"""
Chat Routes — Main chat endpoint for the agentic system.

POST /chat/message → Orchestrator routes to correct agent → Response
"""

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from api.agents.orchestrator import Orchestrator

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Request / Response Models ──────────────────────────────────

class ChatMessage(BaseModel):
    """Incoming chat message from the user."""
    message: str = Field(..., min_length=1, max_length=5000, description="User's message")
    user_id: str = Field(default="default", description="User identifier")
    context: dict = Field(default_factory=dict, description="Additional context (exam_date, subject, etc.)")


class ChatResponse(BaseModel):
    """Response from the agentic system."""
    response: str = Field(..., description="Agent's response text")
    agent_used: str = Field(..., description="Which agent handled the message")


# ── Endpoints ──────────────────────────────────────────────────

@router.post("/message", response_model=ChatResponse)
async def chat(msg: ChatMessage):
    """
    Main chat endpoint — routes message to the appropriate AI agent.

    The Orchestrator analyzes the message intent and routes to:
    - PlannerAgent: Study schedules, revision plans
    - AssignmentAgent: Concept explanations, homework help
    - MemoryAgent: Past conversation retrieval
    """
    try:
        orchestrator = Orchestrator()

        response_text, agent_used = await orchestrator.route(
            message=msg.message,
            context={**msg.context, "user_id": msg.user_id},
        )

        return ChatResponse(
            response=response_text,
            agent_used=agent_used,
        )

    except ValueError as e:
        logger.error(f"Configuration or validation error in chat: {e}")
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}", exc_info=True)
        err_msg = str(e)
        if "API_KEY" in err_msg or "api_key" in err_msg:
            detail = "Gemini API key is invalid or not configured. Please check your .env file."
        elif "503" in err_msg or "UNAVAILABLE" in err_msg:
            detail = "The AI service is temporarily experiencing high demand. Please try again in a few moments."
        else:
            detail = f"Chat error: {err_msg}"
        raise HTTPException(
            status_code=500,
            detail=detail,
        )
