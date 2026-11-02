"""
Attendance Routes — Enhanced with timetable and analytics.
"""
import logging
from datetime import datetime, date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func

from api.models.database import get_db
from api.models.attendance import Attendance
from api.models.timetable import Timetable, TimetableOverride
from api.models.subject import Subject

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Request Models ─────────────────────────────────────────────

class AttendanceRecord(BaseModel):
    user_id: int = Field(default=1)
    subject_id: int
    lecture_date: str = Field(default=None)
    start_time: str = Field(default=None)
    end_time: str = Field(default=None)
    lecture_name: str = Field(default=None)
    status: str = Field(default="present")  # present, absent
    reason: str = Field(default=None)


class AttendanceUpdate(BaseModel):
    status: str  # present, absent
    reason: str = Field(default=None)


class TimetableEntry(BaseModel):
    user_id: int = Field(default=1)
    subject_id: int
    day_of_week: str
    start_time: str
    end_time: str
    lecture_name: str = Field(default=None)


class TimetableOverrideEntry(BaseModel):
    user_id: int = Field(default=1)
    subject_id: int
    override_date: str
    start_time: str
    end_time: str
    lecture_name: str = Field(default=None)
    action: str = Field(default="add")


# ── Academic Year Helpers ───────────────────────────────────────

def get_academic_year(d: date = None):
    if d is None:
        d = date.today()
    # Assuming academic year starts in July
    if d.month >= 7:
        return f"{d.year}-{d.year + 1}"
    else:
        return f"{d.year - 1}-{d.year}"


# ── Timetable Endpoints ─────────────────────────────────────────

@router.post("/timetable")
def save_timetable_entry(entry: TimetableEntry, db: Session = Depends(get_db)):
    # Check for duplicates
    existing = db.query(Timetable).filter(
        Timetable.user_id == entry.user_id,
        Timetable.day_of_week == entry.day_of_week,
        Timetable.subject_id == entry.subject_id,
        Timetable.start_time == entry.start_time,
        Timetable.end_time == entry.end_time,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Lecture already exists in timetable.")
    
    tt = Timetable(
        user_id=entry.user_id,
        subject_id=entry.subject_id,
        day_of_week=entry.day_of_week,
        start_time=entry.start_time,
        end_time=entry.end_time,
        lecture_name=entry.lecture_name,
    )
    db.add(tt)
    db.commit()
    db.refresh(tt)
    return {"message": "Timetable entry added", "id": tt.id}


@router.get("/timetable/{user_id}")
def get_timetable(user_id: int, day_of_week: str = None, db: Session = Depends(get_db)):
    query = db.query(Timetable).filter(Timetable.user_id == user_id)
    if day_of_week:
        query = query.filter(Timetable.day_of_week == day_of_week)
    entries = query.order_by(Timetable.start_time).all()
    result = []
    for e in entries:
        subj = db.query(Subject).filter(Subject.id == e.subject_id).first()
        result.append({
            "id": e.id,
            "subject_id": e.subject_id,
            "subject_name": subj.name if subj else "",
            "day_of_week": e.day_of_week,
            "start_time": e.start_time,
            "end_time": e.end_time,
            "lecture_name": e.lecture_name or (subj.name if subj else ""),
        })
    return {"timetable": result}


@router.delete("/timetable/{entry_id}")
def delete_timetable_entry(entry_id: int, db: Session = Depends(get_db)):
    entry = db.query(Timetable).filter(Timetable.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Timetable entry not found.")
    db.delete(entry)
    db.commit()
    return {"message": "Timetable entry deleted"}


@router.post("/timetable/override")
def add_timetable_override(entry: TimetableOverrideEntry, db: Session = Depends(get_db)):
    ov = TimetableOverride(
        user_id=entry.user_id,
        subject_id=entry.subject_id,
        override_date=entry.override_date,
        start_time=entry.start_time,
        end_time=entry.end_time,
        lecture_name=entry.lecture_name,
        action=entry.action,
    )
    db.add(ov)
    db.commit()
    db.refresh(ov)
    return {"message": "Override added", "id": ov.id}


# ── Daily Schedule & Attendance ─────────────────────────────────

@router.get("/today/{user_id}")
def get_today_schedule(user_id: int, target_date: str = None, db: Session = Depends(get_db)):
    if target_date:
        try:
            tdate = datetime.strptime(target_date, "%Y-%m-%d").date()
        except:
            tdate = date.today()
    else:
        tdate = date.today()
    
    day_name = tdate.strftime("%A")  # Monday, Tuesday, etc.
    
    # Get regular timetable for the day
    regular = db.query(Timetable).filter(
        Timetable.user_id == user_id,
        Timetable.day_of_week == day_name
    ).order_by(Timetable.start_time).all()
    
    lectures = []
    for r in regular:
        subj = db.query(Subject).filter(Subject.id == r.subject_id).first()
        lectures.append({
            "subject_id": r.subject_id,
            "subject_name": subj.name if subj else "",
            "start_time": r.start_time,
            "end_time": r.end_time,
            "lecture_name": r.lecture_name or (subj.name if subj else ""),
            "source": "regular",
        })
    
    # Get attendance status for today
    date_str = tdate.strftime("%Y-%m-%d")
    attendance_records = db.query(Attendance).filter(
        Attendance.user_id == user_id,
        Attendance.lecture_date == date_str
    ).all()
    
    att_map = {}
    for a in attendance_records:
        key = f"{a.subject_id}_{a.start_time}_{a.end_time}"
        att_map[key] = {
            "status": a.status,
            "id": a.id,
            "attended": a.attended,
        }
    
    for lec in lectures:
        key = f"{lec['subject_id']}_{lec['start_time']}_{lec['end_time']}"
        if key in att_map:
            lec["attendance_status"] = att_map[key]["status"]
            lec["attendance_id"] = att_map[key]["id"]
        else:
            lec["attendance_status"] = "not_marked"
            lec["attendance_id"] = None
    
    # Calculate stats
    total = len(lectures)
    present = sum(1 for l in lectures if l.get("attendance_status") == "present")
    absent = sum(1 for l in lectures if l.get("attendance_status") == "absent")
    not_marked = sum(1 for l in lectures if l.get("attendance_status") == "not_marked")
    percentage = round((present / total * 100), 1) if total > 0 else 0.0
    
    return {
        "date": date_str,
        "day": day_name,
        "lectures": lectures,
        "stats": {
            "total": total,
            "present": present,
            "absent": absent,
            "not_marked": not_marked,
            "percentage": percentage,
        }
    }


@router.post("/mark-lecture")
def mark_lecture_attendance(record: AttendanceRecord, db: Session = Depends(get_db)):
    date_str = record.lecture_date or date.today().strftime("%Y-%m-%d")
    ay = get_academic_year(datetime.strptime(date_str, "%Y-%m-%d").date())
    
    # Check for duplicate
    existing = db.query(Attendance).filter(
        Attendance.user_id == record.user_id,
        Attendance.subject_id == record.subject_id,
        Attendance.lecture_date == date_str,
        Attendance.start_time == record.start_time,
        Attendance.end_time == record.end_time,
    ).first()
    
    if existing:
        # Update existing
        existing.status = record.status
        existing.attended = record.status == "present"
        existing.reason = record.reason
        existing.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(existing)
        return {"message": f"Attendance updated to {record.status}", "id": existing.id}
    
    attendance = Attendance(
        user_id=record.user_id,
        subject_id=record.subject_id,
        lecture_date=date_str,
        start_time=record.start_time,
        end_time=record.end_time,
        lecture_name=record.lecture_name,
        status=record.status,
        attended=record.status == "present",
        reason=record.reason,
        academic_year=ay,
    )
    db.add(attendance)
    db.commit()
    db.refresh(attendance)
    return {"message": f"Attendance marked as {record.status}", "id": attendance.id}


@router.put("/update/{attendance_id}")
def update_attendance(attendance_id: int, update: AttendanceUpdate, db: Session = Depends(get_db)):
    att = db.query(Attendance).filter(Attendance.id == attendance_id).first()
    if not att:
        raise HTTPException(status_code=404, detail="Attendance record not found.")
    
    att.status = update.status
    att.attended = update.status == "present"
    att.reason = update.reason
    att.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(att)
    return {"message": "Attendance updated", "id": att.id}


# ── Analytics ───────────────────────────────────────────────────

@router.get("/analytics/subject-wise/{user_id}")
def subject_wise_analytics(user_id: int, academic_year: str = None, db: Session = Depends(get_db)):
    if not academic_year:
        academic_year = get_academic_year()
    
    # Get all subjects for user
    subjects = db.query(Subject).filter(Subject.user_id == user_id).all()
    result = []
    
    for subj in subjects:
        records = db.query(Attendance).filter(
            Attendance.user_id == user_id,
            Attendance.subject_id == subj.id,
            Attendance.academic_year == academic_year,
            Attendance.status != "not_marked"
        ).all()
        
        total = len(records)
        present = sum(1 for r in records if r.status == "present")
        absent = total - present
        percentage = round((present / total * 100), 1) if total > 0 else 0.0
        
        result.append({
            "subject_id": subj.id,
            "subject_name": subj.name,
            "total_lectures": total,
            "present": present,
            "absent": absent,
            "percentage": percentage,
            "below_75": percentage < 75 and total > 0,
        })
    
    return {"academic_year": academic_year, "subjects": result}


@router.get("/analytics/overall/{user_id}")
def overall_analytics(user_id: int, academic_year: str = None, db: Session = Depends(get_db)):
    if not academic_year:
        academic_year = get_academic_year()
    
    records = db.query(Attendance).filter(
        Attendance.user_id == user_id,
        Attendance.academic_year == academic_year,
        Attendance.status != "not_marked"
    ).all()
    
    total = len(records)
    present = sum(1 for r in records if r.status == "present")
    absent = total - present
    percentage = round((present / total * 100), 1) if total > 0 else 0.0
    
    return {
        "academic_year": academic_year,
        "total_lectures": total,
        "present": present,
        "absent": absent,
        "percentage": percentage,
    }


@router.get("/analytics/monthly/{user_id}")
def monthly_analytics(user_id: int, academic_year: str = None, db: Session = Depends(get_db)):
    if not academic_year:
        academic_year = get_academic_year()
    
    records = db.query(Attendance).filter(
        Attendance.user_id == user_id,
        Attendance.academic_year == academic_year,
        Attendance.status != "not_marked"
    ).all()
    
    monthly = {}
    for r in records:
        try:
            d = datetime.strptime(r.lecture_date, "%Y-%m-%d")
            month_key = d.strftime("%Y-%m")
            if month_key not in monthly:
                monthly[month_key] = {"present": 0, "absent": 0, "total": 0}
            monthly[month_key]["total"] += 1
            if r.status == "present":
                monthly[month_key]["present"] += 1
            else:
                monthly[month_key]["absent"] += 1
        except:
            continue
    
    result = []
    for k in sorted(monthly.keys()):
        m = monthly[k]
        pct = round((m["present"] / m["total"] * 100), 1) if m["total"] > 0 else 0.0
        result.append({
            "month": k,
            "present": m["present"],
            "absent": m["absent"],
            "total": m["total"],
            "percentage": pct,
        })
    
    return {"academic_year": academic_year, "monthly": result}


@router.get("/academic-years/{user_id}")
def get_academic_years(user_id: int, db: Session = Depends(get_db)):
    years = db.query(Attendance.academic_year).filter(
        Attendance.user_id == user_id,
        Attendance.academic_year.isnot(None)
    ).distinct().all()
    year_list = sorted([y[0] for y in years if y[0]], reverse=True)
    if not year_list:
        year_list = [get_academic_year()]
    return {"academic_years": year_list}


# Keep old endpoints for compatibility
class OldAttendanceRecord(BaseModel):
    user_id: int = Field(default=1)
    subject_id: int
    date: str = Field(default=None)
    attended: bool
    reason: str = Field(default=None)


@router.post("/mark")
def mark_attendance_old(record: OldAttendanceRecord, db: Session = Depends(get_db)):
    if record.date:
        try:
            d = datetime.fromisoformat(record.date).date()
            date_str = d.strftime("%Y-%m-%d")
        except:
            date_str = date.today().strftime("%Y-%m-%d")
    else:
        date_str = date.today().strftime("%Y-%m-%d")
    
    ay = get_academic_year(datetime.strptime(date_str, "%Y-%m-%d").date())
    status = "present" if record.attended else "absent"
    
    attendance = Attendance(
        user_id=record.user_id,
        subject_id=record.subject_id,
        lecture_date=date_str,
        status=status,
        attended=record.attended,
        reason=record.reason,
        academic_year=ay,
    )
    db.add(attendance)
    db.commit()
    db.refresh(attendance)
    return {"message": f"Attendance marked: {'✅ Present' if record.attended else '❌ Absent'}", "id": attendance.id}


@router.get("/{user_id}/{subject_id}")
def get_attendance(user_id: int, subject_id: int, db: Session = Depends(get_db)):
    records = db.query(Attendance).filter(
        Attendance.user_id == user_id,
        Attendance.subject_id == subject_id,
    ).order_by(Attendance.lecture_date.desc()).all()
    
    total = len([r for r in records if r.status != "not_marked"])
    attended = sum(1 for r in records if r.status == "present")
    percentage = round((attended / total * 100), 1) if total > 0 else 0.0
    
    classes_needed = 0
    if percentage < 75.0 and total > 0:
        needed = (0.75 * total - attended) / 0.25
        classes_needed = max(0, int(needed) + 1)
    
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
                "date": r.lecture_date,
                "attended": r.status == "present",
                "reason": r.reason,
                "status": r.status,
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
    from api.services.llm_service import LLMService
    
    records = db.query(Attendance).filter(
        Attendance.user_id == user_id,
        Attendance.subject_id == subject_id,
    ).all()
    
    total = len([r for r in records if r.status != "not_marked"])
    attended = sum(1 for r in records if r.status == "present")
    percentage = round((attended / total * 100), 1) if total > 0 else 0.0
    
    if total == 0:
        return {"advice": "No attendance records yet. Start tracking to get personalized advice!"}
    
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
