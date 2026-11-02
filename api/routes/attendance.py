"""
Attendance Routes — Track and analyze class attendance.

POST /attendance/mark             → Mark attendance for a class
GET  /attendance/{user_id}/{subj} → Get attendance records + percentage
GET  /attendance/advice/{user_id}/{subj} → Get AI advice on attendance
"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from api.models.database import get_db
from api.models.attendance import Attendance

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Request Models ─────────────────────────────────────────────

class AttendanceRecord(BaseModel):
    """Mark attendance for a single class."""
    user_id: int = Field(default=1)
    subject_id: int
    date: str = Field(default=None, description="ISO date string, defaults to today")
    attended: bool
    reason: str = Field(default=None, description="Reason if absent")


# ── Endpoints ──────────────────────────────────────────────────

@router.post("/mark")
def mark_attendance(record: AttendanceRecord, db: Session = Depends(get_db)):
    """Mark attendance for a class session."""
    # Parse date or use today
    if record.date:
        try:
            date = datetime.fromisoformat(record.date)
        except ValueError:
            date = datetime.now(timezone.utc)
    else:
        date = datetime.now(timezone.utc)

    attendance = Attendance(
        user_id=record.user_id,
        subject_id=record.subject_id,
        date=date,
        attended=record.attended,
        reason=record.reason,
    )
    db.add(attendance)
    db.commit()
    db.refresh(attendance)

    status = "✅ Present" if record.attended else "❌ Absent"

    return {
        "message": f"Attendance marked: {status}",
        "id": attendance.id,
        "attended": record.attended,
    }


@router.get("/{user_id}/{subject_id}")
def get_attendance(user_id: int, subject_id: int, db: Session = Depends(get_db)):
    """
    Get attendance records and statistics for a user + subject.

    Returns:
    - Individual records
    - Total classes, attended count, percentage
    - Warning if below minimum threshold
    """
    records = (
        db.query(Attendance)
        .filter(
            Attendance.user_id == user_id,
            Attendance.subject_id == subject_id,
        )
        .order_by(Attendance.date.desc())
        .all()
    )

    total = len(records)
    attended = sum(1 for r in records if r.attended)
    percentage = round((attended / total * 100), 1) if total > 0 else 0.0

    # Calculate classes needed to reach 75%
    classes_needed = 0
    if percentage < 75.0 and total > 0:
        # Solve: (attended + x) / (total + x) >= 0.75
        # x >= (0.75 * total - attended) / 0.25
        needed = (0.75 * total - attended) / 0.25
        classes_needed = max(0, int(needed) + 1)

    # Warning status
    if percentage >= 75:
        status = "🟢 Safe"
    elif percentage >= 65:
        status = "🟡 Warning — Approaching minimum"
    else:
        status = "🔴 Critical — Below minimum requirement"

    return {
        "records": [
            {
                "id": r.id,
                "date": r.date.isoformat() if r.date else None,
                "attended": r.attended,
                "reason": r.reason,
            }
            for r in records
        ],
        "stats": {
            "total_classes": total,
            "attended": attended,
            "absent": total - attended,
            "percentage": percentage,
            "status": status,
            "classes_needed_for_75": classes_needed,
        },
    }


@router.get("/advice/{user_id}/{subject_id}")
async def get_attendance_advice(user_id: int, subject_id: int, db: Session = Depends(get_db)):
    """Get AI-powered attendance advice based on current stats."""
    from api.services.llm_service import LLMService

    # Get current stats
    records = (
        db.query(Attendance)
        .filter(
            Attendance.user_id == user_id,
            Attendance.subject_id == subject_id,
        )
        .all()
    )

    total = len(records)
    attended = sum(1 for r in records if r.attended)
    percentage = round((attended / total * 100), 1) if total > 0 else 0.0

    if total == 0:
        return {"advice": "No attendance records yet. Start tracking to get personalized advice! 📊"}

    llm = LLMService()
    prompt = f"""Student attendance stats:
- Total classes: {total}
- Attended: {attended}
- Percentage: {percentage}%
- Required minimum: 75%

Give brief, actionable advice (3-4 sentences max) about their attendance situation.
If below 75%, calculate exactly how many consecutive classes they need to attend."""

    advice = await llm.call(
        system_prompt="You are a concise academic advisor. Give practical attendance advice.",
        user_message=prompt,
        max_tokens=300,
        temperature=0.5,
        use_fast_model=True,
    )

    return {"advice": advice, "percentage": percentage}
