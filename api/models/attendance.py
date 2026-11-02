"""
Attendance model — tracks class attendance per subject.
"""

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from api.models.database import Base


class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    attended = Column(Boolean, nullable=False)
    reason = Column(String(500), nullable=True)

    # Relationships
    user = relationship("User", back_populates="attendance_records")
    subject = relationship("Subject", back_populates="attendance_records")

    def __repr__(self):
        return f"<Attendance(id={self.id}, attended={self.attended}, date='{self.date}')>"
