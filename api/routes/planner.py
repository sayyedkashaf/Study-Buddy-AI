"""
Planner Routes — Study plan generation and retrieval.

POST /planner/generate  → Generate a new study plan
GET  /planner/{user_id} → Get all plans for a user
"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from api.models.database import get_db
from api.models.study_plan import StudyPlan
from api.agents.planner_agent import PlannerAgent

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Request / Response Models ──────────────────────────────────

class PlanRequest(BaseModel):
    """Request to generate a study plan."""
    user_id: int = Field(default=1, description="User ID")
    subject_id: int = Field(default=None, description="Subject ID (optional)")
    exam_date: str = Field(..., description="Exam date in YYYY-MM-DD format")
    request_text: str = Field(..., min_length=5, description="What to plan for")


class PlanResponse(BaseModel):
    """Generated study plan."""
    plan_id: int
    plan: str
    exam_date: str


# ── Endpoints ──────────────────────────────────────────────────

@router.post("/generate", response_model=PlanResponse)
async def generate_plan(req: PlanRequest, db: Session = Depends(get_db)):
    """
    Generate a personalized study plan using the PlannerAgent.

    The agent:
    1. Searches the syllabus for relevant topics
    2. Calculates days until exam
    3. Creates a weighted study schedule via Gemini LLM
    4. Saves the plan to the database
    """
    # Validate exam date
    try:
        exam_date = datetime.strptime(req.exam_date, "%Y-%m-%d")
        if exam_date.date() <= datetime.now().date():
            raise HTTPException(status_code=400, detail="Exam date must be in the future.")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    # Generate plan via agent
    try:
        agent = PlannerAgent()
        plan_text = await agent.run(
            message=req.request_text,
            context={"exam_date": req.exam_date},
        )
    except Exception as e:
        logger.error(f"Plan generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate study plan.")

    # Save to database
    plan = StudyPlan(
        user_id=req.user_id,
        subject_id=req.subject_id,
        title=req.request_text[:200],
        content=plan_text,
        exam_date=req.exam_date,
        created_at=datetime.now(timezone.utc),
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)

    return PlanResponse(
        plan_id=plan.id,
        plan=plan_text,
        exam_date=req.exam_date,
    )


@router.get("/{user_id}")
def get_plans(user_id: int, db: Session = Depends(get_db)):
    """Get all study plans for a user, newest first."""
    plans = (
        db.query(StudyPlan)
        .filter(StudyPlan.user_id == user_id)
        .order_by(StudyPlan.created_at.desc())
        .all()
    )

    return {
        "plans": [
            {
                "id": p.id,
                "title": p.title,
                "content": p.content,
                "exam_date": p.exam_date,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in plans
        ],
        "total": len(plans),
    }
