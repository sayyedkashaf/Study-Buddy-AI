"""
StudyPlan model — stores AI-generated study schedules.
"""

from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from api.models.database import Base


class StudyPlan(Base):
    __tablename__ = "study_plans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=True)
    title = Column(String(300), nullable=True)
    content = Column(Text, nullable=False)  # Full plan as markdown/text
    exam_date = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", back_populates="study_plans")
    subject = relationship("Subject", back_populates="study_plans")

    def __repr__(self):
        return f"<StudyPlan(id={self.id}, title='{self.title}')>"
