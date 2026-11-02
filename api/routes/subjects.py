"""
Subject Routes — Manage subjects/courses.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from api.models.database import get_db
from api.models.subject import Subject

logger = logging.getLogger(__name__)
router = APIRouter()


class SubjectCreate(BaseModel):
    name: str = Field(..., min_length=1)
    user_id: int = Field(default=1)
    code: str = Field(default=None)
    credits: float = Field(default=3.0)


class SubjectUpdate(BaseModel):
    name: str = Field(..., min_length=1)


@router.get("/")
def list_subjects(user_id: int = 1, db: Session = Depends(get_db)):
    subjects = (
        db.query(Subject)
        .filter(Subject.user_id == user_id)
        .order_by(Subject.id)
        .all()
    )
    return {
        "subjects": [
            {
                "id": s.id,
                "name": s.name,
                "code": s.code,
                "credits": s.credits,
                "exam_date": s.exam_date,
                "syllabus_filename": s.syllabus_filename,
            }
            for s in subjects
        ]
    }


@router.post("/")
def create_subject(subject: SubjectCreate, db: Session = Depends(get_db)):
    name = subject.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Subject name cannot be empty.")
    
    # Check for duplicates
    existing = (
        db.query(Subject)
        .filter(Subject.user_id == subject.user_id, Subject.name.ilike(name))
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="A subject with this name already exists.")
    
    new_subject = Subject(
        user_id=subject.user_id,
        name=name,
        code=subject.code.strip() if subject.code else None,
        credits=subject.credits,
    )
    db.add(new_subject)
    db.commit()
    db.refresh(new_subject)
    
    logger.info(f"Created subject: {new_subject.name} (id={new_subject.id})")
    return {
        "id": new_subject.id,
        "name": new_subject.name,
        "code": new_subject.code,
        "credits": new_subject.credits,
    }


@router.put("/{subject_id}")
def rename_subject(subject_id: int, subject: SubjectUpdate, db: Session = Depends(get_db)):
    name = subject.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Subject name cannot be empty.")
    
    subj = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subj:
        raise HTTPException(status_code=404, detail="Subject not found.")
    
    # Check for duplicates (different subject)
    existing = (
        db.query(Subject)
        .filter(Subject.user_id == subj.user_id, Subject.name.ilike(name), Subject.id != subject_id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="A subject with this name already exists.")
    
    subj.name = name
    db.commit()
    db.refresh(subj)
    
    logger.info(f"Renamed subject {subject_id} to {name}")
    return {
        "id": subj.id,
        "name": subj.name,
        "code": subj.code,
        "credits": subj.credits,
    }


@router.delete("/{subject_id}")
def delete_subject(subject_id: int, db: Session = Depends(get_db)):
    subj = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subj:
        raise HTTPException(status_code=404, detail="Subject not found.")
    
    db.delete(subj)
    db.commit()
    
    logger.info(f"Deleted subject {subject_id} ({subj.name})")
    return {"message": f"Deleted subject {subj.name}", "id": subject_id}
