"""
Attendance model — tracks class attendance per scheduled lecture.
"""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from api.models.database import Base


class Attendance(Base):
    __tablename__ = "attendance"
    __table_args__ = (
        UniqueConstraint('user_id', 'subject_id', 'lecture_date', 'start_time', 'end_time', name='uq_attendance_lecture'),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    lecture_date = Column(String(10), nullable=False, index=True)  # YYYY-MM-DD
    start_time = Column(String(5), nullable=True)
    end_time = Column(String(5), nullable=True)
    lecture_name = Column(String(200), nullable=True)
    status = Column(String(10), nullable=False)  # present, absent, not_marked
    attended = Column(Boolean, nullable=True)  # For backward compatibility
    reason = Column(String(500), nullable=True)
    academic_year = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", back_populates="attendance_records")
    subject = relationship("Subject", back_populates="attendance_records")

    def __repr__(self):
        return f"<Attendance(id={self.id}, status={self.status}, date='{self.lecture_date}')>"
