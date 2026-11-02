"""
Timetable model — weekly college timetable.
"""
from sqlalchemy import Column, Integer, String, ForeignKey, Time
from sqlalchemy.orm import relationship
from api.models.database import Base


class Timetable(Base):
    __tablename__ = "timetable"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    day_of_week = Column(String(10), nullable=False)  # Monday, Tuesday, etc.
    start_time = Column(String(5), nullable=False)  # HH:MM
    end_time = Column(String(5), nullable=False)  # HH:MM
    lecture_name = Column(String(200), nullable=True)
    is_temp_override = Column(Integer, default=0)  # 0 = regular, 1 = day-specific override

    # Relationships
    user = relationship("User")
    subject = relationship("Subject")


class TimetableOverride(Base):
    __tablename__ = "timetable_overrides"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    override_date = Column(String(10), nullable=False)  # YYYY-MM-DD
    start_time = Column(String(5), nullable=False)
    end_time = Column(String(5), nullable=False)
    lecture_name = Column(String(200), nullable=True)
    action = Column(String(10), default="add")  # add, remove, replace

    user = relationship("User")
    subject = relationship("Subject")
